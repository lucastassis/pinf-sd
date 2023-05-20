import paho.mqtt.client as mqtt 
import sys
import random
import pandas as pd
import json
import time
import hashlib
import uuid

# total args
n = len(sys.argv)

# check args
if (n != 2):
    print("correct use: python controller.py <broker_address>")
    exit()

# some control vars
BROKER_ADDR = sys.argv[1]
class Controller:
    transactions = pd.DataFrame()        
       
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
    solution_dict = json.loads(str(message.payload.decode("utf-8")))
    solution = solution_dict['Solution'] 
    res = hashlib.sha1(solution.encode()).hexdigest()
    bin_res = str_bin_in_4digits(res)
    challenge = controller.transactions.iloc[-1]['Challenge']
    winner = controller.transactions.loc[controller.transactions['TransactionID'] == solution_dict['TransactionID'], 'Winner'].item()
    # verifica se o challenge ja foi resolvido
    if winner == -1:
        # resposta correta
        if bin_res[:challenge] == challenge * '0':
            topic = 'sd/42/result/'
            solution = {'ClientID' : solution_dict['ClientID'], 
                        'TransactionID' : solution_dict['TransactionID'], 
                        'Solution' : solution,
                        'Result' : 1}
            solution = json.dumps(solution).replace(' ', '')
            client.publish(topic, solution)
            controller.transactions.loc[controller.transactions['TransactionID'] == solution_dict['TransactionID'], 'Winner'] = solution_dict['ClientID']
            controller.transactions.loc[controller.transactions['TransactionID'] == solution_dict['TransactionID'], 'Solution'] = solution_dict['Solution']
        # resposta incorreta
        else:
            topic = 'sd/42/result/'
            solution = {'ClientID' : solution_dict['ClientID'], 
                        'TransactionID' : solution_dict['TransactionID'], 
                        'Solution' : solution,
                        'Result' : 0}
            solution = json.dumps(solution).replace(' ', '')
            client.publish(topic, solution)
    else:
        topic = 'sd/42/result/'
        solution = {'ClientID' : solution_dict['ClientID'], 
                    'TransactionID' : solution_dict['TransactionID'], 
                    'Solution' : solution,
                    'Result' : 0}
        solution = json.dumps(solution).replace(' ', '')
        client.publish(topic, solution)

# init
id = uuid.uuid1().int
transactions = pd.DataFrame() # transaction table
client = mqtt.Client(str(id))
client.connect(BROKER_ADDR) 
client.subscribe(topic='sd/42/solution/')
client.on_message=on_message 
controller = Controller()

print('Inicializando servidor...')
client.loop_start()
while True:
    print('Escolha:')
    print('1 para gerar novo desafio,')
    print('2 para finalizar')
    n = input('Qual sua escolha: ')

    if n == '1':
        print(controller.transactions)
        # publish new challenge
        new_challenge = pd.DataFrame([{'TransactionID' : len(controller.transactions), 'Challenge' : random.randint(10, 20), 'Solution' : '', 'Winner' : -1}])
        controller.transactions = pd.concat([controller.transactions, new_challenge], ignore_index=True)
        str_new_challenge = json.dumps(controller.transactions.iloc[-1].to_dict()).replace(' ', '')
        client.publish('sd/42/challenge/', str_new_challenge)

        while controller.transactions.tail(1)['Winner'].item() == -1:
            time.sleep(1)
        
    if n == '2':
        print('Tchau!')
        exit()
