import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPool2D,Flatten,Dense
from tensorflow.keras.optimizers import SGD
import uuid
import numpy as np
import random
import matplotlib.pyplot as plt

class Trainer():
    def __init__(self, min_trainers, trainers_per_round, num_rounds):
        # ids and vars for election
        self.id = uuid.uuid1().int
        self.client_list = [self.id]
        self.vote = uuid.uuid1().int
        self.voter_list = {str(self.id) : self.vote}
        self._is_leader = False

        # vars if trainer
        self.model = self.define_model()
        self.num_samples = int(np.random.choice(np.arange(10000, 20000, 1000))) # select a random number ranging from 10000 < num_samples < 20000
        self.x_train, self.y_train, self.x_test, self.y_test = self.split_data()
        self.stop_flag = False

        # vars if leader
        self.trainer_list = []
        self.min_trainers = min_trainers
        self.trainers_per_round = trainers_per_round
        self.current_round = 0
        self.num_rounds = num_rounds
        self.num_responses = 0 # number of responses received on aggWeights and metrics
        self.weights = [] # save weights for agg
        self.trainer_samples = [] # save num_samples scale for agg
        self.accuracy_list = []
        self.mean_accuracy = 0

    # --------------- general methods --------------- #
    # getters and setters
    def get_id(self):
        return self.id
    
    def get_vote(self):
        return self.vote
    
    def get_voter_list(self):
        return self.voter_list
    
    def get_client_list(self):
        return self.client_list
    
    def get_num_clients(self):
        return len(self.client_list)

    def get_num_voters(self):
        return len(self.voter_list)
    
    def add_new_client(self, new_id):
        if new_id not in self.client_list:
            self.client_list.append(new_id)
    
    def add_client_vote(self, vote):
        self.voter_list.update({vote['id'] : vote['vote']})
    
    def is_leader(self):
        return self._is_leader
    
    # election ops
    def election(self):
        winner = max(self.voter_list, key=self.voter_list.get)
        if int(winner) == self.id:
            self._is_leader = True
            self.trainer_list = self.client_list.copy()
            self.trainer_list.remove(self.id)
            print(f'I\'m the leader!')
        else:
            self._is_leader = False
            print(f'I\'m a trainer!')

    # --------------- trainer methods --------------- #
    def get_num_samples(self):
        return self.num_samples
    
    def define_model(self, input_shape=(28, 28, 1), n_classes=10):
        model = Sequential()
        model.add(Conv2D(32, (3, 3), activation='relu', kernel_initializer='he_uniform', input_shape=input_shape))
        model.add(MaxPool2D((2, 2)))
        model.add(Flatten())
        model.add(Dense(100, activation='relu', kernel_initializer='he_uniform'))
        model.add(Dense(n_classes, activation='softmax'))
        opt = SGD(learning_rate=0.01, momentum=0.9)
        model.compile(optimizer=opt, loss='categorical_crossentropy', metrics=['accuracy'])

        return model
    
    def split_data(self):
        # load and preprocess data
        (x_train, y_train), (x_test, y_test) = tf.keras.datasets.mnist.load_data()
        x_train = x_train / 255
        x_test = x_test / 255
        # split data
        idx_train = np.random.choice(np.arange(len(x_train)), self.num_samples, replace=False)
        x_train = x_train[idx_train]
        y_train = tf.one_hot(y_train[idx_train].astype(np.int32), depth=10)
        
        idx_test = np.random.choice(np.arange(len(x_test)), 3000, replace=False)
        x_test = x_test[idx_test]
        y_test = tf.one_hot(y_test[idx_test].astype(np.int32), depth=10)

        return x_train, y_train, x_test, y_test

    def train_model(self):
        self.model.fit(x=self.x_train, y=self.y_train, batch_size=64, epochs=10, verbose=3)

    def eval_model(self):
        acc = self.model.evaluate(x=self.x_test, y=self.y_test, verbose=False)[1]
        return acc
    
    def get_weights(self):
        return self.model.get_weights()
    
    def update_weights(self, weights):
        self.model.set_weights(weights)
    
    def set_stop_true(self):
        self.stop_flag = True
    
    def get_stop_flag(self):
        return self.stop_flag

    # --------------- leader methods --------------- #
    # getters
    def get_trainer_list(self):
        return self.trainer_list
    
    def get_current_round(self):
        return self.current_round
    
    def get_num_trainers(self):
        return len(self.trainer_list)
    
    def get_num_responses(self):
        return self.num_responses
    
    # "setters"
    def update_num_responses(self):
        self.num_responses += 1
    
    def reset_num_responses(self):
        self.num_responses = 0
    
    def update_current_round(self):
        self.current_round += 1

    def add_weight(self, weights):
        self.weights.append(weights)
    
    def get_weight_list(self):
        return self.weights

    def reset_weight_list(self):
        self.weights = []
    
    def add_num_samples(self, num_samples):
        self.trainer_samples.append(num_samples)
    
    def get_trainer_samples_list(self):
        return self.trainer_samples

    def reset_trainer_samples_list(self):
        self.trainer_samples = []
    
    def add_accuracy(self, acc):
        self.accuracy_list.append(acc)
    
    def get_accuracy_list(self):
        return self.accuracy_list
    
    def reset_accuracy_list(self):
        self.accuracy_list = []
    
    def set_mean_accuracy(self, mean_accuracy):
        self.mean_accuracy = mean_accuracy
        
    def get_mean_accuracy(self):
        return self.mean_accuracy
    
    # operations
    def select_trainers_for_round(self):
        return random.sample(self.trainer_list, self.trainers_per_round)
    