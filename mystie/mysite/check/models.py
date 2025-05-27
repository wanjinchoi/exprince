from django.db import models

# Create your models here.

class Company(models.Model):
        #사번
        code = models.CharField(max_length=20, primary_key=True,name='code')
        #이름
        name = models.CharField(max_length=20,name='name')
        last_update = models.DateField()

        def __str__(self):
                return self.code,self.name