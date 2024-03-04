from datetime import date, datetime, timedelta

from . import cache
from .models import *


# cmonth (continuous month) = year*12 + month
def date_to_cmonth(date):
    return (date.year * 12) + date.month


def cmonth_to_date(cmonth):
    return date(cmonth // 12, cmont % 12, 1)


def items_by_cmonth(envelope):
    beginning_of_time = UserData.objects.for_user(envelope.user).beginning_of_time

    cmonths = {
        cmonth: []
        for cmonth in range(
            date_to_cmonth(beginning_of_time), date_to_cmonth(datetime.now())
        )
    }

    for item in envelope.item_set.all():
        cmonth = date_to_cmonth(cache.get_item_date(item))

        # if this is false, cmonth is current month or before beginning of time
        if cmonth in cmonths:
            cmonths[cmonth].append(item)

    return cmonths


def month_diff(date1, date2):
    years = abs(date1.year - date2.year)
    months = abs(date1.month - date2.month)
    return years * 12 + months


def months_back(d, count):
    d -= timedelta(days=1)
    d = date(d.year, d.month, 1)

    if count > 1:
        return months_back(d, count - 1)
    return d


def expenses(items):
    return [item.amount for item in items if item.amount < 0]


def envelope_mean_expenses(user):
    envelopes = Envelope.objects.filter(user=user)

    envelope_ranges = {}

    for envelope in envelopes:
        expenses_by_cmonth = {
            cmonth: sum(expenses(items))
            for cmonth, items in items_by_cmonth(envelope).items()
        }

        latest_cmonth = max(expenses_by_cmonth.keys())
        i = 1
        while True:
            for cmonth in range(latest_cmonth + 1 - i, latest_cmonth + 1):
                


"""
def stats(user):
    stats = {}

    now = datetime.now().date()
    current_month = date(now.year, now.month, 1)
    three_months_back = months_back(current_month, 3)
    six_months_back = months_back(current_month, 6)

    beginning_of_time = UserData.objects.for_user(user).beginning_of_time
    first_date = now

    envelopes = Envelope.objects.filter(user=user)

    for envelope in envelopes:
        if envelope.name != "Rent":
            continue

        stats[envelope] = {}

        all_time_items = []
        three_month_items = []
        six_month_items = []
        for item in envelope.item_set.all():
            item_date = cache.get_item_date(item)

            if item_date >= current_month or item_date < beginning_of_time:
                continue

            if item_date < first_date:
                first_date = item_date

            if item_date > three_months_back:
                three_month_items.append(item)
            if item_date > six_months_back:
                six_month_items.append(item)
            all_time_items.append(item)

        stats[envelope][0] = expenses(all_time_items) / (
            month_diff(now, first_date) + 1
        )
        stats[envelope][3] = expenses(three_month_items) / 3
        stats[envelope][6] = expenses(six_month_items) / 6

    return stats
"""
