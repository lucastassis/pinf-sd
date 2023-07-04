import paho.mqtt.client as mqtt 
import sys
import random
import json
import time
import uuid
from trainer import Trainer
import numpy as np
class color:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD_START = '\033[1m'
    BOLD_END = '\033[0m'
    RESET = "\x1B[0m"

# --------------- create trainer and connect on queues --------------- #
# total args
n = len(sys.argv)
 
# check args
if (n != 7):
    print("correct use: python server.py <broker_address> <min_clients> <clients_per_round> <num_rounds> <accuracy_threshold> <group_number>.")
    exit()

BROKER_ADDR = sys.argv[1]
MIN_TRAINERS = int(sys.argv[2])
TRAINERS_PER_ROUND = int(sys.argv[3])
NUM_ROUNDS = int(sys.argv[4])
STOP_ACC = float(sys.argv[5])
GROUP_NUM = int(sys.argv[6])

# general callbacks
def on_connect(client, userdata, flags, rc):
    client.subscribe(f'sd/trab42/group={GROUP_NUM}/init')
    client.subscribe(f'sd/trab42/group={GROUP_NUM}/election')
    # trainer
    client.subscribe(f'sd/trab42/group={GROUP_NUM}/selection')
    client.subscribe(f'sd/trab42/group={GROUP_NUM}/aggregation')
    client.subscribe(f'sd/trab42/group={GROUP_NUM}/finish')
    # leader
    client.subscribe(f'sd/trab42/group={GROUP_NUM}/round')
    client.subscribe(f'sd/trab42/group={GROUP_NUM}/evaluation')
    # aggregation server
    client.subscribe(f'sd/trab42/aggregation_server/aggregated')
    client.subscribe(f'sd/trab42/aggregation_server/mean_accuracy')

# register new clients on client list
def on_message_init(client, userdata, message):
    m = json.loads(message.payload.decode("utf-8"))
    trainer.add_new_client(m['id'])

# register clients votes
def on_message_voting(client, userdata, message):
    m = json.loads(message.payload.decode("utf-8"))
    trainer.add_client_vote(m)

# trainer callbacks
# train model if selected for training
def on_message_selection(client, userdata, message):
    if not trainer.is_leader():
        m = json.loads(message.payload.decode("utf-8"))
        if trainer.get_id() in m['selected']:
            print(color.BOLD_START + 'new round starting' + color.BOLD_END)
            print(f'trainer was selected for training this round and will start training!')
            trainer.train_model()
            r = json.dumps({'id' : trainer.get_id(), 'weights' : [w.tolist() for w in trainer.get_weights()], 'num_samples' : trainer.get_num_samples()})
            client.publish(f'sd/trab42/group={GROUP_NUM}/round', r)
            print(f'finished training and sent weights!')
        else:
            print(color.BOLD_START + 'new round starting' + color.BOLD_END)
            print(f'trainer was not selected for training this round')

# update aggregated weights and compute accuracy on round
def on_message_aggregation(client, userdata, message):
    if not trainer.is_leader():
        m = json.loads(message.payload.decode("utf-8"))
        print(f'received aggregated weights!')
        agg_weights = [np.asarray(w, dtype=np.float32) for w in m["weights"]]
        trainer.update_weights(agg_weights)
        r = json.dumps({'id' : trainer.get_id(), 'accuracy' : trainer.eval_model()})
        print(f'sending eval metrics!\n')
        client.publish(f'sd/trab42/group={GROUP_NUM}/evaluation', r)

# finish process
def on_message_finish(client, userdata, message):
    if not trainer.is_leader():
        trainer.set_stop_true()
        exit()

# leader callbacks
# receive weights from trainers and add to list
def on_message_round(client, userdata, message):
    if trainer.is_leader():
        m = json.loads(message.payload.decode("utf-8"))
        num_samples = m['num_samples']
        trainer.add_weight(m['weights']) # add weight to list of weights
        trainer.add_num_samples(num_samples) # add num samples to list of num_samples
        trainer.update_num_responses()
        print(f'received weights from trainer {m["id"]}!')

# receive accuracy from trainers and add to list
def on_message_evaluation(client, userdata, message):
    if trainer.is_leader():
        m = json.loads(message.payload.decode("utf-8"))
        trainer.add_accuracy(m['accuracy'])
        trainer.update_num_responses()

# receive aggregated weights from central server and send to trainers
def on_message_server_aggregated(client, userdata, message):
    if trainer.is_leader():
        m = json.loads(message.payload.decode("utf-8"))
        response = json.dumps({'weights' : m['weights']})
        client.publish(f'sd/trab42/group={GROUP_NUM}/aggregation', response)

# receive mean accuracy from central server
def on_message_server_mean_accuracy(client, userdata, message):
    if trainer.is_leader():
        m = json.loads(message.payload.decode("utf-8"))
        # update stop queue or continue process
        trainer.set_mean_accuracy(m['mean_accuracy'])
        trainer.update_num_responses()
        
# start client
trainer = Trainer(min_trainers=MIN_TRAINERS, trainers_per_round=TRAINERS_PER_ROUND, num_rounds=NUM_ROUNDS)
print(f'client (ID: {trainer.get_id()}) started on group {GROUP_NUM}!')
client = mqtt.Client(str(trainer.get_id()))
client.connect(BROKER_ADDR)
client.on_connect = on_connect
client.message_callback_add(f'sd/trab42/group={GROUP_NUM}/init', on_message_init)
client.message_callback_add(f'sd/trab42/group={GROUP_NUM}/election', on_message_voting)
# trainer
client.message_callback_add(f'sd/trab42/group={GROUP_NUM}/selection', on_message_selection)
client.message_callback_add(f'sd/trab42/group={GROUP_NUM}/aggregation', on_message_aggregation)
client.message_callback_add(f'sd/trab42/group={GROUP_NUM}/finish', on_message_finish)
# leader
client.message_callback_add(f'sd/trab42/group={GROUP_NUM}/round', on_message_round)
client.message_callback_add(f'sd/trab42/group={GROUP_NUM}/evaluation', on_message_evaluation)
client.message_callback_add('sd/trab42/aggregation_server/aggregated', on_message_server_aggregated)
client.message_callback_add('sd/trab42/aggregation_server/mean_accuracy', on_message_server_mean_accuracy)

# start client loop
client.loop_start()

# --------------- init and election --------------- #
# publish on init and wait
while trainer.get_num_clients() != MIN_TRAINERS:
    m = json.dumps({'id' : trainer.get_id()})
    client.publish(f'sd/trab42/group={GROUP_NUM}/init', m)
    time.sleep(1)

# repeat message to (mostly) avoid deadlocks on "late clients"
m = json.dumps({'id' : trainer.get_id()})
client.publish(f'sd/trab42/group={GROUP_NUM}/init', m)

# publish on voting and wait
print(f'My vote is: {trainer.get_vote()}')
m = json.dumps({'id' : str(trainer.get_id()), 'vote' : trainer.get_vote()})
client.publish(f'sd/trab42/group={GROUP_NUM}/election', m)
while trainer.get_num_voters() != MIN_TRAINERS:
    time.sleep(1)

# repeat message to (mostly) avoid deadlocks
m = json.dumps({'id' : str(trainer.get_id()), 'vote' : trainer.get_vote()})
client.publish(f'sd/trab42/group={GROUP_NUM}/election', m)

# election
trainer.election()

# --------------- trainer loop --------------- #
if not trainer.is_leader():
    while not trainer.get_stop_flag():
        time.sleep(1)

# --------------- leader loop --------------- #
if trainer.is_leader():
    time.sleep(2) # for sync purposes
    while trainer.get_current_round() != NUM_ROUNDS:
        trainer.update_current_round()
        print(color.RESET + '\n' + color.BOLD_START + f'starting round {trainer.get_current_round()}' + color.BOLD_END)
        
        # select trainers for round
        trainer_list = trainer.get_trainer_list()
        select_trainers = trainer.select_trainers_for_round()
        m = json.dumps({'selected' : select_trainers})
        client.publish(f'sd/trab42/group={GROUP_NUM}/selection', m)

        # wait for agg responses
        while trainer.get_num_responses() != TRAINERS_PER_ROUND:
            time.sleep(1)
        trainer.reset_num_responses() # reset num_responses for next round

        # send weights to aggregation server
        # agg_weights = trainer.agg_weights()
        response = json.dumps({'weights' : trainer.get_weight_list(), 'num_samples' : trainer.get_trainer_samples_list(), 'group' : GROUP_NUM})
        client.publish(f'sd/trab42/aggregation_server/aggregation', response)
        print(f'sent aggregated weights to aggregation server!')
        trainer.reset_weight_list()
        trainer.reset_trainer_samples_list()

        # wait for metrics response and send to aggregation server
        while trainer.get_num_responses() != trainer.get_num_trainers():
            time.sleep(1)
        trainer.reset_num_responses() # reset num_responses for next round 
        response = json.dumps({'accuracy_list' : trainer.get_accuracy_list()})
        client.publish('sd/trab42/aggregation_server/evaluation', response)
        trainer.reset_accuracy_list()

        # wait for mean accuracy from aggregation server
        while trainer.get_num_responses() != 1:
            time.sleep(1)
        trainer.reset_num_responses()

        # check if mean accuracy on the round met the threshold
        print(color.GREEN +f'mean accuracy on round {trainer.get_current_round()} was {trainer.get_mean_accuracy()}\n' + color.RESET)
        if trainer.get_mean_accuracy() >= STOP_ACC:
            print(color.RED + f'accuracy threshold met! stopping the training!')
            m = json.dumps({'stop' : True})
            client.publish(f'sd/trab42/group={GROUP_NUM}/finish', m)
            time.sleep(1)
            exit()

    print(color.RED + f'rounds threshold met! stopping the training!')
    m = json.dumps({'stop' : True})
    client.publish(f'sd/trab42/group={GROUP_NUM}/finish', m)

client.loop_stop()


