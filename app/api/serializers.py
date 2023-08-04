from rest_framework import serializers

class AuthClientSerializer(serializers.Serializer):
    client_mac = serializers.CharField(max_length=17)
    client_ip = serializers.CharField(max_length=15)
    username = serializers.CharField(max_length=100)
    password = serializers.CharField(max_length=100)
    redir = serializers.CharField(max_length=200)
    user_agent = serializers.CharField(max_length=500)
    client_token = serializers.CharField(max_length=100)
    custom_variable = serializers.CharField(max_length=500)

class ClientAuthSerializer(serializers.Serializer):
    client_mac = serializers.CharField(max_length=17)
    bytes_incoming = serializers.IntegerField()
    bytes_outgoing = serializers.IntegerField()
    session_start = serializers.IntegerField()
    session_end = serializers.IntegerField()
    client_token = serializers.CharField(max_length=100)

class OtherMethodSerializer(serializers.Serializer):
    client_mac = serializers.CharField(max_length=17)
    bytes_incoming = serializers.IntegerField()
    bytes_outgoing = serializers.IntegerField()
    session_start = serializers.IntegerField()
    session_end = serializers.IntegerField()
    client_token = serializers.CharField(max_length=100)
