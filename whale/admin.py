from django.contrib import admin

# Register your models here.

from . models import Whale, EX
admin.site.register(Whale)
admin.site.register(EX)