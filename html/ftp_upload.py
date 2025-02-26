import os
import paramiko

def sftp_upload(sftp, local_path, remote_path):
    try:
        sftp.put(local_path, remote_path)
        print("File upload successful.")
    except Exception as e:
        print("An error occurred:", e)

files = [
    {
        'file': './main.css',
        'target': '/etc/opennds/htdocs/'
    },
    {
        'file': './splash.html',
        'target': '/etc/opennds/htdocs/'
    },
    {
        'file': './theme_click-to-continue-legacy.sh',
        'target': '/usr/lib/opennds/'
    },
    {
        'file': '../opennds/ojo_binauth.sh',
        'target': '/usr/lib/opennds/'
    },
    {
        'file': './client_params.sh',
        'target': '/usr/lib/opennds/'
    }
]

hostname = '192.168.8.1'
port = 22
username = 'root'
password = '<Jeddah123/>'

transport = paramiko.Transport((hostname, port))
transport.connect(username=username, password=password)

sftp = paramiko.SFTPClient.from_transport(transport)

for local_file in files:
    local_path = local_file['file']
    remote_path = os.path.join(local_file['target'], os.path.basename(local_path))
    sftp_upload(sftp, local_path, remote_path)

sftp.close()
transport.close()
