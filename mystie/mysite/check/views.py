import openpyxl
from django.shortcuts import render

# 엑셀을 생성 및 행 추가 (여기서는 행 단위 추가만 함 열만 추가하는건 검색 바람 )
import openpyxl # 엑셀을 만드는 api (엑셀 미설치 시에도 동작)
from io import BytesIO # 엑셀 파일을 전송 할 수 있도록 바이트 배열로 변환

# Create your views here.
from django.http import HttpResponse
#edit
from .models import Company

def index(request):
    #edit
    uzi_list = Company.objects.all()
    context = {'uzi_list': uzi_list}

    wb = openpyxl.load_workbook('C:\\Users\\vivans\\Desktop\\제이티통신\\exceldata-fail.xlsx') # 불러오기
    ws = wb.active  # 엑셀 활성화
    excelfile = BytesIO()  # 바이트 배열 생성



    return render(request, 'check/index.html', context)
