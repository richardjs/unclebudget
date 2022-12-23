from django.views.generic import *
from django.http import HttpResponse
from django.shortcuts import redirect, render

from unclebudget.models import *


class AccountDetail(DetailView):
    model = Account


class AccountList(ListView):
    model = Account


class EnvelopeDetail(DetailView):
    model = Envelope


class EnvelopeList(ListView):
    model = Envelope


def process(request):
    receipt = Receipt.objects.filter(
        user=request.user,
        balanced=False
    ).order_by('date').first()

    if not receipt:
        return HttpResponse('All receipts balanced')

    return redirect('receipt', receipt.pk)


def receipt(request, pk):
    receipt = Receipt.objects.get(user=request.user, pk=pk)
    accounts = Account.objects.filter(user=request.user)
    envelopes = Envelope.objects.filter(user=request.user)

    return render(request, 'unclebudget/process.html', {
        'receipt': receipt,
        'accounts': accounts,
        'envelopes': envelopes,
    })
