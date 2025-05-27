import os


def main(dest_path):
    file_list = os.listdir(dest_path)
    for i in file_list:
        os.remove(dest_path+"\\"+i)


if __name__ == '__main__':
    main(r"C:\Users\Myeongkook Park\PycharmProjects\softpackPython\excel\csv_file")