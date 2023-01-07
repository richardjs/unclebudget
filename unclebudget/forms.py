from django.forms import ModelForm, TextInput

from .models import *


class EnvelopeForm(ModelForm):
    class Meta:
        model = Envelope
        fields = ('name', 'description')
        widgets = {
            'name': TextInput(),
            'description': TextInput(),
        }
