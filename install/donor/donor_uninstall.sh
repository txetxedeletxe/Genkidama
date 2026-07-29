#!/usr/bin/env bash

if [ "$EUID" -ne 0 ]; then
    echo "Error: Please run this script as root."
    exit 1
fi

# Stop services
echo "Stopping and disabling \"genkidama-donor\" service."
systemctl disable --now genkidama-donor.service || true

# Purge files
echo "Purging configuration and unit files."
rm -rf /opt/genkidama
rm -rf /etc/genkidama
rm -f /etc/systemd/system/genkidama-donor.service

# Remove users
echo "Removing user \"genkidama\""
userdel genkidama

# Reload Systemd
echo "Reloading systemd"
systemctl daemon-reload

# Finish
echo "Uninstall successfully complete!"

