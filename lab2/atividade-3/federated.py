import os
# Make TensorFlow logs less verbose
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
import flwr as fl
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Flatten,Dense
from tensorflow.keras.optimizers import SGD
import numpy as np
import sys
import matplotlib.pyplot as plt

def weighted_average(metrics):
    # Multiply accuracy of each client by number of examples used
    acc = [num_examples * m["accuracy"] for num_examples, m in metrics]
    examples = [num_examples for num_examples, _ in metrics]

    # Aggregate and return custom metric (weighted average)
    results = {"accuracy": sum(acc) / sum(examples)}
    return results

class FlowerClient(fl.client.NumPyClient):
    def __init__(self, model, x_train, y_train, x_test, y_test) -> None:
        self.model = model
        self.x_train = x_train
        self.y_train = y_train
        self.x_test = x_test
        self.y_test = y_test

    def get_parameters(self, config):
        return self.model.get_weights()

    def fit(self, parameters, config):
        self.model.set_weights(parameters)
        self.model.fit(self.x_train, self.y_train, epochs=1, verbose=2)
        return self.model.get_weights(), len(self.x_train), {}

    def evaluate(self, parameters, config):
        self.model.set_weights(parameters)
        loss, acc = self.model.evaluate(self.x_test, self.y_test, verbose=2)
        return loss, len(self.x_test), {"accuracy": acc}

def define_model_1(input_shape, num_classes):
    model = Sequential()
    model.add(Flatten(input_shape=[input_shape[0], input_shape[1]]))
    model.add(Dense(100, activation='relu', kernel_initializer='he_uniform'))
    model.add(Dense(num_classes, activation='softmax'))
    opt = SGD(learning_rate=0.01, momentum=0.9)
    model.compile(optimizer=opt, loss='categorical_crossentropy', metrics=['accuracy'])

    return model

def define_model_2(input_shape, num_classes):
    model = Sequential()
    model.add(Flatten(input_shape=[input_shape[0], input_shape[1]]))
    model.add(Dense(100, activation='relu', kernel_initializer='he_uniform'))
    model.add(Dense(50, activation='relu', kernel_initializer='he_uniform'))
    model.add(Dense(num_classes, activation='softmax'))
    opt = SGD(learning_rate=0.01, momentum=0.9)
    model.compile(optimizer=opt, loss='categorical_crossentropy', metrics=['accuracy'])

    return model

def client_fn_random_1(cid: str) -> fl.client.Client:
    input_shape = (28, 28, 1)
    num_classes = 10
    num_clients = 10
    
    (x_train, y_train), (x_test, y_test) = tf.keras.datasets.mnist.load_data()
    sample_size_train = int((1/num_clients)*len(x_train))
    sample_size_test = int((1/num_clients)*len(x_test))
    idx_train = np.random.choice(np.arange(len(x_train)), sample_size_train, replace=False)
    x_train = x_train[idx_train]/255.0
    y_train = y_train[idx_train]
    y_train = tf.one_hot(y_train.astype(np.int32), depth=10)
    idx_test = np.random.choice(np.arange(len(x_test)), sample_size_test, replace=False)
    x_test = x_test[idx_test]/255.0
    y_test = y_test[idx_test]
    y_test = tf.one_hot(y_test.astype(np.int32), depth=10)
    model = define_model_1(input_shape,num_classes)
    # Create and return client
    return FlowerClient(model, x_train, y_train, x_test, y_test)

def client_fn_random_2(cid: str) -> fl.client.Client:
    input_shape = (28, 28, 1)
    num_classes = 10
    num_clients = 10
    
    (x_train, y_train), (x_test, y_test) = tf.keras.datasets.mnist.load_data()
    sample_size_train = int((1/num_clients)*len(x_train))
    sample_size_test = int((1/num_clients)*len(x_test))
    idx_train = np.random.choice(np.arange(len(x_train)), sample_size_train, replace=False)
    x_train = x_train[idx_train]/255.0
    y_train = y_train[idx_train]
    y_train = tf.one_hot(y_train.astype(np.int32), depth=10)
    idx_test = np.random.choice(np.arange(len(x_test)), sample_size_test, replace=False)
    x_test = x_test[idx_test]/255.0
    y_test = y_test[idx_test]
    y_test = tf.one_hot(y_test.astype(np.int32), depth=10)
    model = define_model_2(input_shape,num_classes)
    # Create and return client
    return FlowerClient(model, x_train, y_train, x_test, y_test)

def run(model):
    num_clients = 10

    if model == 'model_1':
        # Create FedAvg strategy
        strategy = fl.server.strategy.FedAvg(
            fraction_fit=1,  
            fraction_evaluate=1,  
            min_fit_clients=10,  
            min_evaluate_clients=10,  
            min_available_clients=int(
                num_clients
            ),  
            evaluate_metrics_aggregation_fn=weighted_average,
        )

        # Start simulation
        history = fl.simulation.start_simulation(
            client_fn=client_fn_random_1,
            num_clients=num_clients,
            config=fl.server.ServerConfig(num_rounds=10),
            strategy=strategy,
            
        )

        fig, ax = plt.subplots(1, 1)
        
        y, x = zip(*history.metrics_distributed['accuracy'])
        plt.plot([str(s) for s in y], x)
        plt.annotate('%0.3f' % x[-1], xy=(1, x[-1]), xytext=(8, 0), 
                 xycoords=('axes fraction', 'data'), textcoords='offset points')
        plt.xlabel('rounds')
        plt.ylabel('accuracy')
        plt.title(f'simulation using {model}')
        plt.savefig(f'./federated-model={model}.png', dpi=400)
        plt.close(fig)
    
    elif model == 'model_2':
        # Create FedAvg strategy
        strategy = fl.server.strategy.FedAvg(
            fraction_fit=1,  
            fraction_evaluate=1,  
            min_fit_clients=10,  
            min_evaluate_clients=10,  
            min_available_clients=int(
                num_clients
            ),  
            evaluate_metrics_aggregation_fn=weighted_average,
        )

        # Start simulation
        history = fl.simulation.start_simulation(
            client_fn=client_fn_random_2,
            num_clients=num_clients,
            config=fl.server.ServerConfig(num_rounds=10),
            strategy=strategy,
            
        )

        fig, ax = plt.subplots(1, 1)
        
        y, x = zip(*history.metrics_distributed['accuracy'])
        plt.plot([str(s) for s in y], x)
        plt.annotate('%0.3f' % x[-1], xy=(1, x[-1]), xytext=(8, 0), 
                 xycoords=('axes fraction', 'data'), textcoords='offset points')
        plt.xlabel('rounds')
        plt.ylabel('accuracy')
        plt.title(f'simulation using {model}')
        plt.savefig(f'./federated-model={model}.png', dpi=400)
        plt.close(fig)

if __name__ == '__main__':
    (x_train, y_train), (x_test, y_test) = tf.keras.datasets.mnist.load_data()

    for model in ['model_1', 'model_2']:
        run(model)
