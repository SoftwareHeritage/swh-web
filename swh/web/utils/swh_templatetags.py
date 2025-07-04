# Copyright (C) 2017-2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json
import re

from django import template
from django.contrib.staticfiles.finders import find
from django.utils.safestring import mark_safe

from swh.web.save_code_now.origin_save import get_savable_visit_types
from swh.web.utils import rst_to_html
from swh.web.utils.converters import SWHDjangoJSONEncoder

register = template.Library()


@register.filter
def docstring_display(docstring):
    """
    Utility function to htmlize reST-formatted documentation in browsable
    api.
    """
    return rst_to_html(docstring, raw_enabled=True)


@register.filter
def urlize_links_and_mails(text):
    """Utility function for decorating api links in browsable api.

    Args:
        text: whose content matching links should be transformed into
        contextual API or Browse html links.

    Returns
        The text transformed if any link is found.
        The text as is otherwise.

    """
    if 'href="' not in text:
        text = re.sub(r"(http.*)", r'<a href="\1">\1</a>', text)
        mails = set()
        for mail in re.findall(r'([^ <>"]+@[^ <>"]+)', text):
            if not mail.startswith(("http://", "https://")):
                mails.add(mail)
        for mail in mails:
            text = text.replace(mail, f'<a href="mailto:{mail}">{mail}</a>')

    return text


@register.filter
def urlize_header_links(text):
    """Utility function for decorating headers links in browsable api.

    Args
        text: Text whose content contains Link header value

    Returns:
        The text transformed with html link if any link is found.
        The text as is otherwise.

    """
    ret = re.sub(
        r'<(http[^<>]+)>; rel="([^,]+)"',
        r'<<a href="\1">\1</a>>; rel="\2"\n',
        str(text),
    ).replace("\n,", "\n")
    return ret[:-1]


@register.filter
def jsonify(obj):
    """Utility function for converting a django template variable
    to JSON in order to use it in script tags.

    Args
        obj: Any django template context variable

    Returns:
        JSON representation of the variable.

    """
    return mark_safe(json.dumps(obj, cls=SWHDjangoJSONEncoder))


@register.filter
def sub(value, arg):
    """Django template filter for subtracting two numbers

    Args:
        value (int/float): the value to subtract from
        arg (int/float): the value to subtract to

    Returns:
        int/float: The subtraction result
    """
    return value - arg


@register.filter
def mul(value, arg):
    """Django template filter for multiplying two numbers

    Args:
        value (int/float): the value to multiply from
        arg (int/float): the value to multiply with

    Returns:
        int/float: The multiplication result
    """
    return value * arg


@register.filter
def key_value(dict, key):
    """Django template filter to get a value in a dictionary.

    Args:
        dict (dict): a dictionary
        key (str): the key to lookup value

    Returns:
        The requested value in the dictionary
    """
    return dict[key]


@register.filter
def visit_type_savable(visit_type: str) -> bool:
    """Django template filter to check if a save request can be
    created for a given visit type.

        Args:
            visit_type: the type of visit

        Returns:
            If the visit type is saveable or not

    """
    return visit_type in get_savable_visit_types()


@register.filter
def split(value, arg):
    """Django template filter to split a string.

    Args:
        value (str): the string to split
        arg (str): the split separator

    Returns:
        list: the split string parts
    """
    return value.split(arg)


@register.filter
def static_path_exists(path: str) -> bool:
    """Django template filter to check a static path exists.

    Args:
        path: static path to check existence.

    Returns:
        Whether the path exists.
    """
    return bool(find(path))
