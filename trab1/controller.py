import random
import numpy as np
import matplotlib.pyplot as plt

class Controller:
    def __init__(self, min_trainers=2, trainers_per_round=2, num_rounds=5):
        self.trainer_list = []
        self.min_trainers = min_trainers
        self.trainers_per_round = trainers_per_round
        self.current_round = 0
        self.num_rounds = num_rounds # total number of rounds
        self.num_responses = 0 # number of responses received on aggWeights and metrics
        self.weights = [] # save weights for agg
        self.trainer_samples = [] # save num_samples scale for agg
        self.acc_list = []
        self.mean_acc_per_round = []
    
    # getters
    def get_trainer_list(self):
        return self.trainer_list
    
    def get_current_round(self):
        return self.current_round
    
    def get_num_trainers(self):
        return len(self.trainer_list)
    
    def get_num_responses(self):
        return self.num_responses

    def get_mean_acc(self):
        mean = float(np.mean(np.array(self.acc_list)))
        self.mean_acc_per_round.append(mean) # save mean acc
        return mean
    
    # "setters"
    def update_num_responses(self):
        self.num_responses += 1
    
    def reset_num_responses(self):
        self.num_responses = 0
    
    def reset_acc_list(self):
        self.acc_list = []
    
    def update_current_round(self):
        self.current_round += 1
    
    def add_trainer(self, trainer_id):
        self.trainer_list.append(trainer_id)

    def add_weight(self, weights):
        self.weights.append(weights)
    
    def add_num_samples(self, num_samples):
        self.trainer_samples.append(num_samples)
    
    def add_accuracy(self, acc):
        self.acc_list.append(acc)

    # operations
    def select_trainers_for_round(self):
        return random.sample(self.trainer_list, self.trainers_per_round)
    
    def agg_weights(self):
        scaling_factor = list(np.array(self.trainer_samples) / np.array(self.trainer_samples).sum())
        
        # scale weights
        for scaling, weights in zip(scaling_factor, self.weights):
            for i in range(0, len(weights)):
                weights[i] = weights[i] * scaling
        
        # agg weights
        agg_weights = []
        for layer in range(0, len(self.weights[0])):
            var = []
            for model in range(0, len(self.weights)):
                var.append(self.weights[model][layer])
            agg_weights.append(sum(var))

        # reset weights and samples for next round
        self.weights = []
        self.trainer_samples = []

        return agg_weights

    def plot_training_metrics(self):
        fig, ax = plt.subplots(1, 1)
        x = self.mean_acc_per_round
        y = np.arange(len(x)) + 1
        plt.plot([str(s) for s in y], x)
        plt.annotate('%0.3f' % x[-1], xy=(1, x[-1]), xytext=(8, 0), 
                    xycoords=('axes fraction', 'data'), textcoords='offset points')
        plt.xlabel('rounds')
        plt.ylabel('accuracy')
        plt.title(f'simulation using num_rounds={len(x)}')
        plt.savefig(f'./simulation-rounds={len(x)}.png', dpi=600)
        plt.close(fig)

                   
        

