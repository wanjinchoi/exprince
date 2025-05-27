from openpyxl import load_workbook


def main(input_path, sheet):
    wb = load_workbook(input_path)
    for z in range(len(wb[sheet]['B'])-1):
        wb[sheet]['A'+str(z+2)].value = z+1
    wb.save(input_path)


if __name__ == '__main__':
    main()