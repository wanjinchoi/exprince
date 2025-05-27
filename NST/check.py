import datetime
import os

def main(checklist):
   ####2024/06/27

   # 경민 폴더
   directory = r"C:\work\NST\경민"
   if os.path.exists(directory):
       files = os.listdir(directory)
       for file in files:
           if file.endswith('.xls') or file.endswith('.xlsx'):
               return 1

   # 영신 폴더
   directory = r"C:\work\NST\영신"
   if os.path.exists(directory):
       files = os.listdir(directory)
       for file in files:
           if file.endswith('.xls') or file.endswith('.xlsx'):
               return 2

   # 청우 폴더
   directory = r"C:\work\NST\청우"
   if os.path.exists(directory):
       files = os.listdir(directory)
       for file in files:
           if file.endswith('.xls') or file.endswith('.xlsx'):
               return 3

   # 태양 폴더
   directory = r"C:\work\NST\태양"
   if os.path.exists(directory):
       files = os.listdir(directory)
       for file in files:
           if file.endswith('.xls') or file.endswith('.xlsx'):
               return 4

   # 모든 폴더에 파일이 없는 경우
   return 5

if __name__ == "__main__":
        main('aa')