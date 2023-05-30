# Laboratório 6 - Eleição e Coordenação Distribuída

[Link do video]()

## Integrantes do grupo

2022132020 - Mestrado - Breno Aguiar Krohling

2021231578 - Mestrado - Lucas Miguel Tassis

2022241702 - Doutorado - Vitor Fontana Zanotelli

## Introdução

Nesse trabalho, foi pedido a implementação de um protótipo similar a um minerador de criptomoedas utilizando um sistema de comunicação indireta por meio de um *middleware Publish/Subscribe* utilizando fila de mensagens. O broker utilizado foi o EMQX. A implementação dos clientes foram feitas utilizando a linguagem Python e com o auxílio da biblioteca `paho`. Nesse laboratório também foi pedido para implementar eleição e coordenação distribuída entre os mineradores, para escolha do líder (coordenador) e mineradores.

## Organização do diretório e instruções para execução

### Organização do diretório

Todos os códigos implementados estão disponibilizados no diretório `lab6/`. O arquivo `client.py` possui a implementação dos clientes mineradores/líder que serão executados. O arquivo `miner.py` possui a implementação da classe `Miner`,  que possui a implementação da lógica de coordenação e mineração, para quem for escolhido como líder/minerador.

### Instruções para execução

Para execução dos clientes basta utilizar o comando `python client.py <broker_addr> <num_clients>`, onde `<broker_addr>` é o endereço do broker, e `<num_clients>` é o número de clientes que irão ser executados durante a rodada. Por exemplo, se quisermos fazer uma simulação com 3 clientes e utilizando o broker público disponibilizado pelo EMQX, basta executar `python client.py broker.emqx.io 3`.

## Implementação



## Comentários sobre experimentos e resultados

