import subprocess, ast, os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'opw.settings')
django.setup()
from app import models

res = subprocess.run(['sudo', 'ndsctl', 'json'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

if not res.stderr:
	ndsctl_response = ast.literal_eval(res.stdout.decode('utf-8'))
	ndsctl_clients = ndsctl_response['clients']

	preauth_clients = []
	auth_clients = []

	for client in ndsctl_clients:
		if ndsctl_clients[client]['state'] == 'Preauthenticated':
			preauth_clients.append(ndsctl_clients[client]['mac'])

		if ndsctl_clients[client]['state'] == 'Authenticated':
			auth_clients.append(ndsctl_clients[client]['mac'])
		
	clients = models.Clients.objects.all()
	whitelists = models.Whitelist.objects.all()
	
	connected_client_list = {c.MAC_Address: {
		'Upload_Rate': c.Upload_Rate, 
		'Download_Rate': c.Upload_Rate,
		'Status': c.Connection_Status} 
		for c in clients if c.Connection_Status == 'Connected'}

	connected_clients = [c for c in connected_client_list]
	whitelisted_clients = [c.MAC_Address for c in whitelists]

	network_settings = models.Network.objects.get(pk=1)

	global_upload_rate = network_settings.Upload_Rate
	global_download_rate = network_settings.Download_Rate

	all_connected_clients = set(connected_clients).union(whitelisted_clients)
	for_auth_clients = set(preauth_clients).intersection(all_connected_clients)
	for_deauth_clients = set(auth_clients).difference(all_connected_clients)

	# Authentication
	for client in for_auth_clients:
		if client in connected_client_list:
			client_data = connected_client_list[client]

			upload_rate = client_data['Upload_Rate'] if client_data['Upload_Rate'] > 0 else global_upload_rate
			download_rate = client_data['Download_Rate'] if client_data['Download_Rate'] > 0 else global_download_rate
		else:
			upload_rate = global_upload_rate
			download_rate = global_download_rate

		cmd = ['sudo', 'ndsctl', 'auth', client, str(0), str(upload_rate), str(download_rate)]
		ndsctl_res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

		if not ndsctl_res.stderr:
			print('Client ' + client + ' successfully authenticated.')

	# Deauthentication
	for client in for_deauth_clients:
		cmd = ['sudo', 'ndsctl', 'deauth', client]
		ndsctl_res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

		if not ndsctl_res.stderr:
			print('Client ' + client + ' sucessfully deauthenticated.')