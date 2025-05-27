import cv2
import chardet as ch

file =r'C:\Users\vivans\Desktop\test\何でも.jpg'
print(ch.detect((file.encode())))




file2= file.decode("cp949")
image = cv2.imread(file2)