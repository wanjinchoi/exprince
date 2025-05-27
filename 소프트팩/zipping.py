import os
import zipfile


def main():
    new_zips = zipfile.ZipFile(r'C:\Users\다현짱\Downloads\결과물\결과물.zip', 'w')
    
    for folder, subfolders, files in os.walk(r'C:\Users\다현짱\Downloads\결과물\\'):
        for file in files:
            new_zips.write(os.path.join(folder, file),
                           os.path.relpath(os.path.join(folder, file), r'C:\Users\다현짱\Downloads\결과물\\'),
                           compress_type=zipfile.ZIP_DEFLATED)
    new_zips.close()
    return 0


if __name__ == '__main__':
    main()