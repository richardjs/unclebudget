from django.contrib import admin

from .models import *

admin.site.register(Account)
admin.site.register(Entry)
admin.site.register(Envelope)
admin.site.register(Item)
admin.site.register(Load)
admin.site.register(Note)
admin.site.register(Template)
admin.site.register(TemplateItem)
admin.site.register(UserData)
