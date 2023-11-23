from django.core.cache import cache

from . import models


UNBALANCED_ENTRIES_KEY = "user:{user.pk}:unbalanced_entries"


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
