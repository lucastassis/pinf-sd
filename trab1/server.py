import paho.mqtt.client as mqtt
from controller import Controller
import json
import time
import numpy as np
import sys

# total args
n = len(sys.argv)
 
# check args
if (n != 6):
    print("correct use: python server.py <broker_address> <min_clients> <clients_per_round> <num_rounds> <accuracy_threshold>.")
    exit()

BROKER_ADDR = sys.argv[1]
MIN_TRAINERS = int(sys.argv[2])
TRAINERS_PER_ROUND = int(sys.argv[3])
NUM_ROUNDS = int(sys.argv[4])
STOP_ACC = float(sys.argv[5])

# class for coloring messages on terminal
class color:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD_START = '\033[1m'
    BOLD_END = '\033[0m'
    RESET = "\x1B[0m"

# subscribe to queues on connection
def on_connect(client, userdata, flags, rc):
    subscribe_queues = ['sd/trab42/registerQueue', 'sd/trab42/preAggQueue', 'sd/trab42/metricsQueue']
    for s in subscribe_queues:
        client.subscribe(s)

# callback for registerQueue: add trainer to the pool of trainers
def on_message_register(client, userdata, message):
    controller.add_trainer(message.payload.decode("utf-8"))
    print(f'trainer number {message.payload.decode("utf-8")} just joined the pool')

# callback for preAggQueue: get weights of trainers, aggregate and send back
def on_message_agg(client, userdata, message):
    m = json.loads(message.payload.decode("utf-8"))
    weights = [np.asarray(w, dtype=np.float32) for w in m['weights']]
    num_samples = m['num_samples']
    controller.add_weight(weights) # add weight to list of weights
    controller.add_num_samples(num_samples) # add num samples to list of num_samples
    controller.update_num_responses()
    print(f'received weights from trainer {m["id"]}!')

# callback for metricsQueue: get accuracy of every trainer and compute the mean
def on_message_metrics(client, userdata, message):
    m = json.loads(message.payload.decode("utf-8"))
    controller.add_accuracy(m['accuracy'])
    controller.update_num_responses()
    
# connect on queue
controller = Controller(min_trainers=MIN_TRAINERS, trainers_per_round=TRAINERS_PER_ROUND, num_rounds=NUM_ROUNDS)
client = mqtt.Client('server')
client.connect(BROKER_ADDR)
client.on_connect = on_connect
client.message_callback_add('sd/trab42/registerQueue', on_message_register)
client.message_callback_add('sd/trab42/preAggQueue', on_message_agg)
client.message_callback_add('sd/trab42/metricsQueue', on_message_metrics)

# start loop
client.loop_start()
print(color.BOLD_START + 'starting server...' + color.BOLD_END)

# wait trainers to connect
while controller.get_num_trainers() < MIN_TRAINERS:
    time.sleep(1)

# begin training
while controller.get_current_round() != NUM_ROUNDS:
    controller.update_current_round()
    print(color.RESET + '\n' + color.BOLD_START + f'starting round {controller.get_current_round()}' + color.BOLD_END)
    # select trainers for round
    trainer_list = controller.get_trainer_list()
    select_trainers = controller.select_trainers_for_round()
    for t in trainer_list:
        if t in select_trainers:
            print(f'selected trainer {t} for training on round {controller.get_current_round()}')
            m = json.dumps({'id' : t, 'selected' : True}).replace(' ', '')
            client.publish('sd/trab42/selectionQueue', m)
        else:
            m = json.dumps({'id' : t, 'selected' : False}).replace(' ', '')
            client.publish('sd/trab42/selectionQueue', m)
    
    # wait for agg responses
    while controller.get_num_responses() != TRAINERS_PER_ROUND:
        time.sleep(1)
    controller.reset_num_responses() # reset num_responses for next round

    # aggregate and send
    agg_weights = controller.agg_weights()
    response = json.dumps({'weights' : [w.tolist() for w in agg_weights]})
    client.publish('sd/trab42/posAggQueue', response)
    print(f'sent aggregated weights to trainers!')

    # wait for metrics response
    while controller.get_num_responses() != controller.get_num_trainers():
        time.sleep(1)
    controller.reset_num_responses() # reset num_responses for next round 
    mean_acc = controller.get_mean_acc()
    print(color.GREEN +f'mean accuracy on round {controller.get_current_round()} was {mean_acc}\n' + color.RESET)

    # update stop queue or continue process
    if mean_acc >= STOP_ACC:
        print(color.RED + f'accuracy threshold met! stopping the training!')
        controller.plot_training_metrics()
        m = json.dumps({'stop' : True})
        client.publish('sd/trab42/stopQueue', m)
        time.sleep(1) # time for clients to finish
        exit()
    controller.reset_acc_list()

print(color.RED + f'rounds threshold met! stopping the training!')
client.publish('sd/trab42/stopQueue', m)
controller.plot_training_metrics()
client.loop_stop()