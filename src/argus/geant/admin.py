from django.contrib import admin
from .models import EndpointEvent

class EndpointEventAdmin(admin.ModelAdmin):
    pass

admin.site.register(EndpointEvent, EndpointEventAdmin)
