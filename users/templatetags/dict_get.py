# your_app/templatetags/dict_get.py
from django import template
register = template.Library()
@register.filter
def dict_get(d, key):
    return d.get(int(key), {})
