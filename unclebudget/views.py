from decimal import Decimal

from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.generic import *

from .models import *
from .loader import load_entries


def account_detail(request, pk):
    accounts = Account.objects.filter(user=request.user)
    try:
        account = accounts.get(pk=pk)
    except Account.DoesNotExist:
        raise Http404()

    return render(request, 'unclebudget/account_detail.html', {
        'account': account,
        'accounts': accounts,
    })


class EnvelopeDetail(DetailView):
    template_name = 'unclebudget/envelope_detail.html'
    def get_queryset(self):
        return Envelope.objects.filter(
            user=self.request.user, pk=self.kwargs['pk'],
        )


def summary(request):
    accounts = Account.objects.filter(user=request.user)
    envelopes = Envelope.objects.filter(user=request.user)
    return render(request, 'unclebudget/summary.html', {
        'accounts': accounts,
        'envelopes': envelopes,
    })


def process(request):
    receipt = Receipt.objects.filter(
        ~Q(balance=0),
        user=request.user,
    ).order_by('date').first()

    if not receipt:
        return redirect('summary')

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

    return render(request, 'unclebudget/receipt.html', {
        'receipt': receipt,
        'accounts': accounts,
        'envelopes': envelopes,
    })


def upload(request):
    entries = None
    no_new_entries = False

    if request.method == 'POST':
        account = get_object_or_404(Account, user=request.user, pk=request.POST['account'])
        text = request.FILES['csv'].read()
        load, entries = load_entries(account, text)
        if not entries:
            no_new_entries = True
            load.delete()

    accounts = Account.objects.filter(user=request.user)
    loads = Load.objects.filter(user=request.user)

    return render(request, 'unclebudget/upload.html', {
        'accounts': accounts,
        'loads': loads,
        'entries': entries,
        'no_new_entries': no_new_entries,
    })


def toggle_theme(request):
    settings = Settings.objects.for_user(request.user)
    settings.dark_mode = not settings.dark_mode
    settings.save()
    return redirect(request.META.get('HTTP_REFERER', reverse('summary')))
