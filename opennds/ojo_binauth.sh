#!/bin/sh

# Define API endpoint URL
# API_URL="http://localhost:8000/app/api/create_user/"
API_URL="http://192.168.8.168:8000/app/api/create_user/"  # Replace this with the actual API endpoint URL
# ENCRYPTION_KEY="YourEncryptionKey"
API_TOKEN="3a3ab3815478ca093c50a3b4a59ad80086bd2772"
TIMEOUT_SECONDS=5

session_length=0
action=$1

# Check if the first argument is "auth_client" or "ndsctl_auth"
if [ $action = "auth_client" ]; then
    # Construct the JSON data for auth_client
    JSON_DATA=$(cat <<-EOF
    {
        "method": "$1",
        "client_mac": "$2",
        "username": "$3",
        "password": "$4",
        "redir": "$5",
        "user_agent": "$6",
        "client_ip": "$7",
        "client_token": "$8",
        "custom_variable": "$9"
    }
EOF
    )
elif [ $action == "ndsctl_auth" ]; then
    # Construct the JSON data for ndsctl_auth
    JSON_DATA=$(cat <<-EOF
    {
        "method": "$1",
        "client_mac": "$2",
        "bytes_incoming": "$3",
        "bytes_outgoing": "$4",
        "session_start": "$5",
        "session_end": "$6",
        "client_token": "$7",
        "custom_variable": "$8"
    }
EOF
    )
else
    # Construct the JSON data for other methods
    JSON_DATA=$(cat <<-EOF
    {
        "method": "$1",
        "client_mac": "$2",
        "bytes_incoming": "$3",
        "bytes_outgoing": "$4",
        "session_start": "$5",
        "session_end": "$6",
        "client_token": "$7"
    }
EOF
    )
fi

# Encrypt the JSON data with AES-256-CBC encryption using openssl
# ENCRYPTED_DATA=$(echo -n "$JSON_DATA" | openssl enc -aes-256-cbc -a -pbkdf2 -k "$ENCRYPTION_KEY")

# Send the HTTP POST request and capture the API response
API_RESPONSE=$(curl -s -X POST -w "\n%{http_code}" "${API_URL}" \
    -H "Content-Type: application/json" \
    -H "Authorization: Token $API_TOKEN" \
    -d "${JSON_DATA}" \API_TOKEN
    -m $TIMEOUT_SECONDS)

# Extract the HTTP status code and API response from the captured data
HTTP_STATUS=$(echo "$API_RESPONSE" | tail -n 1)
API_RESPONSE=$(echo "$API_RESPONSE" | head -n -1)

# Check the method and HTTP status code, then exit the script accordingly
if [ $action = "auth_client" ]; then
    if  [ "$HTTP_STATUS" -eq 200 ]; then
        # Parse the API response to extract the session_length value
        session_length=$(echo "$API_RESPONSE" | sed -n 's/.*"session_length":\([0-9]*\).*/\1/p')

        # echo $JSON_DATA
        # echo "auth_client request with 0"
        echo $session_length 0 0 0 0
        exit 0
    else
        # echo $JSON_DATA
        # echo "Authentication Failed Exiting with 1"
        exit 1
    fi
else
    exit 1  # Exit with status 0 (error) for other methods or status codes
fi
