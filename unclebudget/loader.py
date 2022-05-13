from importlib import import_module

from django.conf import settings


class LoadException(Exception):
    pass


def load(file):
    if isinstance(file, str):
        file = open(file)

    charges = None
    with file:
        text = file.read()
        for loader in settings.UNCLEBUDGET_LOADERS:
            file.seek(0)
            try:
                charges = import_module(loader).load(file)
            except Exception as e:
                pass

    if charges == None:
        raise LoadException(f'No loaders successful for file {file}')
    
    # TODO actual account
    account = Account(name='dummy')
    account.save()
    load.save()
    load = Load(loader=loader, text=text)
    for charge in charges:
        charge.account = account
        charge.load = load
        charge.save()
