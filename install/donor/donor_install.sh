#!/usr/bin/env bash
set -e # Exit immediately if a command fails

if [ "$EUID" -ne 0 ]; then
    echo "Error: Please run this script as root."
    exit 1
fi

echo "Starting installation of genkidama donor service..."

# Variables
## User # TODO make these modifiable via env variables
GENKIDAMA_USER="genkidama"

## Directories # TODO make these modifiable via env variables
SYSTEMD_PATH="/etc/systemd/system"
INSTALL_PATH="/opt/genkidama"
CONFIG_PATH="/etc/genkidama"

CERTS_PATH="$CONFIG_PATH/certs"
ENVIRONMENT_PATH="$INSTALL_PATH/env"

## Filenames
CONFIG_FILENAME="donor.conf"
SERVICE_FILENAME="genkidama-donor.service"
UNINSTALL_SCRIPT_FILENAME="donor_uninstall.sh"

## Files
CONFIG_FILE="$CONFIG_PATH/$CONFIG_FILENAME"
SERVICE_FILE="$SYSTEMD_PATH/$SERVICE_FILENAME"
UNINSTALL_SCRIPT_FILE="$INSTALL_PATH/$UNINSTALL_SCRIPT_FILENAME"

PYTHON_EXECUTABLE="$ENVIRONMENT_PATH/bin/python3"
GENKIDAMA_EXECUTABLE="$ENVIRONMENT_PATH/bin/genkidama"


## Local stuff
LOCAL_DIRECTORY=$(dirname "$0")

CONFIG_FILE_TEMPLATE="$LOCAL_DIRECTORY/$CONFIG_FILENAME.template"
SERVICE_FILE_TEMPLATE="$LOCAL_DIRECTORY/$SERVICE_FILENAME.template"
UNINSTALL_SCRIPT_FILE_TEMPLATE="$LOCAL_DIRECTORY/$UNINSTALL_SCRIPT_FILENAME.template"

# Check system environment
echo "Checking system environment..."

## python
SYSTEM_PYTHON_EXECUTABLE=$(which /usr/bin/python3 || which /bin/python3)
if [ -z "$SYSTEM_PYTHON_EXECUTABLE" ]; then
    echo "Error: \"python3\" command not found. Genkidama needs a systemwide python with version >= 3.13"
    exit 1
fi

SYSTEM_PYTHON_VERSION=$($SYSTEM_PYTHON_EXECUTABLE -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if (( $(echo "$SYSTEM_PYTHON_VERSION < 3.13" | bc -l) )); then
    echo "Error: Python 3.13 or higher is required. Found $SYSTEM_PYTHON_VERSION."
    exit 1
fi

## virtualenv
if ! $SYSTEM_PYTHON_EXECUTABLE -m venv -h &>/dev/null; then
    echo "Error: \"venv\" python module not found on systemwide python installation. Genkidama needs a systemwide virtualenv package installed. See https://virtualenv.pypa.io/en/latest/."
    exit 1
fi

echo "System environment checked: The system satisfies the installation requirements!"

# Make genkidama user
echo "Creating a system user for Genkidama: \"$GENKIDAMA_USER\"."

if ! id "$GENKIDAMA_USER" &>/dev/null; then
    useradd --system --no-create-home --shell /usr/sbin/nologin $GENKIDAMA_USER
    echo "User \"$GENKIDAMA_USER\" created."
else
    echo "User \"$GENKIDAMA_USER\" already exists. Change \"GENKIDAMA_USER\" variable in instal script or remove \"$GENKIDAMA_USER\" user from system."
    exit 2
fi

# Populate templates
TMP_CONFIG_FILE=$(mktemp)
TMP_SERVICE_FILE=$(mktemp)
TMP_UNINSTALL_SCRIPT_FILE=$(mktemp)

export GENKIDAMA_USER INSTALL_PATH CONFIG_PATH CERTS_PATH ENVIRONMENT_PATH CONFIG_FILE SERVICE_FILE PYTHON_EXECUTABLE GENKIDAMA_EXECUTABLE
envsubst < "$CONFIG_FILE_TEMPLATE" >  "$TMP_CONFIG_FILE"
envsubst < "$SERVICE_FILE_TEMPLATE" > "$TMP_SERVICE_FILE"
EUID="\$EUID" envsubst < "$UNINSTALL_SCRIPT_FILE_TEMPLATE" > "$TMP_UNINSTALL_SCRIPT_FILE"


# Create Directories
echo "Creating directories."
mkdir -p "$SYSTEMD_PATH" "$INSTALL_PATH" "$CONFIG_PATH" "$CERTS_PATH" "$ENVIRONMENT_PATH"

# Create Virtualenv and install genkidama
echo "Installing genkidama in a virtual environment."
$SYSTEM_PYTHON_EXECUTABLE -m venv "$ENVIRONMENT_PATH"
$PYTHON_EXECUTABLE -m pip install genkidama

# Install Config Files
echo "Installing configuration files."

cp "$TMP_CONFIG_FILE" "$CONFIG_FILE"
cp "$TMP_CONFIG_FILE" "$CONFIG_FILE.default" # Make a default copy

chown root:root "$CONFIG_FILE"
chown root:root "$CONFIG_FILE.default"
chmod 644 "$CONFIG_FILE"
chmod 644 "$CONFIG_FILE.default"

cp "$TMP_SERVICE_FILE" "$SERVICE_FILE"

chown root:root "$SERVICE_FILE"
chmod 644 "$SERVICE_FILE"

# Copy uninstall script
echo "Copying $UNINSTALL_SCRIPT_FILENAME."
cp "$TMP_UNINSTALL_SCRIPT_FILE" "$UNINSTALL_SCRIPT_FILE"

chown root:root "$UNINSTALL_SCRIPT_FILE"
chmod +x "$UNINSTALL_SCRIPT_FILE"


# Reload systemd
echo "Reloading systemctl daemon register."
systemctl daemon-reload

# Finish
echo "Finishing up: Cleaning."
rm -f "$TMP_CONFIG_FILE" "$TMP_SERVICE_FILE" "$TMP_UNINSTALL_SCRIPT_FILE"

echo "Installation of genkidama donor service completed successfully!"
echo "To activate the donor daemon, start/enable the \"genkidama-donor.service\" unit."













