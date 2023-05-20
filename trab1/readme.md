# Trabalho I - Aprendizado Federado

[Link para o vídeo de apresentação](https://drive.google.com/file/d/1XBOd1tPMANAm72kMYJYcBv9a0X_npXDR/view?usp=share_link)

## Integrantes do grupo
2022132020 - Mestrado - Breno Aguiar Krohling

2021231578 - Mestrado - Lucas Miguel Tassis

2022241702 - Doutorado - Vitor Fontana Zanotelli

## Introdução

Nesse trabalho foi pedido a implementação do esquema de aprendizado federado utilizando *publish/subscribe* com fila de mensagens como modo de comunicação entre os componentes do sistema. O *broker* de mensagens utilizado foi o EMQX com utilização da biblioteca `paho` no Python. Todos os códigos foram escritos na linguagem Python.

## Organização do diretório e instruções para execução

### Organização do diretório
O diretório está organizado da seguinte forma:

`./client.py`: é o arquivo que inicia o cliente e conexão com broker/callback de mensagens.
`./server.py`: é o arquivo que inicia o servidor e conexão com broker/callback de mensagens.
`./trainer.py`: é o arquivo que contém a implementação da classe `Trainer`, que contém as implementações das operações feitas no `client.py`.
`./controller.py`: é o arquivo que contém a implementação da classe `Controller`, que contém as implementações das operações feitas no `server.py`.

### Instruções para execução
Para execução do servidor basta utilizar o seguinte comando:

`python server.py <broker_address> <min_clients> <clients_per_round> <num_rounds> <accuracy_threshold>`

Por exemplo, se quiser iniciar o servidor em um broker EMQX no localhost, com o mínimo de clientes necessário para iniciar o treinamento igual a 3, o número de clientes escolhidos por round igual a 2, e uma acurácia mínima de 97%, basta:

`python server.py localhost 3 2 5 0.97`

Para iniciar os clientes treinadores basta utilizar o seguinte comando:

`python client.py <broker_address>`

Por exemplo, no exemplo dado para o servidor, seria:

`python client.py localhost`

## Implementação

Primeiramente, vamos analisar a arquitetura utilizada pelos componentes. A figura abaixo apresenta a arquitetura utilizada no sistema, com especificação de quem faz o *publish* e o *subscribe* em cada uma das filas:

<img src="figs/queuediagram.png" width="800"/>

Notamos que temos dois agentes principais: *client* e *server*. Como especificado, o *client* é o responsável por ser o "treinador" durante o aprendizado federado. Já o *server* é o responsável por agregar os pesos e controlar os rounds (escolha de treinadores do round, etc). Todas as mensagens passadas para a filas foram serializadas no formato JSON. Como falado anteriormente, a lógica das operações do *client* e *server* são implementadas no código pelas classes *Trainer* e *Controller*, respectivamente.

O fluxo de treinamento implementado é o seguinte: 

Primeiramente, deve-se conectar o *server*, que ao inicializar o processo, faz *subscribe* nas filas **registerQueue**, **preAggQueue** e **metricsQueue**. Uma vez que o *server* está funcionando, podemos começar a inicializar os treinadores. Ao inicializar cada *client* faz *subscribe* nas filas **selectionQueue**, **posAggQueue** e **stopQueue**. Ao incializar os clientes, também é feito o *sampling* de sua base local para treinamento dos modelos. É feito um *sampling* aleatório de `10000 < num_samples < 20000` na base MNIST para servir como sua base.  Note que esse processo acaba permitindo que mais de um cliente tenha exemplos repetidos, mas como o tratamento disso não era interessante para/no escopo desse trabalho em específico, foi utilizado dessa forma.

Quando cada client inicializa, ele também faz a primeira publicação de mensagem, que é a mensagem `{'id' : int}` na fila **registerQueue**, fazendo seu registro na *pool* de treinadores do *server*, que ao receber a mensagem, adiciona cada cliente a sua lista de clientes. Uma vez que o número mínimo de clientes passado ao servidor é atingido, o treinamento é inicializado. O *server*, ao atingir o número mínimo de clientes, faz uma escolha aleatória do número mínimo de clientes e envia mensagens `{'id': int, 'selected' : bool}` para a **selectionQueue**. Todos os clientes recebem todas as mensagens e fazem um *parsing* da mensagem por seu `id`. Os clientes escolhidos iniciam o treinamento em sua base local, e os que não são escolhidos ficam esperando. No fim do treinamento, os clientes escolhidos publicam a mensagem `{'id' : int, 'weights' : list, 'num_samples' : int}` na fila **preAggQueue**. Note que para serializar os pesos, que inicialmente são organizados em uma lista de `np.array` , é necessário fazer uma transformação para uma lista de listas, que depois é desfeita no servidor para cálculo do *Federated Avg*. Uma vez que o servidor recebe todos os pesos ele faz sua agregação e envia de volta para todos os clientes (até os que não treinaram). Esse envio é feito pela mensagem `{'weights' : list}` na fila **posAggQueue**. Os clientes recebem e fazem a atualização dos seus pesos locais. Ao atualizar, cada um dos clientes faz a validação dos novos pesos em sua base de teste local (que nesse trabalho são os 10k já separados pela base MNIST em todos os clientes), e envia a mensagem `{'id' : int, 'accuracy' : float}` na fila **metricsQueue**. O servidor, ao receber todas as acurácias, computa sua média e verifica se já chegou no threshold escolhido no início do treinamento, caso tenha passado o threshold, ele envia uma mensagem `{'stop' : bool}` para a fila **stopQueue **indicando para os clientes terminarem o processo. Caso contrário, um novo round é inicializado, e o processo é repetido. Caso o modelo nunca alcance o threshold de acurácia, ele irá parar com a mesma mensagem ao chegar no número máximo de rounds.

No final do treinamento também é gerado um plot com a acurácia ao longo dos rounds!

## Exemplo de experimento e resultado

Para experimentar, utilizamos alguns setups diferentes como no laboratório 2 utilizando a biblioteca `flower` . Para exemplificar iremos mostrar experimentos com número de rounds igual 10 (e sem threshold de acurácia, para que sejam feito todos os rounds). Foram utilizados 3 clientes e cada modelo treinou 10 épocas. As figuras abaixo apresentam os resultados obtidos.

<img src="figs/simulation-rounds=10.png" width="800"/>

Pode-se observar que o modelo chegou em uma acurácia ~0.98 no segundo round. Como a base MNIST é uma base *toy*, é possível obter resultados com um menor número de rounds nela, como analisado no laboratório 2. Para comparação, a figura abaixo apresenta o plot para 10 rounds utilizando o `flower`:

<img src="figs/flower-simulation-rounds=10.png" width="800"/>

Notamos que o modelo `flower` obteve um resultado melhor no primeiro round. Mas esse primeiro resultado pior pode ter sido por conta de alguma diferença de *sampling* dos dados de treinamento/ruído no treinamento da rede (em outros testes o primeiro round deu um resultado melhor, e em alguns outros semelhante ao apresentado). E também, a convergência foi mais rápida que a da biblioteca `flower`, mas que novamente pode ser só parte da aleatoriedade no treinamento da rede/*sampling* dos dados de treinamento ao longo dos rounds. Outro ponto é que no laboratório 2 não foi utilizado todos os 10k exemplos de teste do MNIST para validação, e sim uma parte dele, logo, isso também pode ter influênciado a melhor acurácia no round 1. 

De qualquer forma, o fato mais importante é que houve aprendizado e convergência em nossa implementação e com esses resultados acreditamos que a performance foi satisfatória no problema.

## Conclusão

Nesse trabalho foi pedido a implementação do treinamento federado utilizando o modelo *publish/subscribe* com fila de mensagens, utilizando o broker EMQX. A implementação foi apresentada nesse documento e os experimentos apresentaram um resultado satisfatório e comparado ao da biblioteca `flower`.