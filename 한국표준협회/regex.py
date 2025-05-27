import re


def main(str_):
    find = str_.find('(구매자명 :')
    p = re.compile("[\\d]+")
    first = str_[find+8:-1].split(",")[0]
    second = p.findall(str_[find + 7:-1].split(",")[1])[0]
    result = first + ',' + second
    print(result)


if __name__ == '__main__':
    main()