from django.views.generic import *
from django.http import HttpResponse
from django.shortcuts import render

from unclebudget.models import *


class AccountDetail(DetailView):
    model = Account


class AccountList(ListView):
    model = Account


class EnvelopeDetail(DetailView):
    model = Envelope


class EnvelopeList(ListView):
    model = Envelope


def process_receipt(request):
    receipt = Receipt.objects.filter(
        user=request.user,
        balanced=False
    ).order_by('date').first()

    if not receipt:
        return HttpResponse('All receipts balanced')

    return render(request, 'unclebudget/process.html', locals())
