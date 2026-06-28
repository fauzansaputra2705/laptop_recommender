from django import template

register = template.Library()


@register.filter
def dict_lookup(d, key):
    """Look up a key in a dict. Usage: {{ mydict|dict_lookup:key }}"""
    if isinstance(d, dict):
        return d.get(key)
    return ""


@register.filter
def list_index(lst, idx):
    """Get item at index from list. Usage: {{ mylist|list_index:0 }}"""
    try:
        return lst[idx]
    except (IndexError, TypeError):
        return ""


@register.filter
def sum_list(lst):
    """Sum all items in a list. Usage: {{ mylist|sum_list }}"""
    try:
        return sum(lst)
    except TypeError:
        return 0


@register.filter
def mul(a, b):
    """Multiply two values. Usage: {{ a|mul:b }}"""
    try:
        return float(a) * float(b)
    except (TypeError, ValueError):
        return 0
