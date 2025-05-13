from django import template
register = template.Library()

@register.filter(name='tuple_get')
def tuple_get(d, tup):
    return d.get(tup)

@register.simple_tag
def make_key(*args):
    return tuple(args)
