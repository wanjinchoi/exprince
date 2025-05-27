import os

def main(checklist):
    test = checklist
    if test:
        print('A','B')
    else:
        print('C',"D")
if __name__ == "__main__":
    main('aa')


print(main(r'{checklist}'))