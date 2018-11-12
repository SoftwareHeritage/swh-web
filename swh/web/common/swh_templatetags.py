# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json
import re

from django import template
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.safestring import mark_safe

from docutils.core import publish_parts
from docutils.writers.html4css1 import Writer, HTMLTranslator
from inspect import cleandoc

register = template.Library()


class NoHeaderHTMLTranslator(HTMLTranslator):
    """
    Docutils translator subclass to customize the generation of HTML
    from reST-formatted docstrings
    """
    def __init__(self, document):
        super().__init__(document)
        self.body_prefix = []
        self.body_suffix = []

    def visit_bullet_list(self, node):
        self.context.append((self.compact_simple, self.compact_p))
        self.compact_p = None
        self.compact_simple = self.is_compactable(node)
        self.body.append(self.starttag(node, 'ul', CLASS='docstring'))


DOCSTRING_WRITER = Writer()
DOCSTRING_WRITER.translator_class = NoHeaderHTMLTranslator


@register.filter
def safe_docstring_display(docstring):
    """
    Utility function to htmlize reST-formatted documentation in browsable
    api.
    """
    docstring = cleandoc(docstring)
    return publish_parts(docstring, writer=DOCSTRING_WRITER)['html_body']


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
        text = re.sub(r'(/api/[^"<]*|/browse/[^"<]*|http.*$)',
                      r'<a href="\1">\1</a>',
                      text)
        return re.sub(r'([^ <>"]+@[^ <>"]+)',
                      r'<a href="mailto:\1">\1</a>',
                      text)
    else:
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
    links = text.split(',')
    ret = ''
    for i, link in enumerate(links):
        ret += re.sub(r'<(/api/.*|/browse/.*)>', r'<<a href="\1">\1</a>>',
                      link)
        # add one link per line and align them
        if i != len(links) - 1:
            ret += '\n     '
    return ret


@register.filter
def jsonify(obj):
    """Utility function for converting a django template variable
    to JSON in order to use it in script tags.

    Args
        obj: Any django template context variable

    Returns:
        JSON representation of the variable.

    """
    return mark_safe(json.dumps(obj, cls=DjangoJSONEncoder))


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
