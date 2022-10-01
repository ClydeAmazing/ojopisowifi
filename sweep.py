import subprocess
import requests

import ast, time

CLIENTS_ENDPOINT_URL = 'http://localhost:8000/app/clients'

def run_command(command):
    try:
        res = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return res
    except FileNotFoundError:
        return None

def sweep(connected_clients):
    ndsctl_res = run_command(['sudo', 'ndsctl', 'json'])

    if not ndsctl_res or ndsctl_res.stderr:
        return False

    try:
        ndsctl_response = ast.literal_eval(ndsctl_res.stdout.decode('utf-8'))
        ndsctl_clients = ndsctl_response['clients']

        preauth_clients = []
        auth_clients = []

        for c in ndsctl_clients:
            client_status = ndsctl_clients[c]['state']
            if client_status == 'Preauthenticated':
                preauth_clients.append(c)
            elif client_status == 'Authenticated':
                auth_clients.append(c)
        
        for_auth_clients = set([*connected_clients]).difference(auth_clients)
        for_deauth_clients = set(auth_clients).difference([*connected_clients])

        # Authentication
        for c in for_auth_clients:
            c_details = connected_clients.get(c)
            if c_details:
                auth_cmd = ['sudo', 'ndsctl', 'auth', c, '0', str(c['u']), str(['d']), '0', '0']
                run_command(auth_cmd)

            time.sleep(0.5)

        # Deauthentication
        for c in for_deauth_clients:
            deauth_cmd = ['sudo', 'ndsctl', 'deauth', c]
            run_command(deauth_cmd)

            time.sleep(0.5)

    except (SyntaxError, ValueError):
        return False

if __name__ == '__main__':
    # Instantiate new http session
    session = requests.Session()

    while True:
        res = session.get(CLIENTS_ENDPOINT_URL, data={})
        if res.status_code == 200:
            response_data = res.json()
            sweep(response_data['clients'])

        time.sleep(5)