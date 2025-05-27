from django.contrib import admin

from .models import Company

# Register your models here.


##찾기 클래스
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('code','name')
    search_fields = ['code']

admin.site.register(Company,CompanyAdmin)
