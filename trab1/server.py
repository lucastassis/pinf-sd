import paho.mqtt.client as mqtt
from controller import Controller
import json
import time
import numpy as np

STOP_ACC = 0.7
NUM_ROUNDS = 2
MIN_TRAINERS = 2

def on_connect(client, userdata, flags, rc):
    subscribe_queues = ['sd/trab42/registerQueue', 'sd/trab42/preAggQueue', 'sd/trab42/metricsQueue']
    for s in subscribe_queues:
        client.subscribe(s)
    
def on_message_register(client, userdata, message):
    controller.add_trainer(message.payload.decode("utf-8"))
    print(f'trainer number {message.payload.decode("utf-8")} just joined the pool')

def on_message_agg(client, userdata, message):
    # do stuff
    msg = json.loads(message.payload.decode("utf-8"))
    weights = [np.asarray(w, dtype=np.float32) for w in msg['weights']]
    num_samples = msg['num_samples']
    controller.add_weight(weights) # add weight to list of weights
    controller.add_num_samples(num_samples) # add num samples to list of num_samples
    controller.update_num_responses()

def on_message_metrics(client, userdata, message):
    msg = json.loads(message.payload.decode("utf-8"))
    print(msg['accuracy'], type(msg['accuracy']))
    controller.add_accuracy(msg['accuracy'])
    controller.update_num_responses()
    
# connect on queue
controller = Controller(min_trainers=MIN_TRAINERS, num_rounds=NUM_ROUNDS)
client = mqtt.Client('server')
client.connect('localhost')
client.on_connect = on_connect
client.message_callback_add('sd/trab42/registerQueue', on_message_register)
client.message_callback_add('sd/trab42/preAggQueue', on_message_agg)
client.message_callback_add('sd/trab42/metricsQueue', on_message_metrics)

# start loop
client.loop_start()
print('starting server...')

# wait trainers to connect
while controller.get_num_trainers() < MIN_TRAINERS:
    time.sleep(1)

# begin training
while controller.get_current_round() != controller.get_num_rounds():
    controller.update_current_round()

    # choose trainers for round
    trainer_list = controller.get_trainer_list()
    chosen_trainers = controller.choose_trainers_for_round()
    for t in trainer_list:
        if t in chosen_trainers:
            m = json.dumps({'id' : t, 'chosen' : True}).replace(' ', '')
            client.publish('sd/trab42/selectionQueue', m)
        else:
            m = json.dumps({'id' : t, 'chosen' : False}).replace(' ', '')
            client.publish('sd/trab42/selectionQueue', m)
    
    # wait for agg responses
    while controller.get_num_responses() != controller.get_min_trainers():
        time.sleep(1)
    controller.reset_num_responses() # reset num_responses for next round

    # aggregate and send
    agg_weights = controller.agg_weights()
    response = json.dumps({'weights' : [w.tolist() for w in agg_weights]})
    client.publish('sd/trab42/posAggQueue', response)

    # wait for metrics response
    while controller.get_num_responses() != controller.get_num_trainers():
        time.sleep(1)
    controller.reset_num_responses() # reset num_responses for next round 

    # update stop queue or continue process
    if controller.get_mean_acc() >= STOP_ACC:
        msg = json.dumps({'stop' : True})
        client.publish('sd/trab42/stopQueue', msg)
        time.sleep(1)
        exit()
    
    controller.reset_acc_list()

client.publish('sd/trab42/stopQueue', msg)
client.loop_stop()