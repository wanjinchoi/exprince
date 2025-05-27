import datetime


def main(dt: str):
    """
    Converting string type date to unix time-stamp
    dt: 2021-03-26 11:30:20
    return 1616725820.0
    """
    asd
    d = datetime.datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
    return d.timestamp()
