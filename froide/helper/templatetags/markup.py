from django import template
from django.conf import settings
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(is_safe=True)
def markdown(value, arg=''):
    """
    Taken from Django 1.4 to avoid deprecation warnings

    Runs Markdown over a given value, optionally using various
    extensions python-markdown supports.

    Syntax::

        {{ value|markdown:"extension1_name,extension2_name..." }}

    To enable safe mode, which strips raw HTML and only returns HTML
    generated by actual Markdown syntax, pass "safe" as the first
    extension in the list.

    If the version of Markdown in use does not support extensions,
    they will be silently ignored.

    """
    try:
        import markdown
    except ImportError:
        if settings.DEBUG:
            raise template.TemplateSyntaxError("Error in 'markdown' filter: The Python markdown library isn't installed.")
        return force_unicode(value)
    else:
        extensions = [e for e in arg.split(",") if e]
        if len(extensions) > 0 and extensions[0] == "safe":
            extensions = extensions[1:]
            safe_mode = True
        else:
            safe_mode = False
        if safe_mode:
            return mark_safe(markdown.markdown(force_unicode(value), extensions, safe_mode=safe_mode,
                enable_attributes=False))
        else:
            return mark_safe(markdown.markdown(force_unicode(value), extensions, safe_mode=safe_mode))
