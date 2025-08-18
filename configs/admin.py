from django.contrib import admin
from .models import TDS, Component


# Register your models here.

class ComponentAdmin(admin.ModelAdmin):
    list_display = ('component_name', 'operation')


admin.site.register(Component, ComponentAdmin)
admin.site.register(TDS)
