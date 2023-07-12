import paho.mqtt.client as mqtt 
import random
import sys
import json
import time
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from cryptography.x509 import CertificateBuilder
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption, load_pem_public_key
import datetime
from cryptography.hazmat.primitives import hashes


# python params parser
n = len(sys.argv)
if n < 3:
    print('Incorrect command, try: python client.py <BROKER_ADDR> <N_CLIENTS>')
    exit()
BROKER_ADDR  = sys.argv[1]
N = int(sys.argv[2])

# class definition
class CertificateAuthority():
    def __init__(self):
        self.id = random.getrandbits(32)
        self.node_keys = dict()
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=1024)
        self.public_key = self.private_key.public_key()
    
    def get_id(self):
        return self.id

    def get_node_keys(self):
        return self.node_keys

    def get_num_keys(self):
        return len(self.node_keys)

    def add_node_key(self, node_id, pubkey):
        self.node_keys[node_id] = pubkey
    
    def generate_certificate(self, pubkey):
        # lab code
        subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"BR"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"Espirito Santo"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u"Vitoria"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Universidade Federal do Espirito Santo (Ufes)"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"Ufes"),
    ])  

        print(bytes.fromhex(pubkey))
        key = load_pem_public_key(bytes.fromhex(pubkey))

        cert_builder = x509.CertificateBuilder()
        cert_builder = cert_builder.subject_name(subject)
        cert_builder = cert_builder.issuer_name(issuer)
        cert_builder = cert_builder.public_key(key)
        cert_builder = cert_builder.serial_number(x509.random_serial_number())
        cert_builder = cert_builder.not_valid_before(datetime.datetime.utcnow())
        cert_builder = cert_builder.not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
        cert_builder = cert_builder.add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        cert_builder = cert_builder.sign(self.private_key, hashes.SHA256(), default_backend())

        cert = cert_builder.public_bytes(Encoding.PEM)

        return cert

# MQTT 
def on_connect(client, userdata, flags, rc):
    client.subscribe('sd/42/pubkey')

def on_message_pubkey(client, userdata, message):
    m = json.loads(message.payload.decode("utf-8"))
    print(f'received new pubkey from node {m["NodeID"]}')
    auth.add_node_key(str(m['NodeID']), m['PubKey'])
    
auth = CertificateAuthority()
client = mqtt.Client(str(auth.get_id()))
client.on_connect = on_connect
client.connect(BROKER_ADDR)
client.message_callback_add('sd/42/pubkey', on_message_pubkey)
client.loop_start()

# wait for nodes to send pubkeys
while auth.get_num_keys() != N:
    time.sleep(1)

for node_id, pubkey in auth.get_node_keys().items():
    cert = auth.generate_certificate(pubkey)
    m = json.dumps({'NodeID' : node_id, 'Cert' : cert.decode('utf-8')})
    client.publish('sd/42/cert', m)

client.loop_stop()