from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
def get_attr(obj, attr):
    """Get an attribute from an object dynamically. Usage: {{ obj|get_attr:"field_name" }}"""
    try:
        value = getattr(obj, attr)
        if callable(value):
            return value()
        return value
    except AttributeError:
        return ""


@register.inclusion_tag("datatable/table.html", takes_context=True)
def datatable(context):
    """Render a full HTMX datatable component.

    Expects context["datatable"] dict set by DatatableViewMixin.
    Usage in template:
        {% load datatable %}
        {% datatable %}
    """
    return context.get("datatable", {})
