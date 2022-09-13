# Copyright (C) 2017-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import base64
import stat
import textwrap
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

import chardet
import magic

from django.utils.html import escape
from django.utils.safestring import mark_safe

from swh.web.config import get_config
from swh.web.utils import (
    archive,
    browsers_supported_image_mimes,
    django_cache,
    format_utc_iso_date,
    highlightjs,
    reverse,
    rst_to_html,
)
from swh.web.utils.exc import NotFoundExc, sentry_capture_exception
from swh.web.utils.typing import SnapshotContext


@django_cache()
def get_directory_entries(
    sha1_git: str,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Function that retrieves the content of a directory
    from the archive.

    The directories entries are first sorted in lexicographical order.
    Sub-directories and regular files are then extracted.

    Args:
        sha1_git: sha1_git identifier of the directory

    Returns:
        A tuple whose first member corresponds to the sub-directories list
        and second member the regular files list

    Raises:
        NotFoundExc if the directory is not found
    """
    entries: List[Dict[str, Any]] = list(archive.lookup_directory(sha1_git))
    for e in entries:
        e["perms"] = stat.filemode(e["perms"])
        if e["type"] == "rev":
            # modify dir entry name to explicitly show it points
            # to a revision
            e["name"] = "%s @ %s" % (e["name"], e["target"][:7])

    dirs = [e for e in entries if e["type"] in ("dir", "rev")]
    files = [e for e in entries if e["type"] == "file"]

    dirs = sorted(dirs, key=lambda d: d["name"])
    files = sorted(files, key=lambda f: f["name"])

    return dirs, files


def get_mimetype_and_encoding_for_content(content: bytes) -> Tuple[str, str]:
    """Function that returns the mime type and the encoding associated to
    a content buffer using the magic module under the hood.

    Args:
        content: a content buffer

    Returns:
        A tuple (mimetype, encoding), for instance ('text/plain', 'us-ascii'),
        associated to the provided content.

    """
    m = magic.Magic(mime=True, mime_encoding=True)
    mime_encoding = m.from_buffer(content)
    mime_type, encoding = mime_encoding.split(";")
    encoding = encoding.replace(" charset=", "")
    return mime_type, encoding


# maximum authorized content size in bytes for HTML display
# with code highlighting
content_display_max_size = get_config()["content_display_max_size"]


def re_encode_content(
    mimetype: str, encoding: str, content_data: bytes
) -> Tuple[str, str, bytes]:
    """Try to re-encode textual content if it is not encoded to UTF-8
    for proper display in the browse Web UI.

    Args:
        mimetype: content mimetype as detected by python-magic
        encoding: content encoding as detected by python-magic
        content_data: raw content bytes

    Returns:
        A tuple with 3 members: content mimetype, content encoding (possibly updated
        after processing), content raw bytes (possibly reencoded to UTF-8)
    """
    if mimetype.startswith("text/") and encoding not in ("us-ascii", "utf-8"):
        # first check if chardet detects an encoding with confidence
        result = chardet.detect(content_data)
        if result["confidence"] >= 0.9:
            encoding = result["encoding"]
            content_data = content_data.decode(encoding).encode("utf-8")
        elif encoding == "unknown-8bit":
            # probably a malformed UTF-8 content, re-encode it
            # by replacing invalid chars with a substitution one
            content_data = content_data.decode("utf-8", "replace").encode("utf-8")
        elif encoding not in ["utf-8", "binary"]:
            content_data = content_data.decode(encoding, "replace").encode("utf-8")
    elif mimetype.startswith("application/octet-stream"):
        # file may detect a text content as binary
        # so try to decode it for display
        encodings = ["us-ascii", "utf-8"]
        encodings += ["iso-8859-%s" % i for i in range(1, 17)]
        for enc in encodings:
            try:
                content_data = content_data.decode(enc).encode("utf-8")
            except Exception:
                pass
            else:
                # ensure display in content view
                encoding = enc
                mimetype = "text/plain"
                break
    return mimetype, encoding, content_data


def request_content(
    query_string: str,
    max_size: Optional[int] = content_display_max_size,
    re_encode: bool = True,
) -> Dict[str, Any]:
    """Function that retrieves a content from the archive.

    Raw bytes content is first retrieved, then the content mime type.
    If the mime type is not stored in the archive, it will be computed
    using Python magic module.

    Args:
        query_string: a string of the form "[ALGO_HASH:]HASH" where
            optional ALGO_HASH can be either ``sha1``, ``sha1_git``,
            ``sha256``, or ``blake2s256`` (default to ``sha1``) and HASH
            the hexadecimal representation of the hash value
        max_size: the maximum size for a content to retrieve (default to 1MB,
            no size limit if None)

    Returns:
        A dict filled with content info.

    Raises:
        NotFoundExc if the content is not found
    """
    content_data = archive.lookup_content(query_string)
    filetype = None
    language = None
    # requests to the indexer db may fail so properly handle
    # those cases in order to avoid content display errors
    try:
        filetype = archive.lookup_content_filetype(query_string)
        language = archive.lookup_content_language(query_string)
    except Exception as exc:
        sentry_capture_exception(exc)
    mimetype = "unknown"
    encoding = "unknown"
    if filetype:
        mimetype = filetype["mimetype"]
        encoding = filetype["encoding"]

    if not max_size or content_data["length"] < max_size:
        try:
            content_raw = archive.lookup_content_raw(query_string)
        except Exception as exc:
            sentry_capture_exception(exc)
            raise NotFoundExc(
                "The bytes of the content are currently not available "
                "in the archive."
            )
        else:
            content_data["raw_data"] = content_raw["data"]

            if not filetype:
                mimetype, encoding = get_mimetype_and_encoding_for_content(
                    content_data["raw_data"]
                )

            if re_encode:
                mimetype, encoding, raw_data = re_encode_content(
                    mimetype, encoding, content_data["raw_data"]
                )
                content_data["raw_data"] = raw_data

    else:
        content_data["raw_data"] = None

    content_data["mimetype"] = mimetype
    content_data["encoding"] = encoding

    if language:
        content_data["language"] = language["lang"]
    else:
        content_data["language"] = "not detected"

    return content_data


def prepare_content_for_display(
    content_data: bytes, mime_type: str, path: Optional[str]
) -> Dict[str, Any]:
    """Function that prepares a content for HTML display.

    The function tries to associate a programming language to a
    content in order to perform syntax highlighting client-side
    using highlightjs. The language is determined using either
    the content filename or its mime type.
    If the mime type corresponds to an image format supported
    by web browsers, the content will be encoded in base64
    for displaying the image.

    Args:
        content_data: raw bytes of the content
        mime_type: mime type of the content
        path: path of the content including filename

    Returns:
        A dict containing the content bytes (possibly different from the one
        provided as parameter if it is an image) under the key 'content_data
        and the corresponding highlightjs language class under the
        key 'language'.
    """

    language = None
    if path:
        language = highlightjs.get_hljs_language_from_filename(path.split("/")[-1])

    if language is None:
        language = highlightjs.get_hljs_language_from_mime_type(mime_type)

    if language is None:
        language = "plaintext"

    processed_content: Union[bytes, str] = content_data

    if mime_type.startswith("image/"):
        if mime_type in browsers_supported_image_mimes:
            processed_content = base64.b64encode(content_data).decode("ascii")

    if mime_type.startswith("image/svg"):
        mime_type = "image/svg+xml"

    if mime_type.startswith("text/") or mime_type.startswith("application/"):
        processed_content = content_data.decode("utf-8", errors="replace")

    return {
        "content_data": processed_content,
        "language": language,
        "mimetype": mime_type,
    }


def gen_link(
    url: str,
    link_text: Optional[str] = None,
    link_attrs: Optional[Dict[str, str]] = None,
) -> str:
    """
    Utility function for generating an HTML link to insert
    in Django templates.

    Args:
        url: an url
        link_text: optional text for the produced link,
            if not provided the url will be used
        link_attrs: optional attributes (e.g. class)
            to add to the link

    Returns:
        An HTML link in the form '<a href="url">link_text</a>'

    """
    attrs = " "
    if link_attrs:
        for k, v in link_attrs.items():
            attrs += '%s="%s" ' % (k, v)
    if not link_text:
        link_text = url
    link = '<a%shref="%s">%s</a>' % (attrs, escape(url), escape(link_text))
    return mark_safe(link)


def _snapshot_context_query_params(
    snapshot_context: Optional[SnapshotContext],
) -> Dict[str, str]:
    query_params: Dict[str, str] = {}
    if not snapshot_context:
        return query_params
    if snapshot_context and snapshot_context["origin_info"]:
        origin_info = snapshot_context["origin_info"]
        snp_query_params = snapshot_context["query_params"]
        query_params = {"origin_url": origin_info["url"]}
        if "timestamp" in snp_query_params:
            query_params["timestamp"] = str(snp_query_params["timestamp"])
        if "visit_id" in snp_query_params:
            query_params["visit_id"] = str(snp_query_params["visit_id"])
        if "snapshot" in snp_query_params and "visit_id" not in query_params:
            query_params["snapshot"] = str(snp_query_params["snapshot"])
    elif snapshot_context:
        query_params = {"snapshot": snapshot_context["snapshot_id"]}

    if snapshot_context["release"]:
        query_params["release"] = snapshot_context["release"]
    elif snapshot_context["branch"] and snapshot_context["branch"] not in (
        "HEAD",
        snapshot_context["revision_id"],
    ):
        query_params["branch"] = snapshot_context["branch"]
    elif snapshot_context["revision_id"]:
        query_params["revision"] = snapshot_context["revision_id"]
    return query_params


def gen_revision_url(
    revision_id: str, snapshot_context: Optional[SnapshotContext] = None
) -> str:
    """
    Utility function for generating an url to a revision.

    Args:
        revision_id: a revision id
        snapshot_context: if provided, generate snapshot-dependent
            browsing url

    Returns:
        str: The url to browse the revision

    """
    query_params = _snapshot_context_query_params(snapshot_context)
    # remove query parameters not needed for a revision view
    query_params.pop("revision", None)
    query_params.pop("release", None)

    return reverse(
        "browse-revision", url_args={"sha1_git": revision_id}, query_params=query_params
    )


def gen_revision_link(
    revision_id: str,
    shorten_id: bool = False,
    snapshot_context: Optional[SnapshotContext] = None,
    link_text: Optional[str] = "Browse",
    link_attrs: Optional[Dict[str, str]] = {
        "class": "btn btn-default btn-sm",
        "role": "button",
    },
) -> Optional[str]:
    """
    Utility function for generating a link to a revision HTML view
    to insert in Django templates.

    Args:
        revision_id: a revision id
        shorten_id: whether to shorten the revision id to 7
            characters for the link text
        snapshot_context: if provided, generate snapshot-dependent
            browsing link
        link_text: optional text for the generated link
            (the revision id will be used by default)
        link_attrs: optional attributes (e.g. class)
            to add to the link

    Returns:
        str: An HTML link in the form '<a href="revision_url">revision_id</a>'

    """
    if not revision_id:
        return None

    revision_url = gen_revision_url(revision_id, snapshot_context)

    if shorten_id:
        return gen_link(revision_url, revision_id[:7], link_attrs)
    else:
        if not link_text:
            link_text = revision_id
        return gen_link(revision_url, link_text, link_attrs)


def gen_directory_link(
    sha1_git: str,
    snapshot_context: Optional[SnapshotContext] = None,
    link_text: Optional[str] = "Browse",
    link_attrs: Optional[Dict[str, str]] = {
        "class": "btn btn-default btn-sm",
        "role": "button",
    },
) -> Optional[str]:
    """
    Utility function for generating a link to a directory HTML view
    to insert in Django templates.

    Args:
        sha1_git: directory identifier
        link_text: optional text for the generated link
            (the directory id will be used by default)
        link_attrs: optional attributes (e.g. class)
            to add to the link

    Returns:
        An HTML link in the form '<a href="directory_view_url">link_text</a>'

    """
    if not sha1_git:
        return None

    query_params = _snapshot_context_query_params(snapshot_context)

    directory_url = reverse(
        "browse-directory", url_args={"sha1_git": sha1_git}, query_params=query_params
    )

    if not link_text:
        link_text = sha1_git
    return gen_link(directory_url, link_text, link_attrs)


def gen_snapshot_link(
    snapshot_id: str,
    snapshot_context: Optional[SnapshotContext] = None,
    link_text: Optional[str] = "Browse",
    link_attrs: Optional[Dict[str, str]] = {
        "class": "btn btn-default btn-sm",
        "role": "button",
    },
) -> str:
    """
    Utility function for generating a link to a snapshot HTML view
    to insert in Django templates.

    Args:
        snapshot_id: snapshot identifier
        link_text: optional text for the generated link
            (the snapshot id will be used by default)
        link_attrs: optional attributes (e.g. class)
            to add to the link

    Returns:
        An HTML link in the form '<a href="snapshot_view_url">link_text</a>'

    """

    query_params = _snapshot_context_query_params(snapshot_context)

    snapshot_url = reverse(
        "browse-snapshot",
        url_args={"snapshot_id": snapshot_id},
        query_params=query_params,
    )
    if not link_text:
        link_text = snapshot_id
    return gen_link(snapshot_url, link_text, link_attrs)


def gen_content_link(
    sha1_git: str,
    snapshot_context: Optional[SnapshotContext] = None,
    link_text: Optional[str] = "Browse",
    link_attrs: Optional[Dict[str, str]] = {
        "class": "btn btn-default btn-sm",
        "role": "button",
    },
) -> Optional[str]:
    """
    Utility function for generating a link to a content HTML view
    to insert in Django templates.

    Args:
        sha1_git: content identifier
        link_text: optional text for the generated link
            (the content sha1_git will be used by default)
        link_attrs: optional attributes (e.g. class)
            to add to the link

    Returns:
        An HTML link in the form '<a href="content_view_url">link_text</a>'

    """
    if not sha1_git:
        return None

    query_params = _snapshot_context_query_params(snapshot_context)

    content_url = reverse(
        "browse-content",
        url_args={"query_string": "sha1_git:" + sha1_git},
        query_params=query_params,
    )
    if not link_text:
        link_text = sha1_git
    return gen_link(content_url, link_text, link_attrs)


def get_revision_log_url(
    revision_id: str, snapshot_context: Optional[SnapshotContext] = None
) -> str:
    """
    Utility function for getting the URL for a revision log HTML view
    (possibly in the context of an origin).

    Args:
        revision_id: revision identifier the history heads to
        snapshot_context: if provided, generate snapshot-dependent
            browsing link
    Returns:
        The revision log view URL
    """
    query_params = {}
    if snapshot_context:
        query_params = _snapshot_context_query_params(snapshot_context)

    query_params["revision"] = revision_id
    if snapshot_context and snapshot_context["origin_info"]:
        revision_log_url = reverse("browse-origin-log", query_params=query_params)
    elif snapshot_context:
        url_args = {"snapshot_id": snapshot_context["snapshot_id"]}
        del query_params["snapshot"]
        revision_log_url = reverse(
            "browse-snapshot-log", url_args=url_args, query_params=query_params
        )
    else:
        revision_log_url = reverse(
            "browse-revision-log", url_args={"sha1_git": revision_id}
        )
    return revision_log_url


def gen_revision_log_link(
    revision_id: str,
    snapshot_context: Optional[SnapshotContext] = None,
    link_text: Optional[str] = "Browse",
    link_attrs: Optional[Dict[str, str]] = {
        "class": "btn btn-default btn-sm",
        "role": "button",
    },
) -> Optional[str]:
    """
    Utility function for generating a link to a revision log HTML view
    (possibly in the context of an origin) to insert in Django templates.

    Args:
        revision_id: revision identifier the history heads to
        snapshot_context: if provided, generate snapshot-dependent
            browsing link
        link_text: optional text to use for the generated link
            (the revision id will be used by default)
        link_attrs: optional attributes (e.g. class)
            to add to the link

    Returns:
        An HTML link in the form
        '<a href="revision_log_view_url">link_text</a>'
    """
    if not revision_id:
        return None

    revision_log_url = get_revision_log_url(revision_id, snapshot_context)

    if not link_text:
        link_text = revision_id
    return gen_link(revision_log_url, link_text, link_attrs)


def gen_person_mail_link(
    person: Dict[str, Any], link_text: Optional[str] = None
) -> str:
    """
    Utility function for generating a mail link to a person to insert
    in Django templates.

    Args:
        person: dictionary containing person data
            (*name*, *email*, *fullname*)
        link_text: optional text to use for the generated mail link
            (the person name will be used by default)

    Returns:
        str: A mail link to the person or the person name if no email is
            present in person data
    """
    person_name = person["name"] or person["fullname"] or "None"
    if link_text is None:
        link_text = person_name
    person_email = person["email"] if person["email"] else None
    if person_email is None and "@" in person_name and " " not in person_name:
        person_email = person_name
    if person_email:
        return gen_link(url="mailto:%s" % person_email, link_text=link_text)
    else:
        return person_name


def gen_release_link(
    sha1_git: str,
    snapshot_context: Optional[SnapshotContext] = None,
    link_text: Optional[str] = "Browse",
    link_attrs: Optional[Dict[str, str]] = {
        "class": "btn btn-default btn-sm",
        "role": "button",
    },
) -> str:
    """
    Utility function for generating a link to a release HTML view
    to insert in Django templates.

    Args:
        sha1_git: release identifier
        link_text: optional text for the generated link
            (the release id will be used by default)
        link_attrs: optional attributes (e.g. class)
            to add to the link

    Returns:
        An HTML link in the form '<a href="release_view_url">link_text</a>'

    """

    query_params = _snapshot_context_query_params(snapshot_context)

    release_url = reverse(
        "browse-release", url_args={"sha1_git": sha1_git}, query_params=query_params
    )
    if not link_text:
        link_text = sha1_git
    return gen_link(release_url, link_text, link_attrs)


def format_log_entries(
    revision_log: Iterator[Optional[Dict[str, Any]]],
    per_page: int,
    snapshot_context: Optional[SnapshotContext] = None,
) -> List[Dict[str, str]]:
    """
    Utility functions that process raw revision log data for HTML display.
    Its purpose is to:

        * add links to relevant browse views
        * format date in human readable format
        * truncate the message log

    Args:
        revision_log: raw revision log as returned by the swh-web api
        per_page: number of log entries per page
        snapshot_context: if provided, generate snapshot-dependent
            browsing link


    """
    revision_log_data = []
    for i, rev in enumerate(revision_log):
        if rev is None:
            continue
        if i == per_page:
            break
        author_name = "None"
        author_fullname = "None"
        committer_fullname = "None"
        if rev["author"]:
            author_name = gen_person_mail_link(rev["author"])
            author_fullname = rev["author"]["fullname"]
        if rev["committer"]:
            committer_fullname = rev["committer"]["fullname"]
        author_date = format_utc_iso_date(rev["date"])
        committer_date = format_utc_iso_date(rev["committer_date"])

        tooltip = "revision %s\n" % rev["id"]
        tooltip += "author: %s\n" % author_fullname
        tooltip += "author date: %s\n" % author_date
        tooltip += "committer: %s\n" % committer_fullname
        tooltip += "committer date: %s\n\n" % committer_date
        if rev["message"]:
            tooltip += textwrap.indent(rev["message"], " " * 4)

        revision_log_data.append(
            {
                "author": author_name,
                "id": rev["id"][:7],
                "message": rev["message"],
                "date": author_date,
                "commit_date": committer_date,
                "url": gen_revision_url(rev["id"], snapshot_context),
                "tooltip": tooltip,
            }
        )
    return revision_log_data


# list of common readme names ordered by preference
# (lower indices have higher priority)
_common_readme_names = [
    "readme.markdown",
    "readme.md",
    "readme.rst",
    "readme.txt",
    "readme",
]


def get_readme_to_display(
    readmes: Dict[str, str]
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Process a list of readme files found in a directory
    in order to find the adequate one to display.

    Args:
        readmes: a dict where keys are readme file names and values
            are readme sha1s

    Returns:
        A tuple (readme_name, readme_url, readme_html)
    """
    readme_name = None
    readme_url = None
    readme_sha1 = None
    readme_html = None

    lc_readmes = {k.lower(): {"orig_name": k, "sha1": v} for k, v in readmes.items()}

    # look for readme names according to the preference order
    # defined by the _common_readme_names list
    for common_readme_name in _common_readme_names:
        if common_readme_name in lc_readmes:
            readme_name = lc_readmes[common_readme_name]["orig_name"]
            readme_sha1 = lc_readmes[common_readme_name]["sha1"]
            readme_url = reverse(
                "browse-content-raw",
                url_args={"query_string": readme_sha1},
                query_params={"re_encode": "true"},
            )
            break

    # otherwise pick the first readme like file if any
    if not readme_name and len(readmes.items()) > 0:
        readme_name = next(iter(readmes))
        readme_sha1 = readmes[readme_name]
        readme_url = reverse(
            "browse-content-raw",
            url_args={"query_string": readme_sha1},
            query_params={"re_encode": "true"},
        )

    # convert rst README to html server side as there is
    # no viable solution to perform that task client side
    if readme_name and readme_name.endswith(".rst"):

        @django_cache(
            catch_exception=True,
            exception_return_value="Readme bytes are not available",
        )
        def _rst_readme_to_html(readme_sha1):
            rst_doc = request_content(readme_sha1)
            return rst_to_html(rst_doc["raw_data"])

        readme_html = _rst_readme_to_html(readme_sha1)

    return readme_name, readme_url, readme_html
