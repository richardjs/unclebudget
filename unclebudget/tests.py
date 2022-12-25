from decimal import Decimal
from datetime import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .loader import load
from .models import *


class LoaderTestCase(TestCase):
    def setUp(self):
        User.objects.create_user(
           'testuser', 'testuser@example.com', 'password').save()
        self.user = User.objects.get()
        self.client.login(username='testuser', password='password')

        self.account = Account(
            name='Test', user=self.user,
            initial_balance=0.0, start_date=datetime(1970, 1, 1).date()
        )
        self.account.save()

    def test_first_loader(self):
        csv = '''"Date","Description","Amount"
01/12/2021,"Pending: BOBS GAS",-20
01/11/2021,"Daily Ledger Bal",,10000.00,,
01/11/2021,"PAYFRIEND",-30
01/11/2021,"WALLSHOP",-62.57
01/10/2021,"MICKEY KING",-4.51'''
        entries = load(self.account, csv)
        self.assertEquals(len(Entry.objects.all()), 3)

    def test_second_loader(self):
        csv = '''Transaction Date,Post Date,Transaction Detail,Amount
2021-01-20,2021-01-20,SUPER SUSHI,10.10
2021-01-19,2021-01-20,WAYOUT,300.20
2021-01-19,2021-01-20,ZAXDEE,8.30
2021-01-22,2021-01-22,GROVERS GROCERY,35.50
2021-02-04,2021-02-04,PAYMENT,-354.10'''
        entries = load(self.account, csv)
        self.assertEquals(len(Entry.objects.all()), 5)

    def test_loader_and_dawn_of_time(self):
        csv = '''Transaction Date,Post Date,Transaction Detail,Amount
1969-12-31,2021-01-20,SUPER SUSHI,10.10
2021-01-19,2021-01-20,WAYOUT,300.20
2021-01-19,2021-01-20,ZAXDEE,8.30
2021-01-22,2021-01-22,GROVERS GROCERY,35.50
2021-02-04,2021-02-04,PAYMENT,-354.10'''
        entries = load(self.account, csv)
        self.assertEquals(len(Entry.objects.all()), 4)

    def test_receipt_amounts_equals_charge_amounts(self):
        csv = '''Transaction Date,Post Date,Transaction Detail,Amount
2021-01-20,2021-01-20,SUPER SUSHI,10.10
2021-01-19,2021-01-20,WAYOUT,300.20
2021-01-19,2021-01-20,ZAXDEE,8.30
2021-01-22,2021-01-22,GROVERS GROCERY,35.50
2021-02-04,2021-02-04,PAYMENT,-354.10'''
        entries = load(self.account, csv)
        for entry in entries:
            self.assertEquals(entry.amount, entry.receipt.amount)


class ModelsTestCase(TestCase):
    def setUp(self):
        User.objects.create_user(
           'testuser', 'testuser@example.com', 'password').save()
        self.user = User.objects.get()
        self.client.login(username='testuser', password='password')

        self.account = Account(
            name='Test Account', user=self.user,
            initial_balance=0.0, start_date=datetime(1970, 1, 1).date()
        )
        self.account.save()

        csv = '''"Date","Description","Amount"
01/11/2021,"PAYFRIEND",-30
01/11/2021,"WALLSHOP",-62.57
01/10/2021,"MICKEY KING",-4.51
01/9/2021,"PAYCHECK",1000.00'''
        entries = load(self.account, csv)

        self.envelope = Envelope(
            name='Test Envelope', user=self.user,
        )
        self.envelope.save()

        for entry in entries:
            item = Item(
                user=entry.user,
                amount=entry.amount,
                description=entry.description,
                envelope=self.envelope,
                receipt=entry.receipt,
            )
            item.save()

    def test_account_balance(self):
        self.assertEquals(self.account.balance, Decimal('902.92'))

    def test_receipts_created(self):
        self.assertEquals(len(Receipt.objects.all()), 4)

    def test_receipts_balanced(self):
        for receipt in Receipt.objects.all():
            self.assertTrue(receipt.balanced)

        receipt = Receipt.objects.first()
        item = receipt.item_set.first()
        item.amount = item.amount + 1
        item.save()
        self.assertFalse(receipt.balanced)

    def test_process_receipt(self):
        response = self.client.get(reverse('process'))

        # Everything is balanced in initial conditions
        self.assertIsNone(response.context)

        # Unbalance the receipt
        item = Item.objects.first()
        item.amount = item.amount + 1
        item.save()
        # Process URL should take you to the page for the receipt
        response = self.client.get(reverse('process'), follow=True)
        self.assertEquals(response.context['receipt'], item.receipt)

        # Rebalance the receipt with the web interface
        self.client.post(reverse('receipt', kwargs={'pk': item.receipt.id}), {
            'item_id': item.id,
            'item_envelope': item.envelope.id,
            'item_amount': item.amount - 1,
            'item_description': '',
        })

        # Receipt should be balanced now
        response = self.client.get(reverse('process'), follow=True)
        self.assertIsNone(response.context)

    def test_changing_item_changes_receipt_balance(self):
        item = Item.objects.first()
        item.amount += 1
        item.save()
        self.assertFalse(item.receipt.balanced)
        item.amount -= 1
        item.save()
        self.assertTrue(item.receipt.balanced)
        item.delete()
        self.assertFalse(item.receipt.balanced)
