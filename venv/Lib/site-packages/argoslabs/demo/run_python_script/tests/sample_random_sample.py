import random

def main(*args, num='4'):
    """
    -a A -a B -a C -a D -a E -a F -k num=2
    Converting string type date to unix time-stamp
    args: ('A', 'B', 'C', 'D', 'E', 'F')
    return ['A', 'C', 'B', 'D']  # random
    """
    d = random.sample(args, int(num))
    return d
