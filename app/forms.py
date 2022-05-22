from django import forms
from django.core.validators import validate_ipv4_address
from app import models

class ClientsForm(forms.ModelForm):
	
	class Meta:
		model = models.Clients
		fields = '__all__'

		widgets = {
			'Time_Left': forms.TextInput(attrs={
				'placeholder': '00:00:00',
				'class': 'vTimeField',
				'style': 'margin-top: 0px;'
			})
		}

class NetworkForm(forms.ModelForm):
	Server_IP= forms.CharField(widget=forms.TextInput
		(attrs={'class':'vTextField'}), validators=[validate_ipv4_address])
	Netmask= forms.CharField(widget= forms.TextInput
		(attrs={'class':'vTextField'}), validators=[validate_ipv4_address])
	DNS_1= forms.CharField(widget= forms.TextInput
		(attrs={'class':'vTextField'}), validators=[validate_ipv4_address])
	DNS_2= forms.CharField(widget= forms.TextInput
		(attrs={'class':'vTextField'}), validators=[validate_ipv4_address])
	
	class Meta:
		model = models.Network
		fields = '__all__'

class VouchersForm(forms.ModelForm):

	class Meta:
		model = models.Vouchers
		fields = '__all__'

		widgets = {
			'Voucher_time_value': forms.TextInput(attrs={
				'placeholder': '00:00:00', 
				'class': 'vTimeField',
				'style': 'margin-top: 0px;'
			})
		}

class SettingsForm(forms.ModelForm):

	class Meta:
		model = models.Settings
		fields = '__all__'

		widgets = {
			'Base_Value': forms.TextInput(attrs={
				'placeholder': '00:00:00',
				'class': 'vTimeField',
				'style': 'margin-top: 0px;'
			}),
			'Disable_Pause_Time': forms.TextInput(attrs={
				'placeholder': '00:00:00',
				'class': 'vTimeField',
				'style': 'margin-top: 0px;'
			})
		}

class RatesForm(forms.ModelForm):

	class Meta:
		model = models.Rates
		fields = '__all__'

		widgets = {
			'Minutes': forms.TextInput(attrs={
				'placeholder': '00:00:00',
				'class': 'vTimeField',
				'style': 'margin-top: 0px;'
			})
		}

class CoinSlotForm(forms.ModelForm):

	class Meta:
		model = models.CoinSlot
		fields = '__all__'

class PushNotifForm(forms.ModelForm):
	
	class Meta:
		model = models.PushNotifications
		fields = '__all__'

		widgets = {
			'notification_trigger_time': forms.TextInput(attrs={
				'placeholder': '00:00:00',
				'class': 'vTimeField',
				'style': 'margin-top: 0px;'
			})
		}