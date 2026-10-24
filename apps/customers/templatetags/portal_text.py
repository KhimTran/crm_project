from django import template
from django.utils import translation

from apps.customers.portal_text import is_english, tr

register = template.Library()


# tv4: {% t "tiếng Việt" "English" %} – Admin Portal hiện tiếng Anh; thiếu câu tiếng Anh thì tra từ điển EN
@register.simple_tag
def t(vi, en=None):
    if not is_english():
        return vi
    return en if en is not None else tr(vi)


# tv4: {{ survey.title|tr }} – dịch nội dung người dùng nhập (khảo sát) sang tiếng Anh ở Admin Portal
@register.filter(name="tr")
def tr_filter(value):
    return tr(value)


# tv4: nút đổi ngôn ngữ EN | VI (POST kèm CSRF) đặt ở đầu trang Khảo sát/Phản hồi của Admin/Manager
@register.inclusion_tag("partials/lang_switch.html", takes_context=True)
def lang_switch(context):
    request = context["request"]
    return {"request": request, "current": translation.get_language() or "vi", "csrf_token": context.get("csrf_token"),
            "langs": (("en", "EN"), ("vi", "VI"))}
