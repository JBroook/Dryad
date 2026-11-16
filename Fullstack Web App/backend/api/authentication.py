from django.conf import settings
from django.middleware.csrf import CsrfViewMiddleware
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.authentication import JWTAuthentication


class _CSRFCheck(CsrfViewMiddleware):
    def _reject(self, request, reason):
        return reason


def enforce_csrf(request):
    django_request = request._request
    check = _CSRFCheck(lambda request: None)
    check.process_request(django_request)
    reason = check.process_view(django_request, None, (), {})
    if reason:
        raise PermissionDenied(f"CSRF Failed: {reason}")


class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        header_auth = super().authenticate(request)
        if header_auth is not None:
            return header_auth

        raw_token = request.COOKIES.get(settings.JWT_ACCESS_COOKIE_NAME)
        if raw_token is None:
            return None

        enforce_csrf(request)
        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token
