from django import forms
from django.utils import timezone
from .models import Booking


class BookingCreateForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['check_in', 'check_out', 'adults', 'children', 'guest_name', 'guest_phone', 'special_requests']
        labels = {
            'check_in': 'Kirish sanasi',
            'check_out': 'Chiqish sanasi',
            'adults': 'Kattalar soni',
            'children': 'Bolalar soni',
            'guest_name': 'Mehmonning to‘liq ismi',
            'guest_phone': 'Aloqa telefon raqami',
            'special_requests': 'Maxsus istaklar (ixtiyoriy)',
        }
        widgets = {
            'check_in': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-3 rounded-xl border border-border-subtle bg-white focus:outline-none focus:ring-2 focus:ring-secondary/20 focus:border-secondary transition-all text-sm font-medium'
            }),
            'check_out': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-3 rounded-xl border border-border-subtle bg-white focus:outline-none focus:ring-2 focus:ring-secondary/20 focus:border-secondary transition-all text-sm font-medium'
            }),
            'adults': forms.NumberInput(attrs={
                'min': '1',
                'class': 'w-full px-4 py-3 rounded-xl border border-border-subtle bg-white focus:outline-none focus:ring-2 focus:ring-secondary/20 focus:border-secondary transition-all text-sm font-medium'
            }),
            'children': forms.NumberInput(attrs={
                'min': '0',
                'class': 'w-full px-4 py-3 rounded-xl border border-border-subtle bg-white focus:outline-none focus:ring-2 focus:ring-secondary/20 focus:border-secondary transition-all text-sm font-medium'
            }),
            'guest_name': forms.TextInput(attrs={
                'placeholder': 'masalan: Alisher Usmonov',
                'class': 'w-full px-4 py-3 rounded-xl border border-border-subtle bg-white focus:outline-none focus:ring-2 focus:ring-secondary/20 focus:border-secondary transition-all text-sm'
            }),
            'guest_phone': forms.TextInput(attrs={
                'placeholder': '+998 90 123 45 67',
                'class': 'w-full px-4 py-3 rounded-xl border border-border-subtle bg-white focus:outline-none focus:ring-2 focus:ring-secondary/20 focus:border-secondary transition-all text-sm'
            }),
            'special_requests': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Kechroq kelish, tinch qavat yoki boshqa istaklar bo‘lsa yozing...',
                'class': 'w-full px-4 py-3 rounded-xl border border-border-subtle bg-white focus:outline-none focus:ring-2 focus:ring-secondary/20 focus:border-secondary transition-all text-sm'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in')
        check_out = cleaned_data.get('check_out')

        if check_in and check_out:
            today = timezone.localdate()
            if check_in < today:
                self.add_error('check_in', "Kirish sanasi bugungi kundan oldin bo‘lishi mumkin emas.")
            if check_in >= check_out:
                self.add_error('check_out', "Chiqish sanasi kirish sanasidan keyin bo‘lishi kerak.")
            else:
                nights = (check_out - check_in).days
                if nights < 1:
                    self.add_error('check_out', "Minimal bron muddati 1 kecha.")
                if nights > 30:
                    self.add_error('check_out', "Maksimal bron muddati 30 kecha.")

        return cleaned_data
