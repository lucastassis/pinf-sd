import paho.mqtt.client as mqtt 
import sys
import random
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
    if message.topic == 'sd/42/challenge/':
        on_message_challenge(client, userdata, message)
    elif message.topic == 'sd/42/result/':
        on_message_result(client, userdata, message)

def on_message_challenge(client, userdata, message):
    print("Received message on " + str(message.topic) + ": " + str(message.payload.decode("utf-8")))
    challenge_dict = json.loads(str(message.payload.decode("utf-8")))
    challenge = challenge_dict['Challenge']
    transactionID = challenge_dict['TransactionID']
    i = 0
    while True:
        res = hashlib.sha1(str(i).encode()).hexdigest()
        bin_res = str_bin_in_4digits(res)
        if bin_res[:challenge] == challenge * '0':
            topic = 'sd/42/solution/'
            solution = {'ClientID' : id, 'TransactionID' : transactionID, 'Solution' : str(i)}
            solution = json.dumps(solution).replace(' ', '')
            client.publish(topic, solution)
            break
        i += 1
    
def on_message_result(client, userdata, message):
    print("Received message on " + str(message.topic) + ": " + str(message.payload.decode("utf-8")))
    response = json.loads(str(message.payload.decode("utf-8")))
    # if response['Result'] != 0:
    #     client.loop_stop()
    
# init
id = random.randint(0, 10000000)
print(f'Client {id}')
broker_addr = str(sys.argv[1])
client = mqtt.Client(str(id))
client.connect(broker_addr) 

client.loop_start()
topic_challenge = 'sd/42/challenge/'
topic_result = 'sd/42/result/'
client.subscribe(topic_challenge)
client.subscribe(topic_result)
client.on_message=on_message
time.sleep(60 * 10)
client.loop_stop()