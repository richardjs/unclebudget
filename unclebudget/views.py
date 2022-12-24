from decimal import Decimal

from django.views.generic import *
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

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
    receipt = get_object_or_404(Receipt, user=request.user, pk=pk)

    if request.method == 'POST':
        for item_id, envelope_id, amount, description in zip(
            request.POST.getlist('item_id'),
            request.POST.getlist('item_envelope'),
            request.POST.getlist('item_amount'),
            request.POST.getlist('item_description'),
        ):
            if not envelope_id:
                if item_id:
                    item = get_object_or_404(Item, pk=item_id, user=request.user)
                    item.delete()
                continue

            envelope = get_object_or_404(Envelope, user=request.user, pk=envelope_id)

            if item_id:
                item = get_object_or_404(Item, user=request.user, pk=item_id)
            else:
                item = Item()

            item.amount = Decimal(amount)
            item.description = description
            item.envelope = envelope
            item.receipt = receipt
            item.user = request.user
            item.save()

    accounts = Account.objects.filter(user=request.user)
    envelopes = Envelope.objects.filter(user=request.user)

    return render(request, 'unclebudget/process.html', {
        'receipt': receipt,
        'accounts': accounts,
        'envelopes': envelopes,
    })
