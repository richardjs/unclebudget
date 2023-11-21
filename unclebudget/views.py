from decimal import Decimal

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView as auth_LoginView
from django.db.models import Q
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.generic import CreateView

from .forms import EnvelopeForm
from .models import *
from .loader import load_entries


class LoginView(auth_LoginView):
    """Custom LoginView used to support UNCLEBUDGET_SINGLE_USER"""

    def dispatch(self, request, *args, **kwargs):
        if settings.UNCLEBUDGET_SINGLE_USER:
            single_user = User.objects.get(pk=settings.UNCLEBUDGET_SINGLE_USER)
            login(request, single_user)
            return HttpResponseRedirect(self.get_success_url())

        return super().dispatch(request, *args, **kwargs)


@login_required
def account_detail(request, pk):
    accounts = Account.objects.filter(user=request.user)
    try:
        account = accounts.get(pk=pk)
    except Account.DoesNotExist:
        raise Http404()

    entries = account.entry_set.all()

    accounts_balance = sum([account.balance for account in accounts])

    ongoing_balance = account.balance
    for entry in entries:
        entry.ongoing_balance = ongoing_balance
        ongoing_balance += entry.amount

    return render(
        request,
        "unclebudget/account_detail.html",
        {
            "account": account,
            "accounts": accounts,
            "accounts_balance": accounts_balance,
            "entries": entries,
        },
    )


@login_required
def entry_detail(request, pk):
    entry = get_object_or_404(Entry, user=request.user, pk=pk)

    if request.method == "POST":
        for item_id, envelope_id, amount, description in zip(
            request.POST.getlist("item_id"),
            request.POST.getlist("item_envelope"),
            request.POST.getlist("item_amount"),
            request.POST.getlist("item_description"),
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

            if amount:
                item.amount = Decimal(amount)
            else:
                item.amount = entry.balance

            item.description = description
            item.entry = entry
            item.envelope = envelope
            item.user = request.user
            item.save()

        if "quick-advance" in request.POST and entry.balance == 0:
            return redirect(reverse("process"))

    envelopes = Envelope.objects.filter(user=request.user)

    to_process = [
        entry
        for entry in Entry.objects.filter(user=request.user).order_by("date")
        if not entry.balanced
    ]

    return render(
        request,
        "unclebudget/entry_detail.html",
        {
            "entry": entry,
            "envelopes": envelopes,
            "to_process": to_process,
        },
    )


@login_required
def envelope_detail(request, pk):
    envelopes = Envelope.objects.filter(user=request.user)
    try:
        envelope = envelopes.get(pk=pk)
    except Envelope.DoesNotExist:
        raise Http404()

    envelopes_balance = sum([envelope.balance for envelope in envelopes])

    return render(
        request,
        "unclebudget/envelope_detail.html",
        {
            "envelope": envelope,
            "envelopes": envelopes,
            "envelopes_balance": envelopes_balance,
        },
    )


class EnvelopeCreateView(CreateView, LoginRequiredMixin):
    form_class = EnvelopeForm
    model = Envelope

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


@login_required
def summary(request):
    accounts = Account.objects.filter(user=request.user)
    envelopes = Envelope.objects.filter(user=request.user)

    # TODO we should probably cache this somewhere
    # (but we also want to make sure it's actually useful data)
    accounts_balance = sum([account.balance for account in accounts])
    envelopes_balance = sum([envelope.balance for envelope in envelopes])

    # TODO this is a pretty heavy calculation
    # move it more into SQL, and/or cache it
    to_process = [
        entry
        for entry in Entry.objects.filter(user=request.user).order_by("date")
        if not entry.balanced
    ]

    return render(
        request,
        "unclebudget/summary.html",
        {
            "accounts": accounts,
            "accounts_balance": accounts_balance,
            "envelopes": envelopes,
            "envelopes_balance": envelopes_balance,
            "to_process": to_process,
        },
    )


@login_required
def process(request):
    to_process = [
        entry
        for entry in Entry.objects.filter(user=request.user).order_by("date")
        if not entry.balanced
    ]

    if not to_process:
        return redirect("summary")

    return redirect("entry-detail", to_process[0].pk)


@login_required
def toggle_theme(request):
    settings = UserData.objects.for_user(request.user)
    settings.dark_mode = not settings.dark_mode
    settings.save()
    return redirect(request.META.get("HTTP_REFERER", reverse("summary")))


@login_required
def upload(request):
    entries = None
    no_new_entries = False

    if request.method == "POST":
        account = get_object_or_404(
            Account, user=request.user, pk=request.POST["account"]
        )
        text = request.FILES["csv"].read()
        load, entries = load_entries(account, text)
        if not entries:
            no_new_entries = True
            load.delete()

    accounts = Account.objects.filter(user=request.user)
    loads = Load.objects.filter(user=request.user)

    return render(
        request,
        "unclebudget/upload.html",
        {
            "accounts": accounts,
            "loads": loads,
            "entries": entries,
            "no_new_entries": no_new_entries,
        },
    )
