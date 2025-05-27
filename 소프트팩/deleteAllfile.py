import os


def main(path):
    listdir = os.listdir(path)
    for i in listdir:
        os.remove(path + "\\" + i)
if __name__ == '__main__':
    main()