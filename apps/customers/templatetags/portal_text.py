from django import template

from apps.customers.portal_text import is_english, tr

register = template.Library()


# tv4: {% t "tiếng Việt" "English" %} – Admin Portal hiện tiếng Anh; thiếu câu tiếng Anh thì tra từ điển EN
@register.simple_tag
def t(vi, en=None):
    if not is_english():
        return vi
    return en if en is not None else tr(vi)
