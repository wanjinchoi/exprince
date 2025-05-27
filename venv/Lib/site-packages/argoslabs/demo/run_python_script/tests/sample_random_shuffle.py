import random


def main(*args):
    """
    -a A -a B -a C -a D -a E -a F
    Converting string type date to unix time-stamp
    args: ('A', 'B', 'C', 'D', 'E', 'F')
    return ['B', 'E', 'F', 'D', 'C', 'A']
    """
    deck = list(args)
    random.shuffle(deck)
    return deck
