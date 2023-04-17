import flwr as fl
from matplotlib import pyplot as plt
import numpy as np

def weighted_average(metrics):
    # Multiply accuracy of each client by number of examples used
    acc = [num_examples * m["accuracy"] for num_examples, m in metrics]
    examples = [num_examples for num_examples, _ in metrics]

    # Aggregate and return custom metric (weighted average)
    results = {"accuracy": sum(acc) / sum(examples)}
    return results

num_clients= 5
strategy = fl.server.strategy.FedAvg(
    fraction_fit=1,  
    fraction_evaluate=1,  
    min_fit_clients=5,  
    min_evaluate_clients=5,  
    min_available_clients=int(
        num_clients
    ),  
    evaluate_metrics_aggregation_fn=weighted_average,
)

# Start Flower server
sv = fl.server.start_server(
    server_address='127.0.0.1:8080',
    config=fl.server.ServerConfig(num_rounds=40),
    strategy=strategy
)

y, x = zip(*sv.metrics_distributed['accuracy'])
x_process = np.array(x)[[1, 4, 9, 19, 39]]
fig, ax = plt.subplots(1, 1)
plt.plot([str(s) for s in [2, 5, 10, 20, 40]], x_process)
plt.annotate('%0.3f' % x[-1], xy=(1, x[-1]), xytext=(8, 0), 
                 xycoords=('axes fraction', 'data'), textcoords='offset points')
plt.title('accuracy x rounds using num_clients=5')
plt.xlabel('rounds')
plt.ylabel('accuracy')
plt.savefig(f'./simulation-clients=5.png', dpi=400)
plt.close(fig)