from csv import DictReader
from datetime import datetime
from decimal import Decimal

from unclebudget.models import Entry


def load(file):
    entries = []
    for row in DictReader(file):
        if row['Description'] == 'Daily Ledger Bal':
            continue
        if row['Description'].startswith('Pending:'):
            continue

        entries.append(Entry(
            amount = -Decimal(row['Amount'].replace(',', '')),
            date = datetime.strptime(row['Date'], '%m/%d/%Y').date(),
            description = row['Description'].strip(),
        ))

    return entries
