from csv import DictReader
from datetime import datetime

from unclebudget.models import Charge


def load(file):
    charges = []
    for row in DictReader(file):
        if row['Description'] == 'Daily Ledger Bal':
            continue
        if row['Description'].startswith('Pending:'):
            continue

        charges.append(Charge(
            amount = -float(row['Amount']),
            date = datetime.strptime(row['Date'], '%m/%d/%Y').date(),
            description = row['Description'],
        ))

    return charges
