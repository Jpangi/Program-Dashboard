from django.contrib import admin
from .models import Program, ControlAccount, WorkPackage, EVMData, EVMSnapshot, CSVupload

# Register your models here.
admin.site.register(Program)
admin.site.register(ControlAccount)
admin.site.register(WorkPackage)
admin.site.register(EVMData)
admin.site.register(EVMSnapshot)
admin.site.register(CSVupload)