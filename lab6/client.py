import paho.mqtt.client as mqtt 
import sys
import random
import json
import time
import hashlib
import uuid
from miner import Miner

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
    client.subscribe('sd/42/result')
    client.subscribe('sd/42/exit')

def on_message_init(client, userdata, message):
    m = json.loads(message.payload.decode("utf-8"))
    miner.add_miner_init(m['ClientID'])

def on_message_voting(client, userdata, message):
    m = json.loads(message.payload.decode("utf-8"))
    miner.add_miner_voting(m)

def on_message_challenge(client, userdata, message):
    if not miner.is_leader():
        print('Starting to solve challenge!')
        m = json.loads(message.payload.decode("utf-8"))
        result = miner.solve_challenge(m['Challenge'])
        r = json.dumps({'ClientID' : str(miner.get_id()), 'Solution' : result})
        client.publish('sd/42/result', r)

def on_message_result(client, userdata, message):
    if miner.is_leader():
        m = json.loads(message.payload.decode("utf-8"))
        solved = miner.check_solution(m['Solution'])
        if solved:
            print(f'Challenged solved by miner {m["ClientID"]} with solution {m["Solution"]}')
            client.publish('sd/42/exit', True)
            exit()

def on_message_exit(client, userdata, message):
    exit()
    
miner = Miner()
print(f'Miner (ID: {miner.get_id()}) started!')
client = mqtt.Client(str(miner.get_id()))
client.connect(BROKER_ADDR)
client.on_connect = on_connect
client.message_callback_add('sd/42/init', on_message_init)
client.message_callback_add('sd/42/voting', on_message_voting)
client.message_callback_add('sd/42/challenge', on_message_challenge)
client.message_callback_add('sd/42/result', on_message_result)
client.message_callback_add('sd/42/exit', on_message_exit)

# start client loop
client.loop_start()

# publish on init and wait
while miner.get_num_miners() != N:
    m = json.dumps({'ClientID' : miner.get_id()})
    client.publish('sd/42/init', m)
    time.sleep(1)

# send m again to avoid deadlocks on "late clients"
m = json.dumps({'ClientID' : miner.get_id()})
client.publish('sd/42/init', m)

# publish on voting and wait
print(f'My vote is: {miner.get_vote()}')
m = json.dumps({'ClientID' : str(miner.get_id()), 'VoteID' : miner.get_vote()})
client.publish('sd/42/voting', m)
while miner.get_num_voters() != N:
    time.sleep(1)

# election
miner.election()

# create challenge if leader, solve if not
if miner.is_leader():
    # publish challenge
    client.publish('sd/42/challenge', miner.create_challenge())
    # wait for miner to solve
    while not miner.is_solved():
        time.sleep(1)
elif not miner.is_leader():
    time.sleep(1) # wait for challenge message

client.loop_stop()


