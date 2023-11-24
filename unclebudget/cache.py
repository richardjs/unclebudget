from django.core.cache import cache

from . import models


ACCOUNT_BALANCE_KEY = "account:{account.pk}:balance"
ENVELOPE_BALANCE_KEY = "envelope:{envelope.pk}:balance"
ITEM_DATE_KEY = "item:{item.pk}:date"
UNBALANCED_ENTRIES_KEY = "user:{user.pk}:unbalanced_entries"


def get_account_balance(account):
    cache_key = ACCOUNT_BALANCE_KEY.format(account=account)
    balance = cache.get(cache_key)

    if balance == None:
        balance = account.balance
        cache.set(cache_key, balance, None)

    return balance


def clear_account_balance(account):
    cache_key = ACCOUNT_BALANCE_KEY.format(account=account)
    cache.delete(cache_key)


def get_envelope_balance(envelope):
    cache_key = ENVELOPE_BALANCE_KEY.format(envelope=envelope)
    balance = cache.get(cache_key)

    if balance == None:
        balance = envelope.balance
        cache.set(cache_key, balance, None)

    return balance


def clear_envelope_balance(envelope):
    cache_key = ENVELOPE_BALANCE_KEY.format(envelope=envelope)
    cache.delete(cache_key)


def get_item_date(item):
    cache_key = ITEM_DATE_KEY.format(item=item)
    date = cache.get(cache_key)

    if date == None:
        date = item.entry.date
        cache.set(cache_key, date, None)

    return date


def clear_item_date(item):
    cache_key = ITEM_DATE_KEY.format(item=item)
    cache.delete(cache_key)


def get_unbalanced_entries(user):
    cache_key = UNBALANCED_ENTRIES_KEY.format(user=user)
    unbalanced = cache.get(cache_key)

    if unbalanced == None:
        unbalanced = set(
            [e for e in models.Entry.objects.filter(user=user) if not e.balanced]
        )
        cache.set(cache_key, unbalanced, None)

    return unbalanced


def set_unbalanced_entries(user, entries):
    cache_key = UNBALANCED_ENTRIES_KEY.format(user=user)
    cache.set(cache_key, entries, None)
