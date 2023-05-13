import paho.mqtt.client as mqtt
from trainer import Trainer
import json 
import numpy as np
import time

def on_connect(client, userdata, flags, rc):
    subscribe_queues = ['sd/trab42/selectionQueue', 'sd/trab42/posAggQueue', 'sd/trab42/stopQueue']
    for s in subscribe_queues:
        client.subscribe(s)

def on_message_selection(client, userdata, message):
    msg = json.loads(message.payload.decode("utf-8"))
    if int(msg['id']) == trainer.get_id():
        if bool(msg['chosen']) == True:
            trainer.train_model()
            response = json.dumps({'id' : trainer.get_id(), 'weights' : [w.tolist() for w in trainer.get_weights()], 'num_samples' : trainer.get_num_samples()})
            client.publish('sd/trab42/preAggQueue', response)

def on_message_agg(client, userdata, message):
    print(f'received aggregated weights')
    msg = json.loads(message.payload.decode("utf-8"))
    agg_weights = [np.asarray(w, dtype=np.float32) for w in msg["weights"]]
    trainer.update_weights(agg_weights)
    response = json.dumps({'id' : trainer.get_id(), 'accuracy' : trainer.eval_model()})
    client.publish('sd/trab42/metricsQueue', response)

def on_message_stop(client, userdata, message):
    print(f'received msg to stop')
    trainer.set_stop_true()
    exit()

# connect on queue and send register 
trainer = Trainer()
client = mqtt.Client(str(trainer.get_id()))
client.connect('localhost')
client.on_connect = on_connect
client.message_callback_add('sd/trab42/selectionQueue', on_message_selection)
client.message_callback_add('sd/trab42/posAggQueue', on_message_agg)
client.message_callback_add('sd/trab42/stopQueue', on_message_stop)
client.publish('sd/trab42/registerQueue', trainer.get_id())

# start waiting for jobs
client.loop_start()

while not trainer.get_stop_flag():
    time.sleep(1)

client.loop_stop()