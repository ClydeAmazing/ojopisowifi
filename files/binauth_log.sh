#!/bin/bash
#Copyright (C) The openNDS Contributors 2004-2021
#Copyright (C) BlueWave Projects and Services 2015-2021
#This software is released under the GNU GPL license.

# This is an example script for BinAuth
# It writes a local log and can override authentication requests and quotas.
#
# The client User Agent string is forwarded to this script.
#
# If BinAuth is enabled, NDS will call this script as soon as it has received an authentication, deauthentication or shutdown request
#

##################
# functions:

get_client_zone () {
	# Gets the client zone, (if we don't already have it) ie the connection the client is using, such as:
	# local interface (br-lan, wlan0, wlan0-1 etc.,
	# or remote mesh node mac address
	# This zone name is only displayed here but could be used to customise the login form for each zone

	if [ -z "$client_zone" ]; then
		client_mac=$clientmac
		client_if_string=$(/usr/lib/opennds/get_client_interface.sh $client_mac)
		failcheck=$(echo "$client_if_string" | grep "get_client_interface")

		if [ -z $failcheck ]; then
			client_if=$(echo "$client_if_string" | awk '{printf $1}')
			client_meshnode=$(echo "$client_if_string" | awk '{printf $2}' | awk -F ':' '{print $1$2$3$4$5$6}')
			local_mesh_if=$(echo "$client_if_string" | awk '{printf $3}')

			if [ ! -z "$client_meshnode" ]; then
				client_zone="MeshZone:$client_meshnode LocalInterface:$local_mesh_if"
			else
				client_zone="LocalZone:$client_if"
			fi
		else
			client_zone=""
		fi
	else
		client_zone=$(printf "${client_zone//%/\\x}")
	fi
}

#### end of functions ####


#########################################
#					#
#  Start - Main entry point		#
#					#
#  This script starts executing here	#
#					#
#					#
#########################################

action=$1

if [ $action = "auth_client" ]; then
	# Arguments passed are as follows
	# $1 method
	# $2 client mac
	# $3 legacy1 (previously username)
	# $4 legacy2 (previously password)
	# $5 originurl (redir)
	# $6 client useragent
	# $7 client ip
	# $8 client token
	# $9 custom data string

	# redir, useragent and customdata are url-encoded, so decode:
	redir_enc=$5
	redir=$(printf "${redir_enc//%/\\x}")
	useragent_enc=$6
	useragent=$(printf "${useragent_enc//%/\\x}")
	customdata_enc=$9
	customdata=$(printf "${customdata_enc//%/\\x}")

elif [ $action = "ndsctl_auth" ]; then
	# Arguments passed are as follows
	# $1 method
	# $2 client mac
	# $3 bytes incoming
	# $4 bytes outgoing
	# $5 session start time
	# $6 session end time
	# $7 client token
	# $8 custom data string

	customdata_enc=$8
	customdata=$(printf "${customdata_enc//%/\\x}")
	log_entry="method=$1, clientmac=$2, bytes_incoming=$3, bytes_outgoing=$4, session_start=$5, session_end=$6, token=$7, custom=$customdata_enc"

else
	# All other methods
	# Arguments passed are as follows
	# $1 method
	# $2 client mac
	# $3 bytes incoming
	# $4 bytes outgoing
	# $5 session start time
	# $6 session end time
	# $7 client token

	log_entry="method=$1, clientmac=$2, bytes_incoming=$3, bytes_outgoing=$4, session_start=$5, session_end=$6, token=$7"
fi

#Quotas and session length set elsewhere can be overridden here if action=auth_client, otherwise will be ignored.
# Set length of session in seconds (eg 24 hours is 86400 seconds - if set to 0 then defaults to global or FAS sessiontimeout value):
session_length=0

# Set Rate and Quota values for the client
# The session length, rate and quota values are determined globaly or by FAS/PreAuth on a per client basis.
# rates are in kb/s, quotas are in kB. Setting to 0 means no limit
upload_rate=0
download_rate=0
upload_quota=0
download_quota=0

# Finally before exiting, output the session length, upload rate, download rate, upload quota and download quota (only effective for auth_client).

echo "$session_length $upload_rate $download_rate $upload_quota $download_quota"

# Exit, setting level (only effective for auth_client)
#
# exit 0 tells NDS it is ok to allow the client to have access.
# exit 1 would tell NDS to deny access.
exit 0
