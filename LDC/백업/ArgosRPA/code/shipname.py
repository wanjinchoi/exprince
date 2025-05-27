import openpyxl

def main(shipname):

    if len(shipname)>25:
        sshipname = shipname[0:24]
        return sshipname
    else:
        return shipname






if __name__ == "__main__":
    main('Zenith Gemi Isletmeciligi A.S. (AS AGENTONLY)')

