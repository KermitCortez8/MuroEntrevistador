"""Markdown sin HTML crudo ni enlaces con protocolos peligrosos."""

from django import template
from django.utils.safestring import mark_safe
from markdown_it import MarkdownIt

register = template.Library()


@register.filter
def richtext(value):
    return mark_safe(MarkdownIt("commonmark", {"html": False, "breaks": True}).render(value or ""))
