from csv import DictReader
from datetime import datetime
from decimal import Decimal

from unclebudget.models import Entry


def load(file):
    entries = []
    for row in DictReader(file):
        entries.append(
            Entry(
                amount=Decimal(row["Amount"].replace(",", "")),
                date=datetime.strptime(row["Transaction Date"], "%Y-%m-%d").date(),
                description=row["Transaction Detail"].strip(),
            )
        )

    return entries
