import random

def main(*args):
    """
    -a A -a B -a C -a D -a E -a F -k num=2
    Converting string type date to unix time-stamp
    args: ('A', 'B', 'C', 'D', 'E', 'F')
    return 'A'  # random
    """
    deck = list(args)
    d = random.choice(deck)
    return d
