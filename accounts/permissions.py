from functools import wraps
from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages


class ManagerRequiredMixin(AccessMixin):
    """Verify that the current user is authenticated and is a Hotel Manager or Superuser."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_manager:
            messages.error(request, "Ushbu sahifaga kirish uchun mehmonxona menejeri huquqi talab qilinadi.")
            raise PermissionDenied("Faqat mehmonxona menejerlari uchun ruxsat etilgan.")
        return super().dispatch(request, *args, **kwargs)


def manager_required(view_func):
    """Decorator for views that checks that the user is a Hotel Manager."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Iltimos, avval tizimga kiring.")
            return redirect('accounts:login')
        if not request.user.is_manager:
            messages.error(request, "Ushbu amalni bajarish uchun menejer huquqi talab qilinadi.")
            raise PermissionDenied("Faqat mehmonxona menejerlari uchun ruxsat etilgan.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view
