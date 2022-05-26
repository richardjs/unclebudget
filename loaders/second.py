from csv import DictReader
from datetime import datetime

from unclebudget.models import Entry


def load(file):
    entries = []
    for row in DictReader(file):
        entries.append(Entry(
            amount = float(row['Amount']),
            date = datetime.strptime(row['Transaction Date'], '%Y-%m-%d').date(),
            description = row['Transaction Detail'],
        ))

    return entries
