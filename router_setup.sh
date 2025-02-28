#!/bin/bash

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

# Ensure iptables is installed
if ! command -v iptables &> /dev/null; then
    echo "iptables not found. Installing..."
    apt update && apt install iptables -y
fi

# Ensure iptables is in PATH
export PATH=$PATH:/sbin:/usr/sbin

# Set up IP forwarding and NAT
echo "Setting up IP forwarding and NAT..."
sysctl -w net.ipv4.ip_forward=1
iptables -t nat -A POSTROUTING -o $wan_iface -j MASQUERADE
iptables -A FORWARD -i $wan_iface -o $lan_iface -m state --state RELATED,ESTABLISHED -j ACCEPT
iptables -A FORWARD -i $lan_iface -o $wan_iface -j ACCEPT

# Save iptables rules
iptables-save > /etc/iptables/rules.v4

# Set up DHCP using dnsmasq
echo "Setting up dnsmasq for DHCP on LAN interface..."
cat > /etc/dnsmasq.conf << EOF
interface=$lan_iface
dhcp-range=192.168.1.50,192.168.1.150,12h
server=8.8.8.8
server=1.1.1.1
EOF

# Restart dnsmasq to apply the changes
systemctl restart dnsmasq

# Configure the LAN interface with a static IP
echo "Configuring LAN interface with static IP..."
cat >> /etc/network/interfaces << EOF
auto $lan_iface
iface $lan_iface inet static
address 192.168.1.1
netmask 255.255.255.0
EOF

# Restart networking service to apply changes
systemctl restart networking

echo "Router setup complete. Please reboot the device for changes to take full effect."
