# REDONDOS

Jogo Pygame multiplayer para até 4 jogadores em LAN/Radmin VPN.

## Recursos

- Até 4 jogadores conectando no mesmo servidor por IP.
- Arena 2D com plataformas.
- Tiros com física e queda de bala.
- Rodadas: o último sobrevivente vence.
- Depois de cada rodada, os perdedores escolhem 1 entre 3 cartas aleatórias.
- Cartas dão buffs permanentes durante a partida: velocidade, dano, pulo, cadência, multishot, escudo, menos queda de bala e ricochete.

## Instalação

1. Instale Python 3.10+.
2. Instale o Pygame:

```bash
pip install -r requirements.txt
```

## Como jogar localmente

Abra um terminal na pasta do jogo e rode:

```bash
python server.py
```

Depois, em cada computador/janela de jogador:

```bash
python client.py 127.0.0.1 NomeDoJogador
```

Para jogar no mesmo PC, abra até 4 clientes usando nomes diferentes.

## Como jogar por Radmin VPN

1. Todos entram na mesma rede do Radmin VPN.
2. O host abre o servidor:

```bash
python server.py
```

3. Os outros jogadores pegam o IP Radmin do host e entram assim:

```bash
python client.py IP_DO_HOST NomeDoJogador
```

Exemplo:

```bash
python client.py 26.123.45.67 Henrique
```

## Controles

- A/D ou setas: mover.
- W, espaço ou seta para cima: pular.
- Mouse: mirar.
- Botão esquerdo do mouse: atirar.
- Na tela de cartas: clique na carta ou pressione 1, 2 ou 3.

## Observações

- Porta padrão: `50007`.
- Se não conectar, libere o Python/porta no firewall do Windows.
- O servidor simula o jogo, então todos os clientes recebem o mesmo estado.
