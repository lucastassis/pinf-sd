import grpc
import mine_grpc_pb2
import mine_grpc_pb2_grpc
import pybreaker
import hashlib
import numpy as np
import random

breaker = pybreaker.CircuitBreaker(fail_max=2, reset_timeout=2)

# From https://codereview.stackexchange.com/a/260276
def str_bin_in_4digits(hex_string: str) -> str:
    """
    Turn a hex string into a binary string.
    In the output string, binary digits are space separated in groups of 4.

    >>> str_bin_in_4digits('20AC')
    '0010000010101100'
    """

    return f"{int(hex_string,16):0{len(hex_string)*5-1}_b}".replace('_', '')

def mine(client, client_id):
    transactionId = client.getTransactionId(mine_grpc_pb2.void()).result
    challenge = client.getChallenge(mine_grpc_pb2.transactionId(transactionId=transactionId)).result
    print(f'id: {transactionId}, challenge: {challenge}')
    
    m = hashlib.sha1()
    for i in np.random.permutation(10000000).tolist():
        s = str(i)
        m.update(b"s")
        res = m.hexdigest()
        bin_res = str_bin_in_4digits(res)
        if bin_res[:challenge] == challenge * '0':
            res = client.submitChallenge(mine_grpc_pb2.challengeArgs(transactionId=transactionId, clientId=client_id, solution=res))
            return res

def run(client, n, client_id):
    if n == '1':
        print('getTransactionId:')
        res = client.getTransactionId(mine_grpc_pb2.void())
        print(res)
    elif n == '2':
        print('getChallenge:')
        x = int(input('input transactionId: '))
        res = client.getChallenge(mine_grpc_pb2.transactionId(transactionId=x))
        print(res)
    elif n == '3':
        print('getTransactionStatus:')
        x = int(input('input transactionId: '))
        res = client.getTransactionStatus(mine_grpc_pb2.transactionId(transactionId=x))
        print(res)
    elif n == '4':
        print('getWinner:')
        x = int(input('input transactionId: '))
        res = client.getWinner(mine_grpc_pb2.transactionId(transactionId=x))
        print(res)
    elif n == '5':
        print('getSolution:')
        x = int(input('input transactionId: '))
        res = client.getSolution(mine_grpc_pb2.transactionId(transactionId=x))
        print(res)
    elif n == '6':
        print('mine')
        res = mine(client, client_id)
        print(res)
    elif n == '7':
        print('bye')
        exit()
    else:
        print('entrada inválida')
    
@breaker
def connect():
    channel = grpc.insecure_channel('localhost:8080')
    client = mine_grpc_pb2_grpc.apiStub(channel)
    client_id = random.randint(1, 100000)
    print(client_id)
    while True:
        print('Choose:')
        print('1 para getTransactionId,')
        print('2 para getChallenge,')
        print('3 para getTransactionStatus,')
        print('4 para getWinner')
        print('5 para getSolution')
        print('6 para mine')
        print('7 para finalizar')
        
        n = input('qual sua escolha: ')
        
        try:
            run(client, n, client_id)
        except pybreaker.CircuitBreakerError:
            print(pybreaker.CircuitBreakerError)


if __name__ == '__main__':
    connect()