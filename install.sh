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
apt-get install build-essential libssl-dev libffi-dev python3-dev python3-venv python3-pip nginx dnsmasq gunicorn git systemd -y
echo ''
echo 'Creating src directory'
mkdir /home/sudoadmin/src
echo ''
echo 'Creating python virtual environment'
python3 -m venv /home/sudoadmin/src/venv
echo ''
echo 'Downloading source code from github'
export GIT_SSL_NO_VERIFY=1
git clone https://github.com/ClydeAmazing/ojopisowifi.git /home/sudoadmin/src/ojopisowifi/
echo ''
echo 'Activating virtual environment'
source /home/sudoadmin/src/venv/bin/activate
echo ''
echo 'Upgrading python pip, setuptools and wheel'
pip install --upgrade pip setuptools wheel --trusted-host pypi.org --trusted-host files.pythonhosted.org
echo ''
echo 'Installing ojopisowifi app dependencies'
pip install -r <(grep -v cryptography /home/sudoadmin/src/ojopisowifi/requirements.txt) --trusted-host pypi.org --trusted-host files.pythonhosted.org
echo ''
echo 'Installing cryptography package'
pip install cryptography --index-url=https://www.piwheels.org/simple
echo  ''
echo 'Setting file permissions'
chown sudoadmin:root /home/sudoadmin/src/ojopisowifi/ 
chown sudoadmin:root /home/sudoadmin/src/ojopisowifi/db.sqlite3 
chmod +x /home/sudoadmin/src/ojopisowifi/hooks.py
chmod +x /home/sudoadmin/src/ojopisowifi/sweep.py
echo ''
echo 'Copying system files to target locations'
cp /home/sudoadmin/src/ojopisowifi/files/gunicorn.service /etc/systemd/system/gunicorn.service
cp /home/sudoadmin/src/ojopisowifi/files/hooks.service /etc/systemd/system/hooks.service
cp /home/sudoadmin/src/ojopisowifi/files/opw_init.service /etc/systemd/system/opw_init.service
cp /home/sudoadmin/src/ojopisowifi/files/sweep.service /etc/systemd/system/sweep.service
echo ''
echo 'Removing default nginx profile'
rm /etc/nginx/sites-enabled/default
echo ''
echo 'Setting up new ojo nginx profile'
cp /home/sudoadmin/src/ojopisowifi/files/opw /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/opw /etc/nginx/sites-enabled/
echo ''
echo 'Updating root directory permissions'
sudo chmod 755 /home/sudoadmin
sudo chmod 755 /home/sudoadmin/src
echo ''
echo 'Reloading daemon files'
systemctl daemon-reload
echo ''
echo 'Enabling gunicorn service'
systemctl enable gunicorn.service
echo ''
echo 'Enabling hooks service'
systemctl enable hooks.service
echo ''
echo 'Enabling opw_init service'
systemctl enable opw_init.service
echo ''
echo 'Starting services'
systemctl start gunicorn.service
systemctl start hooks.service
systemctl start opw_init.service
systemctl start sweep.service
echo ''
echo 'Performing collecstatic command'
python /home/sudoadmin/src/ojopisowifi/manage.py collectstatic --no-input > /dev/null
echo ''
echo 'Deactivating Python Virtual Environment'
deactivate
echo ''
echo 'Restarting nginx server'
systemctl restart nginx.service
# echo 'Backing up dnsmasq.conf'
# mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
# echo ''
# echo 'Copying new dnsmasq config'
# cp /home/sudoadmin/src/ojopisowifi/files/dnsmasq.conf /etc/dnsmasq.conf
# echo ''
# echo 'Backing up network interface config'
# mv /etc/network/interfaces /etc/network/interfaces.orig
# echo 'Copying new network interface config'
# cp /home/sudoadmin/src/ojopisowifi/files/interfaces /etc/network/interfaces
