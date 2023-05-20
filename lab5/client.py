import paho.mqtt.client as mqtt 
import sys
import random
import json
import time
import hashlib
import uuid
import threading as td
import queue


# total args
n = len(sys.argv)
 
# check args
if (n != 2):
    print("correct use: python client.py <broker_address>.")
    exit()

BROKER_ADDR = sys.argv[1]

# From https://codereview.stackexchange.com/a/260276
def str_bin_in_4digits(hex_string: str) -> str:
    """
    Turn a hex string into a binary string.
    In the output string, binary digits are space separated in groups of 4.
    >>> str_bin_in_4digits('20AC')
    '0010000010101100'
    """

    return f"{int(hex_string,16):0{len(hex_string)*5-1}_b}".replace('_', '')

def mine(challenge, queue, init, end):
    for i in range(init, end):
        if queue.empty():
            res = hashlib.sha1(str(i).encode()).hexdigest()
            bin_res = str_bin_in_4digits(res)
            if bin_res[:challenge] == challenge * '0':
                queue.put(str(i))
                break
        else:
            break

def on_message_challenge(client, userdata, message):
    challenge_dict = json.loads(str(message.payload.decode("utf-8")))
    challenge = challenge_dict['Challenge']
    transactionID = challenge_dict['TransactionID']
    print(f'Novo desafio com ID {transactionID} and desafio {challenge} recebido!')

    # search solution with multithreading
    solutions_queue = queue.Queue()
    size = 2 ** 32
    threads = [td.Thread(target=mine, args=(challenge, solutions_queue, 0, int(size / 2))), td.Thread(target=mine, args=(challenge, solutions_queue, int(size / 2), int(size)))]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    #  publish solution
    solution = solutions_queue.get()
    topic = 'sd/42/solution/'
    solution = {'ClientID' : id, 'TransactionID' : transactionID, 'Solution' : solution}
    solution = json.dumps(solution).replace(' ', '')
    client.publish(topic, solution)
    
    
def on_message_result(client, userdata, message):
    response = json.loads(str(message.payload.decode("utf-8")))
    if response['Result'] != 0:
        print(f'Parabens cliente {response["ClientID"]}, sua resposta {response["Solution"]} esta correta!')
    elif response['Result'] == -1:
        print(f'Desculpa cliente {response["ClientID"]}, sua solucao {response["Solution"]} esta incorreta ou o problema já foi resolvido!')
    
# init
id = uuid.uuid1().int
client = mqtt.Client(str(id))
client.connect(BROKER_ADDR) 
print(f'Inicializando minerador {id}')
client.subscribe('sd/42/challenge/')
client.subscribe('sd/42/result/') 
client.message_callback_add('sd/42/challenge/', on_message_challenge)
client.message_callback_add('sd/42/result/', on_message_result)

client.loop_forever()