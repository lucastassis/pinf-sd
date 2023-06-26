import numpy as np
import matplotlib.pyplot as plt

class AggregationServer():
    def __init__(self, num_groups):
        self.num_groups = num_groups
        self.weights = []
        self.trainer_samples = []
        self.num_responses = 0
        self.accuracy_list = []
        self.mean_acc_per_round = []
    
    def add_weight(self, weights):
        self.weights += weights
    
    def add_num_samples(self, num_samples):
        self.trainer_samples += num_samples
    
    def get_num_responses(self):
        return self.num_responses
    
    def update_num_responses(self):
        self.num_responses += 1
    
    def reset_num_responses(self):
        self.num_responses = 0
    
    def add_accuracy(self, new_list):
        self.accuracy_list += new_list

    def reset_accuracy_list(self):
        self.accuracy_list = []
    
    def get_mean_acc(self):
        mean = float(np.mean(np.array(self.accuracy_list)))
        self.mean_acc_per_round.append(mean) # save mean acc
        return mean
    
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