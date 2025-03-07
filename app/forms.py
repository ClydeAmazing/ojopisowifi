import psutil

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
	wan_port = forms.ChoiceField()
	lan_port = forms.ChoiceField()
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

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		ethernet_ports = [
			(port, port) for port in psutil.net_if_addrs() 
			# if port.startswith('en') or port.startswith('eth')
		]
		self.fields['wan_port'].choices = ethernet_ports
		self.fields['lan_port'].choices = ethernet_ports

	def clean(self):
		cleaned_data = super().clean()
		wan_port = cleaned_data.get('wan_port')
		lan_port = cleaned_data.get('lan_port')

		if wan_port and lan_port and wan_port == lan_port:
			raise forms.ValidationError('WAN port and LAN port cannot be the same.')
		
		return cleaned_data

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

	def clean(self):
		cleaned_data = super().clean()
		coinslot_pin = cleaned_data.get('Coinslot_Pin')
		light_pin = cleaned_data.get('Light_Pin')
		if coinslot_pin and light_pin:
			if coinslot_pin == light_pin:
				self.add_error(None, 'Coinslot Pin should not be the same as Light Pin.')
		return cleaned_data

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

	def clean(self):
		cleaned_data = super().clean()
		if not cleaned_data.get('Enabled'):
			return

		required_msg = 'This field is required before push notification can be enabled.'
		
		if not cleaned_data.get('app_id'):
			self.add_error('app_id', required_msg)

		if not cleaned_data.get('notification_title'):
			self.add_error('notification_title', required_msg)

		if not self.cleaned_data.get('notification_message'):
			self.add_error('notification_message', required_msg)

		if not self.cleaned_data.get('notification_trigger_time'):
			self.add_error('notification_trigger_time', required_msg)

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