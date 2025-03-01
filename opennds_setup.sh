#!/bin/bash

# Define versions
LIBMICROHTTPD_VERSION="0.9.71"
OPENNDS_VERSION="9.9.1"

# Function to handle cleanup
cleanup() {
    echo "Cleaning up..."
    # Remove downloaded tarballs and extracted directories
    rm -rf "libmicrohttpd-${LIBMICROHTTPD_VERSION}" "libmicrohttpd-${LIBMICROHTTPD_VERSION}.tar.gz"
    rm -rf "opennds-${OPENNDS_VERSION}" "v${OPENNDS_VERSION}"
    echo "Cleanup complete."
}

# Trap function to ensure cleanup runs on exit
trap cleanup EXIT

echo "Installing build dependencies"
if ! apt update && apt install -y build-essential php-cli; then
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
cd "libmicrohttpd-${LIBMICROHTTPD_VERSION}"

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

rm /usr/local/lib/libmicrohttpd*
make install
rm /etc/ld.so.cache
ldconfig -v
cd ..

echo ""
echo "Downloading OpenNDS"
if ! wget "https://codeload.github.com/opennds/opennds/tar.gz/v${OPENNDS_VERSION}"; then
    echo "Error downloading OpenNDS. Exiting."
    exit 1
fi
tar -xf "v${OPENNDS_VERSION}"
cd "opennds-${OPENNDS_VERSION}"

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

echo "OpenNDS installation completed successfully."
