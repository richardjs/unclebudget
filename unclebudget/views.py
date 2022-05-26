from django.views.generic import *
from django.http import HttpResponse

from unclebudget.models import *


class AccountDetail(DetailView):
    model = Account


class AccountList(ListView):
    model = Account


class EnvelopeDetail(DetailView):
    model = Envelope


class EnvelopeList(ListView):
    model = Envelope
