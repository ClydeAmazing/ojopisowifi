#!/bin/bash

# Define versions
LIBMICROHTTPD_VERSION="0.9.71"
OPENNDS_VERSION="9.10.0"
echo "Installing build dependencies"
apt update && apt install -y build-essential
echo ""
echo "Downloading opennds dependency (libmicrohttpd)"
wget "https://ftp.gnu.org/gnu/libmicrohttpd/libmicrohttpd-${LIBMICROHTTPD_VERSION}.tar.gz"
tar -xf "libmicrohttpd-${LIBMICROHTTPD_VERSION}.tar.gz"
cd "libmicrohttpd-${LIBMICROHTTPD_VERSION}"
echo ""
echo "Building libmicrohttpd"
./configure --disable-https
make
rm /usr/local/lib/libmicrohttpd*
make install
rm /etc/ld.so.cache
ldconfig -v
cd ..
echo ""
echo "Downloading OpenNDS"
wget "https://codeload.github.com/opennds/opennds/tar.gz/v${OPENNDS_VERSION}"
tar -xf "v${OPENNDS_VERSION}"
cd "openNDS-${OPENNDS_VERSION}"
echo ""
echo "Building OpenNDS"
make
make install
systemctl enable opennds
