from collections import OrderedDict
from datetime import datetime
from decimal import Decimal
from operator import attrgetter

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView as auth_LoginView
from django.db.models import Q
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.generic import CreateView

from . import cache, stats
from .forms import EnvelopeForm
from .models import *
from .loader import load_entries


@login_required
def account_detail(request, pk):
    accounts = Account.objects.filter(user=request.user)
    try:
        account = accounts.get(pk=pk)
    except Account.DoesNotExist:
        raise Http404()

    entries = account.entry_set.all()

    accounts_balance = sum([cache.get_account_balance(account) for account in accounts])

    ongoing_balance = cache.get_account_balance(account)
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
def all(request):
    accounts = Account.objects.filter(user=request.user)
    envelopes = Envelope.objects.filter(user=request.user)

    # TODO we should probably cache this somewhere
    # (but we also want to make sure it's actually useful data)
    accounts_balance = sum([cache.get_account_balance(account) for account in accounts])
    envelopes_balance = sum(
        [cache.get_envelope_balance(envelope) for envelope in envelopes]
    )

    to_process = cache.get_unbalanced_entries(request.user)

    return render(
        request,
        "unclebudget/all.html",
        {
            "accounts": accounts,
            "accounts_balance": accounts_balance,
            "envelopes": envelopes,
            "envelopes_balance": envelopes_balance,
            "to_process": to_process,
        },
    )


@login_required
def entry_detail(request, pk):
    entry = get_object_or_404(Entry, user=request.user, pk=pk)

    existing_item_ids = set([item.id for item in entry.item_set.all()])

    to_split_amount = entry.amount
    to_split_item_ids = set()

    if request.method == "POST":
        for item_id, envelope_id, amount, description in zip(
            request.POST.getlist("item_id"),
            request.POST.getlist("item_envelope"),
            request.POST.getlist("item_amount"),
            request.POST.getlist("item_description"),
        ):
            if item_id:
                item = get_object_or_404(Item, user=request.user, pk=item_id)
                existing_item_ids.remove(int(item_id))
            else:
                item = Item()

            if not envelope_id:
                if item_id:
                    item = get_object_or_404(Item, pk=item_id, user=request.user)
                    item.delete()
                continue

            envelope = get_object_or_404(Envelope, user=request.user, pk=envelope_id)

            item.description = description
            item.entry = entry
            item.envelope = envelope
            item.user = request.user

            if amount:
                item.amount = Decimal(amount)
                to_split_amount -= item.amount
            else:
                # Temporary amount, to be updated below
                item.amount = 0.01
                # Save it here so we have an ID
                item.save()
                to_split_item_ids.add(item.id)

            item.save()

        # If there are any existing items we didn't see in the above form
        # loop, we should delete them (because the user deleted them)
        for item_id in existing_item_ids:
            Item.objects.get(pk=item_id).delete()

        for item_id in to_split_item_ids:
            Item.objects.filter(pk=item_id).update(
                amount=to_split_amount / len(to_split_item_ids)
            )

        # Save entry to update cache
        entry.save()

        if "quick-advance" in request.POST and entry.balance == 0:
            return redirect(reverse("process"))

    envelopes = Envelope.objects.filter(user=request.user)

    to_process = list(cache.get_unbalanced_entries(request.user))
    to_process.sort(key=attrgetter("date"))
    skipped = cache.get_skipped_entries(user=request.user)
    if to_process:
        while to_process[0] in skipped:
            to_process.append(to_process.pop(0))

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
def entry_skip(request, pk):
    entry = get_object_or_404(Entry, user=request.user, pk=pk)
    cache.add_skipped_entry(request.user, entry)
    return redirect(reverse("process"))


@login_required
def envelope_detail(request, pk):
    envelopes = Envelope.objects.filter(user=request.user)
    try:
        envelope = envelopes.get(pk=pk)
    except Envelope.DoesNotExist:
        raise Http404()

    envelopes_balance = sum(
        [cache.get_envelope_balance(envelope) for envelope in envelopes]
    )

    return render(
        request,
        "unclebudget/envelope_detail.html",
        {
            "envelope": envelope,
            "envelopes": envelopes,
            "envelopes_balance": envelopes_balance,
        },
    )


@login_required
def expect(request):
    if request.method == "POST":
        account = get_object_or_404(
            Account, user=request.user, pk=request.POST["account_id"]
        )

        entry = Entry.objects.create(
            account=account,
            amount=Decimal(request.POST["amount"]),
            date=datetime.now(),
            description=request.POST["description"],
            expected=True,
            user=request.user,
        )

        split_amount = entry.amount
        split_n = 0

        for envelope_id, amount in zip(
            request.POST.getlist("item_envelope"), request.POST.getlist("item_amount")
        ):
            if not envelope_id:
                continue

            if amount:
                amount = Decimal(amount)
                split_amount -= amount
            else:
                split_n += 1

        for envelope_id, amount, description in zip(
            request.POST.getlist("item_envelope"),
            request.POST.getlist("item_amount"),
            request.POST.getlist("item_description"),
        ):
            if not envelope_id:
                continue

            envelope = get_object_or_404(Envelope, user=request.user, pk=envelope_id)

            if amount:
                amount = Decimal(amount)
            else:
                # TODO what if this doesn't divide evenly?
                amount = split_amount / split_n

            Item.objects.create(
                amount=amount,
                description=description,
                envelope=envelope,
                entry=entry,
                user=request.user,
            )

        return HttpResponse("Expected entry created!")

    accounts = Account.objects.filter(user=request.user)
    envelopes = Envelope.objects.filter(user=request.user)

    return render(
        request,
        "unclebudget/expect.html",
        {
            "accounts": accounts,
            "envelopes": envelopes,
        },
    )


class EnvelopeCreateView(CreateView, LoginRequiredMixin):
    form_class = EnvelopeForm
    model = Envelope

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class LoginView(auth_LoginView):
    """Custom LoginView used to support UNCLEBUDGET_SINGLE_USER"""

    def dispatch(self, request, *args, **kwargs):
        if settings.UNCLEBUDGET_SINGLE_USER:
            single_user = User.objects.get(pk=settings.UNCLEBUDGET_SINGLE_USER)
            login(request, single_user)
            return HttpResponseRedirect(self.get_success_url())

        return super().dispatch(request, *args, **kwargs)


@login_required
def process(request):
    to_process = list(cache.get_unbalanced_entries(request.user))
    to_process.sort(key=attrgetter("date"))

    if not to_process:
        return redirect("summary")

    skipped = cache.get_skipped_entries(request.user)
    for entry in to_process:
        if entry in skipped:
            continue

        return redirect("entry-detail", entry.pk)

    # If we've skipped every entry, act like nothing is skipped
    cache.clear_skipped_entries(request.user)
    return redirect("entry-detail", to_process[0].pk)


@login_required
def report_income(request):
    transfer_envelope = request.user.userdata.transfer_envelope

    years = OrderedDict()
    for entry in Entry.objects.filter(
        user=request.user,
        amount__lt=0,
    ).order_by("-date"):
        if entry.item_set.first().envelope == transfer_envelope:
            continue

        if entry.date.year not in years:
            years[entry.date.year] = OrderedDict()

        if entry.date.month not in years[entry.date.year]:
            years[entry.date.year][entry.date.month] = []

        years[entry.date.year][entry.date.month].append(entry)

    return render(
        request,
        "unclebudget/report-income.html",
        {
            "years": years,
        },
    )


@login_required
def report(request):
    from django.http import HttpResponse

    envelope_monthly_expenses = stats.envelope_monthly_expenses(request.user)

    return render(request, "unclebudget/report.html", locals())


@login_required
def summary(request):
    envelopes = Envelope.objects.filter(user=request.user)
    pinned = envelopes.filter(user=request.user, pinned=True)
    negative = [
        envelope for envelope in envelopes if cache.get_envelope_balance(envelope) < 0
    ]

    to_process = cache.get_unbalanced_entries(request.user)

    return render(
        request,
        "unclebudget/summary.html",
        {
            "pinned": pinned,
            "negative": negative,
            "to_process": to_process,
        },
    )


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
