from django import forms
from core.models import Courier


class Driverdetailform(forms.ModelForm):
    class Meta:
        model = Courier
        fields  = ('phone_number','vehicle')


class PayoutForm(forms.ModelForm):
    class Meta:
        model = Courier
        fields = ('paypal_email',)


class ChangeAvatarForm(forms.ModelForm):
    class Meta:
        model = Courier
        fields = ('avatar',)






'''class Driverdetailform(forms.ModelForm):
    phone_number = forms.CharField(required=True)
    vehicle = forms.ChoiceField(choices=VEHICLES_CHOICES)

    class Meta:
        model = Driverdetails
        fields = ('phone_number', 'vehicle')
'''