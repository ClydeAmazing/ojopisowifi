from cryptography.fernet import Fernet
from base64 import b64decode
from app import models
import rsa
import json

def api_response(code):
    response = dict()

    if code == 200:
        response['code'] = code
        response['status'] = 'Success'
        response['description'] = ''

    if code == 300:
        response['code'] = code
        response['status'] = 'Error'
        response['description'] = 'Pay error.'

    if code == 400:
        response['code'] = code
        response['status'] = 'Error'
        response['description'] = 'Pay error. Slot Not Found.'

    if code == 500:
        response['code'] = code
        response['status'] = 'Error'
        response['description'] = 'Session Timeout. <strong><a href="/app/portal">Click to refresh your browser.</a></strong>'

    if code == 600:
        response['code'] = code
        response['status'] = 'Error'
        response['description'] = 'Someone is still paying. Try again.'

    if code == 700:
        response['code'] = code
        response['status'] = 'Error'
        response['description'] = 'Invalid action.'

    if code == 800:
        response['code'] = code
        response['status'] = 'Error'
        response['description'] = 'Client not found.'

    if code == 900:
        response['code'] = code
        response['status'] = 'Error'
        response['description'] = 'Unknown coin inserted.'

    if code == 110:
        response['code'] = code
        response['status'] = 'Error'
        response['description'] = 'Invalid / Used / Expired voucher code.'

    return  response

def fprint():
    serial = None
    mac = None
    try:
        f = open('/proc/cpuinfo','r')
        for line in f:
            if line[0:6]=='Serial':
                serial = line[10:26]
        f.close()
        mac = open("/sys/class/net/eth0/address").read().strip()
    except Exception:
        pass

    return {
            'serial': serial,
            'eth0_mac': mac
        }

def cc(ac=None):
    dev = models.Device.objects.get(pk=1)
    data = dev.Device_SN + dev.Ethernet_MAC
    pub_rsa = dev.pub_rsa
    p_key = rsa.PublicKey.load_pkcs1(pub_rsa, 'PEM')

    try:
        dev_id = b64decode(ac if ac else dev.Device_ID)
    except:
        return False
        
    try:
        rsa.verify(data.encode('utf-8'), dev_id, p_key)
    except rsa.VerificationError:
        return False
    else:
        return True

def grc():
    dev = models.Device.objects.get(pk=1)
    ca = dev.ca
    data = dict()
    data['serial'] = dev.Device_SN
    data['eth0_mac'] = dev.Ethernet_MAC
    f = Fernet(ca)
    data_byte = json.dumps(data).encode('utf-8')
    res = f.encrypt(data_byte)
    return res

def credit_pulse(slot_id, pulse):
    try:
        slot_info = models.CoinSlot.objects.get(Slot_ID=slot_id)
    except models.CoinSlot.DoesNotExist:
        resp = api_response(400)
    else:
        try:
            rates = models.Rates.objects.get(Pulse=pulse)
        except models.Rates.DoesNotExist:
            resp = api_response(900)
        else:
            connected_client = slot_info.Client
            is_inserting = False

            if connected_client:
                is_inserting, _, _ = connected_client.is_inserting_coin()

            if is_inserting:
                ledger = models.Ledger()
                ledger.Client = connected_client
                ledger.Denomination = rates.Denom
                ledger.Slot_No = slot_info.pk
                ledger.save()

                q, _ = models.CoinQueue.objects.get_or_create(Client=connected_client)
                q.Total_Coins += rates.Denom
                q.save()

                slot_info.save()

                resp = api_response(200)
            else:
                resp = api_response(300)
    return resp