import grpc
import mine_grpc_pb2
import mine_grpc_pb2_grpc
import pybreaker

breaker = pybreaker.CircuitBreaker(fail_max=2, reset_timeout=2)

def run(client, n):
    if n == '1':
        print('getTransactionId:')
        res = client.getTransactionId(mine_grpc_pb2.void())
        print(res)
    elif n == '2':
        print('getChallenge:')
        x = int(input('input transactionId: '))
        res = client.getChallenge(mine_grpc_pb2.transactionId(transactionId=0))
        print(res)
    elif n == '3':
        print('getTransactionStatus:')
        x = int(input('input transactionId: '))
        res = client.getTransactionStatus(mine_grpc_pb2.transactionId(transactionId=0))
        print(res)
    elif n == '4':
        print('getWinner:')
        x = int(input('input transactionId: '))
        res = client.getWinner(mine_grpc_pb2.transactionId(transactionId=0))
        print(res)
    elif n == '5':
        print('getSolution:')
        x = int(input('input transactionId: '))
        res = client.getSolution(mine_grpc_pb2.transactionId(transactionId=0))
        print(res)
    elif n == '6':
        print('mine')
        print('TODO :)')
    elif n == '7':
        print('bye')
        exit()
    else:
        print('entrada inválida')
    
@breaker
def connect():
    channel = grpc.insecure_channel('localhost:8080')
    client = mine_grpc_pb2_grpc.apiStub(channel)
    
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
            run(client, n)
        except pybreaker.CircuitBreakerError:
            print(pybreaker.CircuitBreakerError)


if __name__ == '__main__':
    connect()