#!/bin/bash
#Copyright (C) BlueWave Projects and Services 2015-2022
#This software is released under the GNU GPL license.
#
status=$1
clientip=$2
b64query=$3

do_ndsctl () {
	local timeout=4

	for tic in $(seq $timeout); do
		ndsstatus="ready"
		ndsctlout=$(eval ndsctl "$ndsctlcmd")

		for keyword in $ndsctlout; do

			if [ $keyword = "locked" ]; then
				ndsstatus="busy"
				sleep 1
				break
			fi
		done

		if [ "$ndsstatus" = "ready" ]; then
			break
		fi
	done
}

get_client_zone () {
	# Gets the client zone, (if we don't already have it) ie the connection the client is using, such as:
	# local interface (br-lan, wlan0, wlan0-1 etc.,
	# or remote mesh node mac address

	failcheck=$(echo "$clientif" | grep "get_client_interface")

	if [ -z $failcheck ]; then
		client_if=$(echo "$clientif" | awk '{printf $1}')
		client_meshnode=$(echo "$clientif" | awk '{printf $2}' | awk -F ':' '{print $1$2$3$4$5$6}')
		local_mesh_if=$(echo "$clientif" | awk '{printf $3}')

		if [ ! -z "$client_meshnode" ]; then
			client_zone="MeshZone: $client_meshnode"
		else
			client_zone="LocalZone: $client_if"
		fi
	else
		client_zone=""
	fi
}

htmlentityencode() {
	entitylist="
		s/\"/\&quot;/g
		s/>/\&gt;/g
		s/</\&lt;/g
		s/%/\&#37;/g
		s/'/\&#39;/g
		s/\`/\&#96;/g
	"
	local buffer="$1"

	for entity in $entitylist; do
		entityencoded=$(echo "$buffer" | sed "$entity")
		buffer=$entityencoded
	done

	entityencoded=$(echo "$buffer" | awk '{ gsub(/\$/, "\\&#36;"); print }')
}


parse_variables() {
	# Parse for variables in $query from the list in $queryvarlist:

	for var in $queryvarlist; do
		evalstr=$(echo "$query" | awk -F"$var=" '{print $2}' | awk -F', ' '{print $1}')
		evalstr=$(printf "${evalstr//%/\\x}")

		# sanitise $evalstr to prevent code injection
		htmlentityencode "$evalstr"
		evalstr=$entityencoded

		if [ -z "$evalstr" ]; then
			continue
		fi

		eval $var=$(echo "\"$evalstr\"")
		evalstr=""
	done
	query=""
}

parse_parameters() {
	ndsctlcmd="json $clientip"

	do_ndsctl

	if [ "$ndsstatus" = "ready" ]; then
		param_str=$ndsctlout

		for param in gatewayname gatewayaddress gatewayfqdn mac version ip client_type clientif session_start session_end \
			last_active token state upload_rate_limit_threshold download_rate_limit_threshold \
			upload_packet_rate upload_bucket_size download_packet_rate download_bucket_size \
			upload_quota download_quota upload_this_session download_this_session upload_session_avg download_session_avg
		do
			val=$(echo "$param_str" | grep "\"$param\":" | awk -F'"' '{printf "%s", $4}')

			if [ "$val" = "null" ]; then
				val="Unlimited"
			fi

			if [ -z "$val" ]; then
				eval $param=$(echo "Unavailable")
			else
				eval $param=$(echo "\"$val\"")
			fi
		done

		# url decode and html entity encode gatewayname
		gatewayname_dec=$(printf "${gatewayname//%/\\x}")
		htmlentityencode "$gatewayname_dec"
		gatewaynamehtml=$entityencoded

		# Get client_zone from clientif
		get_client_zone

		# Get human readable times:
		sessionstart=$(date -d @$session_start)

		if [ "$session_end" = "Unlimited" ]; then
			sessionend=$session_end
		else
			sessionend=$(date -d @$session_end)
		fi

		lastactive=$(date -d @$last_active)
	fi
}

header() {
# Define a common header html for every page served
	header="<!DOCTYPE html>
		<html>
		<head>
		<meta http-equiv=\"Cache-Control\" content=\"no-cache, no-store, must-revalidate\">
		<meta http-equiv=\"Pragma\" content=\"no-cache\">
		<meta http-equiv=\"Expires\" content=\"0\">
		<meta charset=\"utf-8\">
		<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
		<link rel=\"shortcut icon\" href=\"$url/images/splash.jpg\" type=\"image/x-icon\">
		<title>WiFi Status</title>
		</head>
		<body>
		<div class=\"offset\">
		<div class=\"insert\" style=\"max-width:100%; font-family: sans-serif;\">
	"
	echo "$header"
}

header_redirect() {
# Define a common header html for every page served
	if [ "$mac" = "Unavailable" ]; then
		payload=""
		redir_msg="Unable to fetch client info. Please disconnect and reconnect to wifi."
	else
		payload="<meta http-equiv=\"Refresh\" content=\"1; url='http://10.0.0.1:8000/?referrer=$mac'\" />"
		redir_msg="Redirecting to portal..."
	fi
	
	header="<!DOCTYPE html>
		<html>
		<head>
		<meta http-equiv=\"Cache-Control\" content=\"no-cache, no-store, must-revalidate\">
		<meta http-equiv=\"Pragma\" content=\"no-cache\">
		<meta http-equiv=\"Expires\" content=\"0\">
		<meta charset=\"utf-8\">
		<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
		$payload
		<title>WiFi Status</title>
		</head>
		<body>
		<div class=\"offset\">
		<div class=\"insert\" style=\"max-width:100%; font-family: sans-serif;\">
		$redir_msg
		<br>
	"
	echo "$header"
}

footer() {
	# Define a common footer html for every page served
	year=$(date +'%Y')
	echo "
		</div>
		</div>
		</body>
		</html>
	"
}

body() {
	if [ "$ndsstatus" = "busy" ]; then
		header
		echo "
			<hr>
			<b>The Portal is busy, please click or tap \"Refresh\"<br><br></b>
			<form>
				<input type=\"button\" VALUE=\"Refresh\" onClick=\"history.go(0);return true;\">
			</form>
		"
		footer
	elif [ "$status" = "status" ]; then
		header_redirect
		footer
	elif [ "$status" = "err511" ]; then
		header
		echo "
			<p>Authentication Required</p>
			<form action=\"$url/login\" method=\"get\" target=\"_blank\">
			<input type=\"submit\" value=\"Portal Login\" >
			</form>
			<br>
			<form action=\"$url\" method=\"get\">
			<input type=\"submit\" value=\"Refresh\">
			</form>
		"
		footer
	else
		exit 1
	fi
}

# Start generating the html:
if [ -z "$clientip" ]; then
	exit 1
fi

if [ "$status" = "status" ] || [ "$status" = "err511" ]; then
	parse_parameters

	if [ -z "$gatewayfqdn" ] || [ "$gatewayfqdn" = "disable" ] || [ "$gatewayfqdn" = "disabled" ]; then
		url="http://$gatewayaddress"
	else
		url="http://$gatewayfqdn"
	fi

	querystr=""

	if [ ! -z "$b64query" ]; then
		ndsctlcmd="b64decode $b64query"
		do_ndsctl
		querystr=$ndsctlout	

		# strip off leading "?" character
		querystr=${querystr:1:1024}
		queryvarlist=""

		for element in $querystr; do
			htmlentityencode "$element"
			element=$entityencoded
			varname=$(echo "$element" | awk -F'=' '$2!="" {printf "%s", $1}')
			queryvarlist="$queryvarlist $varname"
		done

		query=$querystr
		parse_variables
	fi

	# header
	body
	# footer
else
	exit 1
fi
