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
    # TODO this can be way optimized (e.g. cache balanced and date,
    # and do it all on DB level)

    receipt = None
    for r in Receipt.objects.filter(user=request.user):
        if r.balanced:
            continue

        if not receipt or receipt.date > r.date:
            receipt = r

    return render(request, 'unclebudget/process.html', locals())
