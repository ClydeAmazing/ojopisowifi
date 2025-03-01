#!/bin/bash

echo "Installing dependencies..."

# Check if iptables is installed
# Note: Added openvswitch-switch-dpdk to fix the netplan apply warning
apt update && apt install -y iptables iptables-persistent openvswitch-switch-dpdk dnsmasq

# Detect available network interfaces
echo "Detecting available network interfaces..."
interfaces=$(ip -o link show | awk -F': ' '{print $2}' | grep -v lo)

# Print available interfaces
echo "Available interfaces:"
counter=1
for iface in $interfaces; do
    echo "$counter) $iface"
    counter=$((counter + 1))
done

# Function to check if the input is a valid interface
is_valid_interface() {
    local interface=$1
    if echo "$interfaces" | grep -wq "$interface"; then
        return 0  # valid interface
    else
        return 1  # invalid interface
    fi
}

# Prompt the user to select the WAN interface
while true; do
    read -p "Enter the number for the WAN (internet) interface: " wan_choice
    wan_iface=$(echo "$interfaces" | sed -n "${wan_choice}p")
    
    if is_valid_interface "$wan_iface"; then
        echo "Selected WAN interface: $wan_iface"
        break
    else
        echo "Invalid choice. Please select a valid WAN interface."
    fi
done

# Prompt the user to select the LAN interface
while true; do
    read -p "Enter the number for the LAN (local network) interface: " lan_choice
    lan_iface=$(echo "$interfaces" | sed -n "${lan_choice}p")

    if [[ "$lan_iface" == "$wan_iface" ]]; then
        echo "LAN and WAN interfaces cannot be the same. Please select a different LAN interface."
        continue
    fi

    if is_valid_interface "$lan_iface"; then
        echo "Selected LAN interface: $lan_iface"
        break
    else
        echo "Invalid choice. Please select a valid LAN interface."
    fi
done

# Ensure iptables is in PATH
export PATH=$PATH:/sbin:/usr/sbin

# Set up IP forwarding and NAT
echo "Setting up IP forwarding and NAT..."

# Configure ipv4 forwarding
sed -i 's/^#net.ipv4.ip_forward=.*/net.ipv4.ip_forward=1/' /etc/sysctl.conf

# Ensure that the lines are uncommented correctly
if ! grep -q "net.ipv4.ip_forward=1" /etc/sysctl.conf; then
    echo "ERROR: Could not configure net.ipv4.ip_forward=1 in /etc/sysctl.conf"
    exit 1
fi

# Apply forwarding immediately
sysctl -w net.ipv4.ip_forward=1
sysctl -p

iptables -t nat -A POSTROUTING -o $wan_iface -j MASQUERADE
iptables -A FORWARD -i $wan_iface -o $lan_iface -m state --state RELATED,ESTABLISHED -j ACCEPT
iptables -A FORWARD -i $lan_iface -o $wan_iface -j ACCEPT

# Ensure the directory exists before saving rules
mkdir -p /etc/iptables

# Save iptables rules
iptables-save > /etc/iptables/rules.v4

# Configure /etc/default/dnsmasq to ignore resolvconf and exclude loopback
echo "Configuring /etc/default/dnsmasq..."
sed -i 's/^#IGNORE_RESOLVCONF=.*/IGNORE_RESOLVCONF=yes/' /etc/default/dnsmasq
sed -i 's/^#DNSMASQ_EXCEPT=.*/DNSMASQ_EXCEPT="lo"/' /etc/default/dnsmasq

# Ensure that the lines are uncommented correctly
if ! grep -q "IGNORE_RESOLVCONF=yes" /etc/default/dnsmasq; then
    echo "ERROR: Could not configure IGNORE_RESOLVCONF in /etc/default/dnsmasq"
    exit 1
fi

if ! grep -q 'DNSMASQ_EXCEPT="lo"' /etc/default/dnsmasq; then
    echo "ERROR: Could not configure DNSMASQ_EXCEPT in /etc/default/dnsmasq"
    exit 1
fi

echo "Successfully configured /etc/default/dnsmasq"

# Set up DHCP using dnsmasq
echo "Setting up dnsmasq for DHCP on LAN interface..."
cat > /etc/dnsmasq.conf << EOF
interface=$lan_iface
bind-interfaces
no-resolv
dhcp-range=192.168.1.50,192.168.1.150,12h
server=8.8.8.8
server=1.1.1.1
EOF

# Restart dnsmasq to apply the changes
systemctl restart dnsmasq

echo "Setting up network interfaces"
# Backup the default netplan configuration
mv /etc/netplan/10-dhcp-all-interfaces.yaml /etc/netplan/10-dhcp-all-interfaces.yaml.orig

# Configure the interfaces
cat > /etc/netplan/20-ojo-interfaces.yaml << EOF
network:
  version: 2
  renderer: networkd
  ethernets:
    $wan_iface:
      dhcp4: yes
      dhcp6: yes
      ipv6-privacy: yes
    $lan_iface:
      addresses:
        - 192.168.1.1/24
      nameservers:
        addresses:
          - 8.8.8.8
          - 1.1.1.1
      dhcp4: no
EOF

# According to the Netplan docs, the permissions must be restricted to the root user.
sudo chmod 600 /etc/netplan/*.yaml

# Apply netplan configuration
netplan apply

# Restart networking service to apply changes
systemctl restart systemd-networkd

echo "Router setup complete. Please reboot the device for changes to take full effect."

read -p "Reboot now? (y/n): " choice
if [[ "$choice" =~ ^[Yy]$ ]]; then
    reboot
fi