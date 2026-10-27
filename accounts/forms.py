from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from .models import UserRole

User = get_user_model()


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        label="Parol",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Kamida 8 ta belgi kiriting',
            'class': 'w-full px-4 py-3 rounded-xl border border-border-subtle bg-white focus:outline-none focus:ring-2 focus:ring-secondary/20 focus:border-secondary transition-all text-sm'
        })
    )
    confirm_password = forms.CharField(
        label="Parolni tasdiqlang",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Parolni qayta kiriting',
            'class': 'w-full px-4 py-3 rounded-xl border border-border-subtle bg-white focus:outline-none focus:ring-2 focus:ring-secondary/20 focus:border-secondary transition-all text-sm'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone']
        labels = {
            'username': 'Foydalanuvchi nomi (Login)',
            'email': 'Elektron pochta manzili',
            'first_name': 'Ismingiz',
            'last_name': 'Familiyangiz',
            'phone': 'Telefon raqamingiz',
        }
        widgets = {
            'username': forms.TextInput(attrs={
                'placeholder': 'masalan: alisher_99',
                'class': 'w-full px-4 py-3 rounded-xl border border-border-subtle bg-white focus:outline-none focus:ring-2 focus:ring-secondary/20 focus:border-secondary transition-all text-sm'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'masalan: alisher@mail.uz',
                'class': 'w-full px-4 py-3 rounded-xl border border-border-subtle bg-white focus:outline-none focus:ring-2 focus:ring-secondary/20 focus:border-secondary transition-all text-sm'
            }),
            'first_name': forms.TextInput(attrs={
                'placeholder': 'Ismingiz',
                'class': 'w-full px-4 py-3 rounded-xl border border-border-subtle bg-white focus:outline-none focus:ring-2 focus:ring-secondary/20 focus:border-secondary transition-all text-sm'
            }),
            'last_name': forms.TextInput(attrs={
                'placeholder': 'Familiyangiz',
                'class': 'w-full px-4 py-3 rounded-xl border border-border-subtle bg-white focus:outline-none focus:ring-2 focus:ring-secondary/20 focus:border-secondary transition-all text-sm'
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': '+998 90 123 45 67',
                'class': 'w-full px-4 py-3 rounded-xl border border-border-subtle bg-white focus:outline-none focus:ring-2 focus:ring-secondary/20 focus:border-secondary transition-all text-sm'
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ushbu email manzili allaqachon ro'yxatdan o'tgan.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('confirm_password')
        if p1 and p2 and p1 != p2:
            self.add_error('confirm_password', "Kiritilgan parollar bir-biriga mos kelmadi.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        # Role is explicitly CUSTOMER upon registration, manager can only be assigned by Admin
        user.role = UserRole.CUSTOMER
        if commit:
            user.save()
        return user


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Login yoki Email",
        widget=forms.TextInput(attrs={
            'placeholder': 'Login yoki pochtangiz',
            'class': 'w-full px-4 py-3 rounded-xl border border-border-subtle bg-white focus:outline-none focus:ring-2 focus:ring-secondary/20 focus:border-secondary transition-all text-sm'
        })
    )
    password = forms.CharField(
        label="Parol",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Parolingizni kiriting',
            'class': 'w-full px-4 py-3 rounded-xl border border-border-subtle bg-white focus:outline-none focus:ring-2 focus:ring-secondary/20 focus:border-secondary transition-all text-sm'
        })
    )


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'avatar']
        labels = {
            'first_name': 'Ism',
            'last_name': 'Familiya',
            'email': 'Email',
            'phone': 'Telefon raqami',
            'avatar': 'Profil rasmi',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl border border-border-subtle bg-white focus:outline-none focus:ring-2 focus:ring-secondary/20 focus:border-secondary transition-all text-sm'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl border border-border-subtle bg-white focus:outline-none focus:ring-2 focus:ring-secondary/20 focus:border-secondary transition-all text-sm'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl border border-border-subtle bg-white focus:outline-none focus:ring-2 focus:ring-secondary/20 focus:border-secondary transition-all text-sm'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl border border-border-subtle bg-white focus:outline-none focus:ring-2 focus:ring-secondary/20 focus:border-secondary transition-all text-sm'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-surface-container file:text-primary hover:file:bg-surface-variant cursor-pointer'
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Ushbu email manzili boshqa foydalanuvchiga tegishli.")
        return email


class StyledPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full px-4 py-2.5 rounded-xl border border-border-subtle bg-white focus:outline-none focus:ring-2 focus:ring-secondary/20 focus:border-secondary transition-all text-sm'
            })
