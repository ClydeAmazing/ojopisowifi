#!/bin/bash

# Ensure the script is run as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root: sudo bash network_interface_setup.sh"
    exit 1
fi

# Check if predictable network interface names are already disabled
if grep -q "extraargs=net.ifnames=0 biosdevname=0" /boot/armbianEnv.txt; then
    echo "Predictable network interface names already disabled. Skipping."
    exit 0
fi

# Disable Predictable Network Interface Names
echo "Disabling Predictable Network Interface Names..."
echo "extraargs=net.ifnames=0 biosdevname=0" >> /boot/armbianEnv.txt

# Update initramfs to apply the changes
echo "Updating initramfs..."
update-initramfs -u

# Reboot the system to apply the changes
echo "Rebooting system to apply changes..."
sudo reboot
exit 0
