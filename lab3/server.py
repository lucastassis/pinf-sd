import grpc
from concurrent import futures
import mine_grpc_pb2
import mine_grpc_pb2_grpc
import hashlib
import pandas as pd
import random

def serve():
    grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    mine_grpc_pb2_grpc.add_apiServicer_to_server(Servicer(), grpc_server)
    grpc_server.add_insecure_port('[::]:8080')
    grpc_server.start()
    grpc_server.wait_for_termination()

class Servicer(mine_grpc_pb2_grpc.apiServicer):

    def __init__(self):
        self.transactionTable = pd.DataFrame([{'TransactionID' : 0,
                                              'Challenge' : random.randint(1, 3),
                                              'Solution' : "",
                                              'Winner' : 0}])

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
            if result != 0:
                result = 0
            else:
                result = 1
        except:
            result = -1
        print(f'getTransactionStatus() results in {result}')        
        return mine_grpc_pb2.intResult(result=result)
        
    def submitChallenge(self, request, context):
        pass
    
    def getWinner(self, request, context):
        try:
            current = self.transactionTable[self.transactionTable['TransactionID'] == request.transactionId]
            result = current['Winner'].tolist()[0]
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