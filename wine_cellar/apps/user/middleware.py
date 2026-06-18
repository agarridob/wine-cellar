from django.utils import translation


class UserLanguageMiddleware:
    """Activate the authenticated user's saved language preference.

    Django's LocaleMiddleware picks the language from the cookie / Accept-
    Language header, which is per-browser. This middleware runs after
    AuthenticationMiddleware and, for logged-in users, overrides it with
    the language stored on their UserSettings so the preference follows the
    user across browsers and devices.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and hasattr(user, "user_settings"):
            language = user.user_settings.language
            if language:
                translation.activate(language)
                request.LANGUAGE_CODE = translation.get_language()
        return self.get_response(request)
