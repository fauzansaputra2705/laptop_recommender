from django import template

register = template.Library()


@register.filter
def get_attr(obj, attr):
    """Get an attribute from an object dynamically. Supports __ lookups.
    Usage: {{ obj|get_attr:"field_name" }} or {{ obj|get_attr:"user__username" }}"""
    try:
        value = obj
        for part in attr.split("__"):
            value = getattr(value, part)
            if callable(value):
                value = value()
        return value
    except (AttributeError, TypeError):
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
