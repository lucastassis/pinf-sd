import grpc
from concurrent import futures
import mine_grpc_pb2
import mine_grpc_pb2_grpc
import hashlib
import pandas as pd
import random

# From https://codereview.stackexchange.com/a/260276
def str_bin_in_4digits(hex_string: str) -> str:
    """
    Turn a hex string into a binary string.
    In the output string, binary digits are space separated in groups of 4.

    >>> str_bin_in_4digits('20AC')
    '0010000010101100'
    """

    return f"{int(hex_string,16):0{len(hex_string)*5-1}_b}".replace('_', '')

def serve():
    grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    mine_grpc_pb2_grpc.add_apiServicer_to_server(Servicer(), grpc_server)
    grpc_server.add_insecure_port('[::]:8080')
    grpc_server.start()
    grpc_server.wait_for_termination()

class Servicer(mine_grpc_pb2_grpc.apiServicer):

    def __init__(self):
        self.transactionTable = pd.DataFrame([{'TransactionID' : 0,
                                              'Challenge' : random.randint(1, 20),
                                              'Solution' : "",
                                              'Winner' : -1}])

    def getTransactionId(self, request, context):
        result = self.transactionTable.iloc[-1]['TransactionID']
        print(f'getTransactionId() results in {result}')
        return mine_grpc_pb2.intResult(result=result)
    
    def getChallenge(self, request, context):
        try:
            current = self.transactionTable[self.transactionTable['TransactionID'] == request.transactionId]
            result = current['Challenge'].tolist()[0]
        except:
            result = -1
        print(f'getChallenge() results in {result}')        
        return mine_grpc_pb2.intResult(result=result)
    
    def getTransactionStatus(self, request, context):
        try:
            current = self.transactionTable.loc[self.transactionTable['TransactionID'] == request.transactionId]
            result = current['Winner'].tolist()[0]
            if result == -1:
                result = 1
            else:
                result = 0
        except:
            result = -1
        print(f'getTransactionStatus() results in {result}')        
        return mine_grpc_pb2.intResult(result=result)
        
    def submitChallenge(self, request, context):
        # check if valid transactionID
        try:
            current = self.transactionTable[self.transactionTable['TransactionID'] == request.transactionId]
            challenge = current['Challenge'].tolist()[0]
        except:
            result = -1
            print(f'submitChallenge() results in {result}')
            return mine_grpc_pb2.intResult(result=result)
        # check if already solved
        if current['Winner'].tolist()[0] != -1:
            result = 2
            print(f'submitChallenge() results in {result}')
            return mine_grpc_pb2.intResult(result=result)
        
        # check if valid solution
        solution = hashlib.sha1(request.solution.encode()).hexdigest()
        bin_solution = str_bin_in_4digits(solution)
        if bin_solution[:challenge] == '0' * challenge:
            result = 1
            self.transactionTable.loc[self.transactionTable['TransactionID'] == request.transactionId, 'Solution'] = request.solution
            self.transactionTable.loc[self.transactionTable['TransactionID'] == request.transactionId, 'Winner'] = request.clientId
            print(f'submitChallenge() results in {result}')

            new_challenge = pd.DataFrame([{'TransactionID' : self.transactionTable.shape[0],
                                           'Challenge' : random.randint(1, 20),
                                           'Solution' : "",
                                           'Winner' : -1}])
            self.transactionTable = pd.concat([self.transactionTable, new_challenge], ignore_index=True)
            return mine_grpc_pb2.intResult(result=result)
        else:
            result = 0
            print(f'submitChallenge() results in {result}')
            return mine_grpc_pb2.intResult(result=result)

    def getWinner(self, request, context):
        try:
            current = self.transactionTable[self.transactionTable['TransactionID'] == request.transactionId]
            result = current['Winner'].tolist()[0]
            if result == -1:
                print(f'getWinner() results in {0}')        
                return mine_grpc_pb2.intResult(result=0)
            else:
                print(f'getWinner() results in {result}')        
                return mine_grpc_pb2.intResult(result=result)
        except:
            result = -1
            print(f'getWinner() results in {result}')        
            return mine_grpc_pb2.intResult(result=result)
        
    
    def getSolution(self, request, context):
        current = self.transactionTable.loc[self.transactionTable['TransactionID'] == request.transactionId]
        status = current['Winner'].tolist()[0]
        solution = current["Solution"].tolist()[0]
        challenge = current['Challenge'].tolist()[0]
        print(f'getTransactionStatus() results in {status, solution, challenge}')
        return mine_grpc_pb2.structResult(status=status, solution=solution, challenge=challenge)

if __name__ == '__main__':
    serve()