import re



def main(checklist):
    pattern = r'(\d+-\d+)'
    match = re.search(pattern, checklist)

    if match:
        b = match.group()
        print(b)
    else:
        b = 'no'
        print(b)



if __name__ == "__main__":
    main()


