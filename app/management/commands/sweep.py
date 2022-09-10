from django.core.management.base import BaseCommand
from app.utils import get_active_clients, run_command
import ast, time

class Command(BaseCommand):
    help = 'I am a mess Sweeper.'

    def handle(self, *args, **kwargs):
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

            clients = get_active_clients()
            connected_clients = clients['clients']
            
            for_auth_clients = set([*connected_clients]).difference(auth_clients)
            for_deauth_clients = set(auth_clients).difference([*connected_clients])

            # Authentication
            for c in for_auth_clients:
                c_details = connected_clients.get(c)
                if c_details:
                    auth_cmd = ['sudo', 'ndsctl', 'auth', c, '0', str(c_details['u']), str(c_details['d']), '0', '0']
                    run_command(auth_cmd)

                time.sleep(1)

            # Deauthentication
            for c in for_deauth_clients:
                deauth_cmd = ['sudo', 'ndsctl', 'deauth', c]
                run_command(deauth_cmd)

                time.sleep(1)

        except (SyntaxError, ValueError):
            return False