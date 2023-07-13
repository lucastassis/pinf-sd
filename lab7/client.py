import paho.mqtt.client as mqtt 
import sys
import random
import json
import time
import hashlib
import uuid
import datetime
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from cryptography.x509 import CertificateBuilder
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
from node import Node

n = len(sys.argv)

if n < 3:
    print('Incorrect command, try: python client.py <BROKER_ADDR> <N_CLIENTS>')
    exit()

BROKER_ADDR  = sys.argv[1]
N = int(sys.argv[2])

def on_connect(client, userdata, flags, rc):
    client.subscribe('sd/42/init')
    client.subscribe('sd/42/voting')
    client.subscribe('sd/42/challenge')
    client.subscribe('sd/42/solution')
    client.subscribe('sd/42/exit')
    client.subscribe('sd/42/cert')

def on_message_init(client, userdata, message):
    m = json.loads(message.payload.decode("utf-8"))
    node.add_node_init(m['NodeID'])

def on_message_voting(client, userdata, message):
    m = json.loads(message.payload.decode("utf-8"))
    node_id = m['NodeID']
    if int(node_id) != node.get_id():
        # verify signature
        signature = bytes.fromhex(m['Signature'])
        verification = node.verify_signature(node_id=node_id, message=bytes(str(m['VoteID']), 'utf-8'), signature=signature)
        if verification:
            node.add_node_voting(m)

def on_message_challenge(client, userdata, message):
    if not node.is_leader():
        print('starting to solve challenge!')
        m = json.loads(message.payload.decode("utf-8"))
        node_id = m['NodeID']
        if int(node_id) != node.get_id():
            # verify signature
            signature = bytes.fromhex(m['Signature'])
            verification = node.verify_signature(node_id=node_id, message=bytes(str(m['Challenge']), 'utf-8'), signature=signature)
            if verification:
                solution = node.solve_challenge(m['Challenge'])
                signature_data = bytes(solution, 'utf-8')
                signature = node.sign_message(signature_data).hex()
                r = json.dumps({'NodeID' : str(node.get_id()), 'Solution' : solution, 'Signature' : signature})
                client.publish('sd/42/solution', r)

def on_message_solution(client, userdata, message):
    if node.is_leader():
        m = json.loads(message.payload.decode("utf-8"))
        node_id = m['NodeID']
        if int(node_id) != node.get_id():
            # verify signature
            signature = bytes.fromhex(m['Signature'])
            verification = node.verify_signature(node_id=node_id, message=bytes(str(m['Solution']), 'utf-8'), signature=signature)
            if verification:
                solved = node.check_solution(m['Solution'])
                if solved:
                    print(f'challenged solved by node {m["NodeID"]} with solution {m["Solution"]}')
                    client.publish('sd/42/exit', True)
                    exit()

def on_message_exit(client, userdata, message):
    exit()

def on_message_cert(client, userdata, message):
    m = json.loads(message.payload.decode("utf-8"))
    # read certificate and save public key
    if int(m['NodeID']) != node.get_id():
        loaded_certificate = x509.load_pem_x509_certificate(m['Cert'].encode('utf-8'), default_backend())
        pubkey = loaded_certificate.public_key()
        node.add_node_key(m['NodeID'], pubkey) 
    
node = Node()
print(f'node (ID: {node.get_id()}) started!')
client = mqtt.Client(str(node.get_id()))
client.connect(BROKER_ADDR)
client.on_connect = on_connect
client.message_callback_add('sd/42/init', on_message_init)
client.message_callback_add('sd/42/voting', on_message_voting)
client.message_callback_add('sd/42/challenge', on_message_challenge)
client.message_callback_add('sd/42/solution', on_message_solution)
client.message_callback_add('sd/42/exit', on_message_exit)
client.message_callback_add('sd/42/cert', on_message_cert)

# start client loop
client.loop_start()

# publish on init and wait
while node.get_num_nodes() != N:
    m = json.dumps({'NodeID' : node.get_id()})
    client.publish('sd/42/init', m)
    time.sleep(1)
# send m again to avoid deadlocks on "late clients"
m = json.dumps({'NodeID' : node.get_id()})
client.publish('sd/42/init', m)

# send public key to certificate authority
m = json.dumps({'NodeID' : node.get_id(), 'PubKey' : node.get_public_key_hex()})
client.publish('sd/42/pubkey', m)

# wait until all nodes keys are registered in the node_keys dict
while node.get_num_keys() != N:
    time.sleep(1)

# publish on voting and wait
print(f'My vote is: {node.get_vote()}')
signature_data = bytes(str(node.get_vote()), 'utf-8')
signature = node.sign_message(signature_data).hex()
m = json.dumps({'NodeID' : str(node.get_id()), 'VoteID' : node.get_vote(), 'Signature' : signature})
client.publish('sd/42/voting', m)
while node.get_num_voters() != N:
    time.sleep(1)

# election
node.election()
time.sleep(2)
# create challenge if leader, solve if not
if node.is_leader():
    # publish challenge
    client.publish('sd/42/challenge', node.create_challenge())
    # wait for node to solve
    while not node.is_solved():
        time.sleep(1)
elif not node.is_leader():
    time.sleep(1) # wait for challenge message

client.loop_stop()


