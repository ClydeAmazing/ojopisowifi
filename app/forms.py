from django import forms
from django.core.validators import validate_ipv4_address
from app import models

class ClientsForm(forms.ModelForm):
	Time_Left= forms.CharField(widget=forms.TextInput
		(attrs={'class':'vTextField'}))
	
	class Meta:
		model = models.Clients
		fields = '__all__'

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

class SettingsForm(forms.ModelForm):
	Base_Value= forms.CharField(widget= forms.TextInput
		(attrs={'class':'vTextField'}))
	Disable_Pause_Time= forms.CharField(widget= forms.TextInput
		(attrs={'class':'vTextField'}))

	class Meta:
		model = models.Settings
		fields = '__all__'