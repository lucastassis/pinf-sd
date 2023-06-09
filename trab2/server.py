import paho.mqtt.client as mqtt 
import sys
import time
import json
from aggregation_server import AggregationServer
import numpy as np
import uuid

# total args
n = len(sys.argv)
 
# check args
if (n != 5):
    print("correct use: python server.py <broker_address> <num_groups> <num_rounds> <accuracy_threshold>.")
    exit()

BROKER_ADDR = sys.argv[1]
NUM_GROUPS = int(sys.argv[2])
NUM_ROUNDS = int(sys.argv[3])
STOP_ACC = float(sys.argv[4])

# general callbacks
def on_connect(client, userdata, flags, rc):
    client.subscribe('sd/trab42/aggregation_server/aggregation')
    client.subscribe('sd/trab42/aggregation_server/evaluation')

# receive weights from leaders and add to list
def on_message_server_aggregation(client, userdata, message):
    m = json.loads(message.payload.decode("utf-8"))
    print(f'received weights from group {m["group"]}')
    weights = [[np.asarray(w, dtype=np.float32) for w in m['weights'][i]] for i in range(0, len(m['weights']))]
    num_samples = m['num_samples']
    server.add_weight(weights) # add weight to list of weights
    server.add_num_samples(num_samples) # add num samples to list of num_samples
    server.update_num_responses()

# receive accuracy from leaders and add to list
def on_message_server_evaluation(client, userdata, message):
    m = json.loads(message.payload.decode("utf-8"))
    server.add_accuracy(m['accuracy_list'])
    server.update_num_responses()
    

# start client 
print('starting aggregation server')
server = AggregationServer(num_groups=NUM_GROUPS)
client = mqtt.Client(str(uuid.uuid1().int))
client.connect(BROKER_ADDR)
client.on_connect = on_connect

# add callbacks
client.message_callback_add('sd/trab42/aggregation_server/aggregation', on_message_server_aggregation)
client.message_callback_add('sd/trab42/aggregation_server/evaluation', on_message_server_evaluation)

# start client loop
round = 0
client.loop_start()
while round != NUM_ROUNDS:
    round += 1

    # wait for weights and publish aggregated weights
    while server.get_num_responses() != NUM_GROUPS:
        time.sleep(1)
    server.reset_num_responses()

    print(f'aggregating weights for round {round}')
    agg_weights = server.agg_weights()
    response = json.dumps({'weights' : [w.tolist() for w in agg_weights]})
    client.publish('sd/trab42/aggregation_server/aggregated', response)

    # wait for accuracy and publish mean accuracy
    while server.get_num_responses() != NUM_GROUPS:
        time.sleep(1)
    server.reset_num_responses()

    mean_acc = server.get_mean_acc()
    response = json.dumps({'mean_accuracy' : mean_acc})
    client.publish('sd/trab42/aggregation_server/mean_accuracy', response)
    server.reset_accuracy_list()
    print(f'computing mean accuracy on round {round}')

    # finish process if accuracy threshold is met
    if mean_acc >= STOP_ACC:
        print(f'accuracy threshold met! stop the training')
        server.plot_training_metrics()
        client.loop_stop()
        exit()

server.plot_training_metrics()
client.loop_stop()

    


    

