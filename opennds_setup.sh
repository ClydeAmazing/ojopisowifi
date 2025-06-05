#!/bin/bash

set -e

# Define versions
LIBMICROHTTPD_VERSION="0.9.71"
OPENNDS_VERSION="10.3.1"

# Create a temporary working directory
WORKDIR="$(mktemp -d)"
cd "$WORKDIR" || exit 1

# Function to handle cleanup
cleanup() {
    echo "Cleaning up..."
    rm -rf "$WORKDIR"
    echo "Cleanup complete."
}

# Trap to ensure cleanup runs on exit
trap cleanup EXIT

echo "Installing build dependencies"
if ! apt update || ! apt install -y build-essential php-cli wget tar gcc make pkg-config ; then
    echo "Error installing build dependencies. Exiting."
    exit 1
fi

echo ""
echo "Downloading opennds dependency (libmicrohttpd)"
if ! wget "https://ftp.gnu.org/gnu/libmicrohttpd/libmicrohttpd-${LIBMICROHTTPD_VERSION}.tar.gz"; then
    echo "Error downloading libmicrohttpd. Exiting."
    exit 1
fi

tar -xf "libmicrohttpd-${LIBMICROHTTPD_VERSION}.tar.gz"
cd "libmicrohttpd-${LIBMICROHTTPD_VERSION}" || exit 1

echo ""
echo "Building libmicrohttpd"
if ! ./configure --disable-https; then
    echo "Error configuring libmicrohttpd. Exiting."
    exit 1
fi

if ! make; then
    echo "Error building libmicrohttpd. Exiting."
    exit 1
fi

rm -f /usr/local/lib/libmicrohttpd*
make install
ldconfig

cd "$WORKDIR" || exit 1

echo ""
echo "Downloading OpenNDS"
if ! wget "https://codeload.github.com/opennds/opennds/tar.gz/v${OPENNDS_VERSION}"; then
    echo "Error downloading OpenNDS. Exiting."
    exit 1
fi

tar -xf "v${OPENNDS_VERSION}"
cd "opennds-${OPENNDS_VERSION}" || exit 1

echo ""
echo "Building OpenNDS"
if ! make; then
    echo "Error building OpenNDS. Exiting."
    exit 1
fi

make install

systemctl enable opennds
echo "Starting OpenNDS"
if ! systemctl start opennds; then
    echo "Error starting OpenNDS. Exiting."
    exit 1
fi

echo "✅ OpenNDS installation completed successfully."
