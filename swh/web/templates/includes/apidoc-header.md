<ul>
  <li><a href="#endpoint-index">Endpoint index</a></li>
  <li><a href="#data-model">Data model</a></li>
  <li><a href="#version">Version</a></li>
  <li><a href="#schema">Schema</a></li>
  <li><a href="#parameters">Parameters</a></li>
  <li><a href="#errors">Errors</a></li>
  <li><a href="#pagination">Pagination</a></li>
  <li><a href="#rate-limiting">Rate limiting</a></li>
</ul>

### Endpoint index

You can jump directly to the <strong><a href="/api/1/">endpoint
index</a></strong>, which lists all available API functionalities, or read on
for more general information about the API.


### Data model

The [Software Heritage](https://www.softwareheritage.org/) project harvests
publicly available source code by tracking software distribution channels such
as version control systems, tarball releases, and distribution packages.

All retrieved source code and related metadata are stored in the Software
Heritage archive, that is conceptually
a [Merkle DAG](https://en.wikipedia.org/wiki/Merkle_tree). All nodes in the
graph are content-addressable, i.e., their node identifiers are computed by
hashing their content and, transitively, that of all nodes reachable from them;
and no node or edge is ever removed from the graph: the Software Heritage
archive is an append-only data structure.

The following types of objects (i.e., graph nodes) can be found in the Software
Heritage archive <small>(for more information see
the
[Software Heritage glossary](https://docs.softwareheritage.org/devel/glossary.html))</small>:

- **Content**: a specific version of a file stored in the archive, identified
  by its cryptographic hashes (currently: SHA1, Git-like "salted" SHA1,
  SHA256). Note that content objects are nameless; their names are
  context-dependent and stored as part of directory entries (see below).<br />
  *Also known as:* "blob"
- **Directory**: a list of directory entries, where each entry can point to
  content objects ("file entries"), revisions ("revision entries"), or
  transitively to other directories ("directory entries"). All entries are
  associated to the local name of the entry (i.e., a relative path without any
  path separator) and permission metadata (e.g., chmod value or equivalent).
- **Revision**: a point in time snapshot of the content of a directory,
  together with associated development metadata (e.g., author, timestamp, log
  message, etc).<br />
  *Also known as:* "commit".
- **Release**: a revision that has been marked as noteworthy with a specific
  name (e.g., a version number), together with associated development metadata
  (e.g., author, timestamp, etc).<br />
  *Also known as:* "tag"
- **Origin**: an Internet-based location from which a coherent set of objects
  (contents, revisions, releases, etc.) archived by Software Heritage has been
  obtained. Origins are currently identified by URLs.
- **Visit**: the passage of Software Heritage on a given origin, to retrieve
  all source code and metadata available there at the time. A visit object
  stores the state of all visible branches (if any) available at the origin at
  visit time; each of them points to a revision object in the archive. Future
  visits of the same origin will create new visit objects, without removing
  previous ones.
- **Person**: an entity referenced by a revision as either the author or the
  committer of the corresponding change. A person is associated to a full name
  and/or an email address.


### Version

The current version of the API is **v1**.

**Warning:** this version of the API is not to be considered stable yet.
Non-backward compatible changes might happen even without changing the API
version number.


### Schema

API access is over HTTPS.

All API endpoints are rooted at <https://archive.softwareheritage.org/api/1/>.

Data is sent and received as JSON by default.

Example:

- from the command line:
``` shell
curl -i https://archive.softwareheritage.org/api/1/stat/counters/
```

#### Response format override

The response format can be overridden using the `Accept` request header. In
particular, `Accept: text/html` (that web browsers send by default) requests
HTML pretty-printing, whereas `Accept: application/yaml` requests YAML-encoded
responses.

Example:

- [/api/1/stat/counters/](/api/1/stat/counters/)
- from the command line:
``` shell
curl -i -H 'Accept: application/yaml' https://archive.softwareheritage.org/api/1/stat/counters/
```

### Parameters

Some API endpoints can be tweaked by passing optional parameters. For GET
requests, optional parameters can be passed as an HTTP query string.

The optional parameter `fields` is accepted by all endpoints that return
dictionaries and can be used to restrict the list of fields returned by the
API, in case you are not interested in all of them. By default, all available
fields are returned.

Example:

- [/api/1/stat/counters/\?fields\=content,directory,revision](/api/1/stat/counters/?fields=content,directory,revision)
- from the command line:
``` shell
curl https://archive.softwareheritage.org/api/1/stat/counters/?fields=content,directory,revision
```


### Errors

While API endpoints will return different kinds of errors depending on their
own semantics, some error patterns are common across all endpoints.

Sending malformed data, including syntactically incorrect object identifiers,
will result in a `400 Bad Request` HTTP response. Example:

- [/api/1/content/deadbeef/](/api/1/content/deadbeef/) (client error:
  "deadbeef" is too short to be a syntactically valid object identifier)
- from the command line:
``` shell
curl -i https://archive.softwareheritage.org/api/1/content/deadbeef/
```

Requesting non existent resources will result in a `404 Not Found` HTTP
response. Example:

- [/api/1/content/0123456789abcdef0123456789abcdef01234567/](/api/1/content/0123456789abcdef0123456789abcdef01234567/)
  (error: no object with that identifier is available [yet?])
- from the command line:
``` shell
curl -i https://archive.softwareheritage.org/api/1/content/04740277a81c5be6c16f6c9da488ca073b770d7f/
```

Unavailability of the underlying storage backend will result in a `503 Service
Unavailable` HTTP response.


### Pagination

Requests that might potentially return many items will be paginated.

Page size is set to a default (usually: 10 items), but might be overridden with
the `per_page` query parameter up to a maximum (usually: 50 items). Example:

``` shell
curl https://archive.softwareheritage.org/api/1/origin/1/visits/?per_page=2
```

To navigate through paginated results, a `Link` HTTP response header is
available to link the current result page to the next one. Example:

    curl -i https://archive.softwareheritage.org/api/1/origin/1/visits/?per_page=2 | grep ^Link:
    Link: </api/1/origin/1/visits/?last_visit=2&per_page=2>; rel="next",


### Rate limiting

Due to limited resource availability on the back end side, API usage is
currently rate limited.  Furthermore, as API usage is currently entirely
anonymous (i.e., without any authentication), API "users" are currently
identified by their origin IP address.

Three HTTP response fields will inform you about the current state of limits
that apply to your current rate limiting bucket:

- `X-RateLimit-Limit`: maximum number of permitted requests per hour
- `X-RateLimit-Remaining`: number of permitted requests remaining before the
  next reset
- `X-RateLimit-Reset`: the time (expressed
  in [Unix time](https://en.wikipedia.org/wiki/Unix_time) seconds) at which the
  current rate limiting will expire, resetting to a fresh `X-RateLimit-Limit`

Example:

    curl -i https://archive.softwareheritage.org/api/1/stat/counters/ | grep ^X-RateLimit
    X-RateLimit-Limit: 60
    X-RateLimit-Remaining: 54
    X-RateLimit-Reset: 1485794532
