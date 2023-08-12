from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, permissions, status
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum
from django.db.models.functions import TruncMonth, TruncDate
from app import models
from app.opw import cc, grc
from .serializers import AuthClientSerializer, ClientAuthSerializer

from datetime import timedelta
import subprocess, ast


def get_NDS_status():
	ndsctl_res = subprocess.run(['sudo', 'ndsctl', 'json'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	if ndsctl_res.stderr:
		return False
	
	return ast.literal_eval(ndsctl_res.stdout.decode('utf-8'))
class DashboardDetails(APIView):
	def post(self, request, format=None):
		action = request.data.get("action", None)

		if not action:
			return Response(status=status.HTTP_404_NOT_FOUND)

		try:
			if action == 'reset':
				models.Ledger.objects.all().delete()
				message = 'Success'

			elif action == 'generate':
				if not cc():
					response = dict()
					rc = grc()
					message = rc.decode('utf-8')
				else:
					message = 'Device is already activated'

			elif action == 'activate':
				key = request.data.get('key', None)
				if key:
					result = cc(key)
					if not result:
						message = 'Error'
					else:
						device = models.Device.objects.get(pk=1)
						device.Device_ID = key
						device.save()

						message = 'Success'
				else:
					message = "Error"

			else:
				dev = models.Device.objects.get(pk=1)

				if action == 'poweroff':
					dev.action = 1
				elif action == 'reboot':
					dev.action = 2
				elif action == 'refresh':
					dev.action = 3
				dev.save()

				message = "Success"

		except Exception as e:
			message = str(e)

		response = {
			'message': message
		}
		
		return Response(response)


	def get(self, request, format=None):
		serial_error = 'You obtained an unauthorized copy of the software. Wifi hotspot customizations is limited. Please contact seller.'
		sales_format = request.data.get("sales_format", None)

		info = dict()
		try:
			ledger = models.Ledger.objects.all()

			if sales_format == 'Monthly':
				info['sales_trend'] = ledger.annotate(Period=TruncMonth('Date')).values('Period').annotate(Sales=Sum('Denomination')).values_list('Period', 'Sales')
			else:
				info['sales_trend'] = ledger.annotate(Period=TruncDate('Date')).values('Period').annotate(Sales=Sum('Denomination')).values_list('Period', 'Sales')
		except ObjectDoesNotExist:
			info['sales_trend'] = None

		connected_count = 0
		disconnected_count = 0
		
		clients = models.Clients.objects.all()
		for client in clients:
			if client.Connection_Status == 'Connected':
				connected_count += 1
			else:
				disconnected_count += 1

		info['connected_count'] = connected_count
		info['disconnected_count'] = disconnected_count

		# test ndsctl response
		# info['ndsctl'] = get_NDS_status()

		try:
			device = models.Device.objects.get(pk=1)
			cc_res = False
			if cc_res or request.user.is_superuser:
				info['message'] = None
			else:
				info['message'] = serial_error

			if not cc_res:
				info['license_status'] = 'Not Activated'
				info['license'] = None
			else:
				info['license_status'] = 'Activated'
				info['license'] = device.Device_ID

			return Response(info, status=status.HTTP_200_OK)

		except ObjectDoesNotExist:
			info['message'] = serial_error
			return Response(info, status=status.HTTP_200_OK)

class CreateUser(APIView):

	def handle_auth_client(self, request_data):
		"""
		Handles the auth_client BinAuth call from OpenNDS.
		"""
		print('Handled by auth_client')
		serialized_data = AuthClientSerializer(data=request_data)
		if not serialized_data.is_valid():
			return Response(status=status.HTTP_400_BAD_REQUEST)
		
		print('data is valid')
		validated_data = serialized_data.validated_data

		client_mac = validated_data['client_mac']
		client_ip = validated_data['client_ip']
		client_user_agent = validated_data['user_agent']
		client_token = validated_data['client_token']

		defaults = {
			'IP_Address': client_ip,
			'FAS_Session': client_token,
			'Settings_id': 1
		}
		print('preparing defaults')
		client, created = models.Clients.objects.update_or_create(MAC_Address=client_mac, defaults=defaults)
		if created:
			# The client was just created. We will not "authenticate" yet
			return Response(status=status.HTTP_201_CREATED)

		print('Checking if client has time')
		if client.running_time > timedelta(0):
			# Send session length to opennds to authenticate the client
			response_data = {
				'session_length': client.running_time
			}
			return Response(response_data, status=status.HTTP_200_OK)
		
		print('Client does not have time')
		# User has no running session time so we cannot allow opennds to authenticate the user
		return Response(status=status.HTTP_401_UNAUTHORIZED)
	
	def handle_client_auth(self, request_data):
		"""
		Handles the client_auth BinAuth call. On this stage, BinAuth acknowledges that 
		the client was authenticated by OpenNDS.

		We will use this acknowledgement request to start the client time if it is not started yet.
		"""
		print('handled by client_auth')
		print(request_data)
		serialized_data = ClientAuthSerializer(data=request_data)
		if not serialized_data.is_valid():
			print(serialized_data.errors)
			return Response(status=status.HTTP_400_BAD_REQUEST)
		
		validated_data = serialized_data.validated_data
		try:
			client = models.Clients.objects.get(MAC_Address=validated_data['client_mac'])
			client.Connect()
			return Response(status=status.HTTP_200_OK)
		except models.Clients.DoesNotExist:
			# Client not found. Lets return an arbitrary not found response
			return Response(status=status.HTTP_404_NOT_FOUND)

	def post(self, request):
		# print(request.data)
		method = request.data['method']
		if method == 'auth_client':
			return self.handle_auth_client(request.data)
		elif method == 'client_auth':
			return self.handle_client_auth(request.data)
		print(method)
		print(request.data)
		return Response(status=status.HTTP_400_BAD_REQUEST)

class GetUser(APIView):
	authentication_classes = []
	permission_classes = []

	def get(self, request, client_mac):
		try:
			client = models.Clients.objects.get(MAC_Address=client_mac)
			rates = models.Rates.objects.all()
			data = {
				'wifi_name': client.Settings.Hotspot_Name,
				'status': client.Connection_Status,
				'mac_address': client.MAC_Address,
				'ip_address': client.IP_Address,
				'total_time': client.Time_Left if client.Connection_Status == 'Paused' else client.running_time,
				'rates': {rate.Denom: rate.Duration for rate in rates}
			}
			return Response(data, status=status.HTTP_200_OK)
		except models.Clients.DoesNotExist:
			return Response(status=status.HTTP_404_NOT_FOUND)
		
	def post(self, request, client_mac, action):
		try:
			client = models.Clients.objects.get(MAC_Address=client_mac)
			response = False
			if action in ['connect', 'resume']:
				response = client.Connect()
			elif action == 'pause':
				response = client.Pause()
			else:
				return Response(status=status.HTTP_404_NOT_FOUND)
			return Response({'success':response}, status=status.HTTP_200_OK)
		except models.Clients.DoesNotExist:
			return Response(status=status.HTTP_404_NOT_FOUND)
