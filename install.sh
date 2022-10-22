echo 'OJO Pisowifi install script'
echo ''
echo 'Adding sudoadmin user and group'
adduser -u 5678 --disabled-login  --gecos '' sudoadmin
echo ''
echo 'Adding sudoadmin to sudo group'
usermod -aG sudo sudoadmin
echo ''
echo 'Updating and upgrading system'
apt-get update && apt-get dist-upgrade -y
echo ''
echo 'Installing dependencies'
apt-get install build-essential libssl-dev libffi-dev python3-dev python3-venv python3-pip redis-server nginx dnsmasq gunicorn git systemd -y
echo ''
echo 'Changing directory to sudoadmin'
cd /home/sudoadmin
echo ''
echo 'Creating src directory'
mkdir src && cd src
echo ''
echo 'Creating python virtual environment'
python3 -m venv venv
echo ''
echo 'Downloading source code from github'
export GIT_SSL_NO_VERIFY=1
git clone https://github.com/ClydeAmazing/ojopisowifi.git
echo ''
echo 'Activating virtual environment'
source venv/bin/activate
echo ''
echo 'Upgrading python pip, setuptools and wheel'
pip install --upgrade pip setuptools wheel --trusted-host pypi.org --trusted-host files.pythonhosted.org
echo ''
echo 'Installing ojopisowifi app dependencies'
pip install -r ojopisowifi/requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
echo ''
echo 'Setting file permissions'
chown sudoadmin:root /home/sudoadmin/src/ojopisowifi/ && chown sudoadmin:root /home/sudoadmin/src/ojopisowifi/db.sqlite3 && chmod +x /home/sudoadmin/src/ojopisowifi/hooks.py
echo ''
echo 'Copying system files to target locations'
cp /home/sudoadmin/src/ojopisowifi/files/gunicorn.service /etc/systemd/system/gunicorn.service
cp /home/sudoadmin/src/ojopisowifi/files/hooks.service /etc/systemd/system/hooks.service
cp /home/sudoadmin/src/ojopisowifi/files/opw_init.service /etc/systemd/system/opw_init.service
cp /home/sudoadmin/src/ojopisowifi/files/opw.conf /etc/nginx/conf.d/
echo ''
echo 'Performing collecstatic command'
python /home/sudoadmin/src/ojopisowifi/manage.py collectstatic
echo ''
echo 'Deactivating Python Virtual Environment'
deactivate
echo ''
echo 'Deactivating Python Virtual Environment'
deactivate
echo ''
echo 'Backing up dnsmasq.conf'
mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
echo ''
echo 'Copying new dnsmasq config'
cp /home/sudoadmin/src/ojopisowifi/files/dnsmasq.conf /etc/dnsmasq.conf
echo ''
echo 'Backing up network interface config'
mv /etc/network/interfaces /etc/network/interfaces.orig
echo 'Copying new network interface config'
cp /home/sudoadmin/src/ojopisowifi/files/interfaces /etc/network/interfaces