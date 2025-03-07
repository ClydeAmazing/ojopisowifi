#!/bin/bash

echo 'OJO Pisowifi install script'
echo ''

# Check if user exists
if id "sudoadmin" &>/dev/null; then
    echo "User 'sudoadmin' already exists. Skipping creation."
else
    echo 'Adding sudoadmin user and group'
    adduser -u 5678 --disabled-login --gecos '' sudoadmin
fi

echo ''

# Check if user is already in sudo group
if groups sudoadmin | grep -q "\bsudo\b"; then
    echo "User 'sudoadmin' is already in the sudo group."
else
    echo 'Adding sudoadmin to sudo group'
    usermod -aG sudo sudoadmin
fi

# Restrict sudo to specific commands (Optional)
SUDOERS_FILE="/etc/sudoers.d/sudoadmin"
ALLOWED_COMMANDS="/usr/bin/ndsctl"

if [[ -f "$SUDOERS_FILE" ]] && grep -Fxq "sudoadmin ALL=(root) NOPASSWD: $ALLOWED_COMMANDS" "$SUDOERS_FILE"; then
    echo "Sudoers file is already configured."
else
    echo "sudoadmin ALL=(root) NOPASSWD: $ALLOWED_COMMANDS" > "$SUDOERS_FILE"
    chmod 0440 "$SUDOERS_FILE"
    echo "Restricted sudo access for 'sudoadmin'."
fi

echo ''
echo "Setup complete. 'sudoadmin' can now run:"
echo "$ALLOWED_COMMANDS"

echo ''
echo 'Updating and upgrading system'
apt-get update && apt-get dist-upgrade -y

echo ''
echo 'Installing dependencies'
apt-get install build-essential libssl-dev libffi-dev python3-dev python3-venv python3-pip nginx gunicorn git systemd redis-server -y

echo ''
echo 'Creating src directory'
mkdir -p /home/sudoadmin/src

echo ''
echo 'Creating python virtual environment'
python3 -m venv /home/sudoadmin/src/venv

echo ''
echo 'Downloading/updating source code from github'
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

echo ''
echo 'Updating directory permissions'
sudo chmod 755 /home/sudoadmin
sudo chmod 755 /home/sudoadmin/src
sudo chown -R sudoadmin:www-data /home/sudoadmin/src/ojopisowifi/
sudo chown sudoadmin:www-data /home/sudoadmin/src/ojopisowifi/db.sqlite3
chmod +x /home/sudoadmin/src/ojopisowifi/hooks.py
chmod +x /home/sudoadmin/src/ojopisowifi/sweep.py

echo ''
echo 'Copying system files to target locations'
cp -f /home/sudoadmin/src/ojopisowifi/files/gunicorn.service /etc/systemd/system/gunicorn.service
cp -f /home/sudoadmin/src/ojopisowifi/files/celery.service /etc/systemd/system/celery.service
cp -f /home/sudoadmin/src/ojopisowifi/files/hooks.service /etc/systemd/system/hooks.service
cp -f /home/sudoadmin/src/ojopisowifi/files/opw_init.service /etc/systemd/system/opw_init.service
cp -f /home/sudoadmin/src/ojopisowifi/files/sweep.service /etc/systemd/system/sweep.service

echo ''
echo 'Configuring NGINX'
rm -f /etc/nginx/sites-enabled/default
cp -f /home/sudoadmin/src/ojopisowifi/files/opw /etc/nginx/sites-available/
ln -sf /etc/nginx/sites-available/opw /etc/nginx/sites-enabled/

echo ''
echo 'Reloading systemd daemon'
systemctl daemon-reload

echo ''
echo 'Enabling and force restarting services'
for service in redis-server gunicorn celery hooks opw_init sweep; do
    systemctl enable "$service".service
    systemctl restart "$service".service
done

echo ''
echo 'Performing collecstatic command'
python /home/sudoadmin/src/ojopisowifi/manage.py collectstatic --no-input > /dev/null

echo ''
echo 'Deactivating Python Virtual Environment'
deactivate

echo ''
echo 'Restarting nginx server'
systemctl restart nginx.service

echo ''
echo 'Installation/update complete!'
