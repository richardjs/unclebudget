from django.contrib import admin

from .models import *

admin.site.register(Account)
admin.site.register(Charge)
admin.site.register(Envelope)
admin.site.register(Item)
admin.site.register(Load)
admin.site.register(Receipt)
