from importlib import import_module
from io import StringIO

from django.conf import settings

from .models import Entry, Load


class LoadException(Exception):
    pass


def load(account, text):
    charges = None

    for loader in settings.UNCLEBUDGET_LOADERS:
        try:
            charges = import_module(loader).load(StringIO(text))
            break
        except Exception:
            pass

    if charges == None:
        raise LoadException(f'No loaders successful')
    
    load = Load(loader=loader, text=text, user=account.user)
    load.save()
    for charge in charges:
        charge.account = account
        charge.load = load
        charge.user = account.user
        charge.save()

    return charges
