from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView
)
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import (
    UserRegistrationForm, UserLoginForm, UserProfileForm, StyledPasswordChangeForm
)


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Xush kelibsiz, {user.first_name or user.username}! Akkauntingiz muvaffaqiyatli yaratildi.")
            next_url = request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('home')
        else:
            messages.error(request, "Iltimos, formadagi xatoliklarni to'g'rilang.")
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = UserLoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, f"Tizimga muvaffaqiyatli kirdingiz. Xush kelibsiz!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Login yoki parol noto'g'ri kiritildi. Qayta urinib ko'ring.")
        return super().form_invalid(form)


def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.info(request, "Siz tizimdan muvaffaqiyatli chiqdingiz.")
        return redirect('home')
    # If accessed via GET, redirect to home
    return redirect('home')


@login_required
def profile_view(request):
    user = request.user
    profile_form = UserProfileForm(instance=user)
    password_form = StyledPasswordChangeForm(user=user)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_profile':
            profile_form = UserProfileForm(request.POST, request.FILES, instance=user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profil ma'lumotlaringiz muvaffaqiyatli yangilandi.")
                return redirect('accounts:profile')
            else:
                messages.error(request, "Profil ma'lumotlarini saqlashda xatolik yuz berdi.")
        elif action == 'change_password':
            password_form = StyledPasswordChangeForm(user=user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Parolingiz muvaffaqiyatli o'zgartirildi.")
                return redirect('accounts:profile')
            else:
                messages.error(request, "Parolni o'zgartirishda xatolik yuz berdi.")

    # Calculate user statistics
    active_bookings_count = 0
    completed_bookings_count = 0
    cancelled_bookings_count = 0

    if hasattr(user, 'bookings'):
        active_bookings_count = user.bookings.filter(status__in=['PENDING', 'CONFIRMED']).count()
        completed_bookings_count = user.bookings.filter(status='COMPLETED').count()
        cancelled_bookings_count = user.bookings.filter(status__in=['CANCELLED', 'REJECTED']).count()

    context = {
        'profile_form': profile_form,
        'password_form': password_form,
        'active_bookings_count': active_bookings_count,
        'completed_bookings_count': completed_bookings_count,
        'cancelled_bookings_count': cancelled_bookings_count,
    }
    return render(request, 'accounts/profile.html', context)
