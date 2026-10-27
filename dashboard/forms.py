from django import forms
from hotels.models import Hotel, Room, RoomImage, Amenity


class HotelForm(forms.ModelForm):
    amenities = forms.ModelMultipleChoiceField(
        queryset=Amenity.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'rounded text-secondary focus:ring-secondary/20'}),
        required=False,
        label="Qulayliklar"
    )

    class Meta:
        model = Hotel
        fields = [
            'name', 'city', 'address', 'stars', 'contact_phone', 'contact_email',
            'check_in_time', 'check_out_time', 'description', 'amenities', 'is_published'
        ]
        labels = {
            'name': 'Mehmonxona nomi',
            'city': 'Shahar',
            'address': 'To‘liq manzil',
            'stars': 'Yulduzlar toifasi (1–5)',
            'contact_phone': 'Aloqa telefoni',
            'contact_email': 'Aloqa pochtasi',
            'check_in_time': 'Kirish vaqti (Check-in)',
            'check_out_time': 'Chiqish vaqti (Check-out)',
            'description': 'Mehmonxona tavsifi',
            'is_published': 'Saytda ko‘rsatilsinmi (Faol)',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-border-subtle bg-white text-sm focus:ring-2 focus:ring-secondary/20'}),
            'city': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-border-subtle bg-white text-sm focus:ring-2 focus:ring-secondary/20'}),
            'address': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-border-subtle bg-white text-sm focus:ring-2 focus:ring-secondary/20'}),
            'stars': forms.NumberInput(attrs={'min': '1', 'max': '5', 'class': 'w-full px-4 py-2.5 rounded-xl border border-border-subtle bg-white text-sm focus:ring-2 focus:ring-secondary/20'}),
            'contact_phone': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-border-subtle bg-white text-sm focus:ring-2 focus:ring-secondary/20'}),
            'contact_email': forms.EmailInput(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-border-subtle bg-white text-sm focus:ring-2 focus:ring-secondary/20'}),
            'check_in_time': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full px-4 py-2.5 rounded-xl border border-border-subtle bg-white text-sm focus:ring-2 focus:ring-secondary/20'}),
            'check_out_time': forms.TimeInput(attrs={'type': 'time', 'class': 'w-full px-4 py-2.5 rounded-xl border border-border-subtle bg-white text-sm focus:ring-2 focus:ring-secondary/20'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'w-full px-4 py-2.5 rounded-xl border border-border-subtle bg-white text-sm focus:ring-2 focus:ring-secondary/20'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'w-5 h-5 rounded text-secondary focus:ring-secondary/20'}),
        }


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = [
            'hotel', 'number', 'title', 'room_type', 'capacity_adults',
            'capacity_children', 'price_per_night', 'description', 'is_active'
        ]
        labels = {
            'hotel': 'Mehmonxona',
            'number': 'Xona raqami',
            'title': 'Xona nomi',
            'room_type': 'Toifasi',
            'capacity_adults': 'Kattalar sig‘imi',
            'capacity_children': 'Bolalar sig‘imi',
            'price_per_night': 'Bir kecha narxi (so‘m)',
            'description': 'Xona haqida',
            'is_active': 'Xona faol holatdami',
        }
        widgets = {
            'hotel': forms.Select(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-border-subtle bg-white text-sm focus:ring-2 focus:ring-secondary/20'}),
            'number': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-border-subtle bg-white text-sm focus:ring-2 focus:ring-secondary/20'}),
            'title': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-border-subtle bg-white text-sm focus:ring-2 focus:ring-secondary/20'}),
            'room_type': forms.Select(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-border-subtle bg-white text-sm focus:ring-2 focus:ring-secondary/20'}),
            'capacity_adults': forms.NumberInput(attrs={'min': '1', 'class': 'w-full px-4 py-2.5 rounded-xl border border-border-subtle bg-white text-sm focus:ring-2 focus:ring-secondary/20'}),
            'capacity_children': forms.NumberInput(attrs={'min': '0', 'class': 'w-full px-4 py-2.5 rounded-xl border border-border-subtle bg-white text-sm focus:ring-2 focus:ring-secondary/20'}),
            'price_per_night': forms.NumberInput(attrs={'step': '1000', 'class': 'w-full px-4 py-2.5 rounded-xl border border-border-subtle bg-white text-sm focus:ring-2 focus:ring-secondary/20'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-4 py-2.5 rounded-xl border border-border-subtle bg-white text-sm focus:ring-2 focus:ring-secondary/20'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'w-5 h-5 rounded text-secondary focus:ring-secondary/20'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and not user.is_superuser:
            # Strictly limit hotel choices to this manager's hotels
            self.fields['hotel'].queryset = Hotel.objects.filter(manager=user)


class RoomImageForm(forms.ModelForm):
    class Meta:
        model = RoomImage
        fields = ['image', 'sort_order', 'is_primary']
        labels = {
            'image': 'Surat',
            'sort_order': 'Tartib raqami',
            'is_primary': 'Asosiy surat',
        }
        widgets = {
            'image': forms.FileInput(attrs={'class': 'w-full text-xs text-gray-500 file:py-1.5 file:px-3 file:rounded-xl file:border-0 file:bg-surface-container file:text-primary'}),
            'sort_order': forms.NumberInput(attrs={'class': 'w-24 px-3 py-1.5 rounded-xl border border-border-subtle text-xs'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'w-4 h-4 rounded text-secondary'}),
        }
