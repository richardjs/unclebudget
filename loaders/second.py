from csv import DictReader
from datetime import datetime

from unclebudget.models import Charge


def load(file):
    charges = []
    for row in DictReader(file):
        charges.append(Charge(
            amount = float(row['Amount']),
            date = datetime.strptime(row['Transaction Date'], '%Y-%m-%d').date(),
            description = row['Transaction Detail'],
        ))

    return charges
