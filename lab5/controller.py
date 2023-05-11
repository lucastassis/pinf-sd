import paho.mqtt.client as mqtt 
import sys
import random
import pandas as pd
import json
import time
import hashlib

# From https://codereview.stackexchange.com/a/260276
def str_bin_in_4digits(hex_string: str) -> str:
    """
    Turn a hex string into a binary string.
    In the output string, binary digits are space separated in groups of 4.
    >>> str_bin_in_4digits('20AC')
    '0010000010101100'
    """

    return f"{int(hex_string,16):0{len(hex_string)*5-1}_b}".replace('_', '')

def on_message(client, userdata, message):
    print("Received message on " + str(message.topic) + ": " + str(message.payload.decode("utf-8")))
    solution_dict = json.loads(str(message.payload.decode("utf-8")))
    solution = solution_dict['Solution'] 
    res = hashlib.sha1(solution.encode()).hexdigest()
    bin_res = str_bin_in_4digits(res)
    challenge = new_challenge['Challenge']
    if bin_res[:challenge] == challenge * '0':
        topic = 'sd/42/result/'
        solution = {'ClientID' : solution_dict['ClientID'], 
                    'TransactionID' : new_challenge['TransactionID'], 
                    'Solution' : solution,
                    'Result' : 1}
        solution = json.dumps(solution).replace(' ', '')
        client.publish(topic, solution)
        # client.loop_stop()
    else:
        topic = 'sd/42/result/'
        solution = {'ClientID' : solution_dict['ClientID'], 
                    'TransactionID' : new_challenge['TransactionID'], 
                    'Solution' : solution,
                    'Result' : 0}
        solution = json.dumps(solution).replace(' ', '')
        client.publish(topic, solution)

# init
id = random.randint(0, 10000000)
broker_addr = str(sys.argv[1])
client = mqtt.Client(str(id))
client.connect(broker_addr) 

while True:
    print('Escolha:')
    print('1 para gerar novo desafio,')
    print('2 para finalizar')

    n = input('qual sua escolha: ')

    if n == '1':
        # publish 
        topic = 'sd/42/challenge/'
        new_challenge = {'TransactionID' : 0, 'Challenge' : random.randint(20, 25)}
        str_new_challenge = json.dumps(new_challenge).replace(' ', '')
        client.publish(topic, str_new_challenge)

        # subscribe
        client.loop_start()
        topic = 'sd/42/solution/'
        client.subscribe(topic)
        client.on_message=on_message 
        time.sleep(10 * 60)
        client.loop_stop()
    if n == '2':
        print('bye')
        exit()