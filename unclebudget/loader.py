from importlib import import_module
from io import StringIO

from django.conf import settings

from .models import *


class LoadException(Exception):
    pass


def load_entries(account, text):
    user_data = UserData.objects.for_user(account.user)

    charges = None

    if type(text) == bytes:
        text = text.decode()

    for loader in settings.UNCLEBUDGET_LOADERS:
        try:
            charges = import_module(loader).load(StringIO(text))
            break
        except Exception:
            pass

    if charges == None:
        raise LoadException(f"No loaders successful")

    load = Load(loader=loader, text=text, user=account.user)
    load.save()

    entries = []
    for charge in charges:
        if charge.date < account.start_date:
            continue

        # Look for expected entries
        expected = Entry.objects.filter(
            account=account,
            amount=charge.amount,
            expected=True,
        ).first()
        if expected:
            expected.date = charge.date
            expected.description = charge.description
            expected.expected = False
            expected.load = load
            expected.save()
            continue

        # Look for duplicates
        duplicate = False
        for entry in Entry.objects.filter(
            account=account,
            date=charge.date,
            description=charge.description,
        ).all():
            if entry.amount == charge.amount:
                duplicate = True
        if duplicate:
            continue

        charge.account = account
        charge.load = load
        charge.user = account.user
        charge.save()

        # Look for small change
        if user_data.small_change_envelope:
            if charge.amount < user_data.small_change_threshold:
                Item.objects.create(
                    amount=charge.amount,
                    envelope=user_data.small_change_envelope,
                    entry=charge,
                    user=account.user,
                )

        entries.append(charge)

    return load, entries
