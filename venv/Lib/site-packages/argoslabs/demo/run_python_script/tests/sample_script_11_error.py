def main(a, b, c):
    try:
        a + b + int(c)
    except Exception as e:
        raise
    return a, b, c
