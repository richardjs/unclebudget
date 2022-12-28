from decimal import Decimal
from datetime import datetime

from django.contrib.auth.models import User, AnonymousUser
from django.test import TestCase
from django.urls import reverse

from .loader import load_entries
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

    def test_first_load_entrieser(self):
        csv = '''"Date","Description","Amount"
01/12/2021,"Pending: BOBS GAS",-20
01/11/2021,"Daily Ledger Bal",,10000.00,,
01/11/2021,"PAYFRIEND",-30
01/11/2021,"WALLSHOP",-62.57
01/10/2021,"MICKEY KING",-4.51'''
        _, entries = load_entries(self.account, csv)
        self.assertEquals(len(Entry.objects.all()), 3)

    def test_second_load_entrieser(self):
        csv = '''Transaction Date,Post Date,Transaction Detail,Amount
2021-01-20,2021-01-20,SUPER SUSHI,10.10
2021-01-19,2021-01-20,WAYOUT,300.20
2021-01-19,2021-01-20,ZAXDEE,8.30
2021-01-22,2021-01-22,GROVERS GROCERY,35.50
2021-02-04,2021-02-04,PAYMENT,-354.10'''
        _, entries = load_entries(self.account, csv)
        self.assertEquals(len(Entry.objects.all()), 5)

    def test_load_entrieser_and_dawn_of_time(self):
        csv = '''Transaction Date,Post Date,Transaction Detail,Amount
1969-12-31,2021-01-20,SUPER SUSHI,10.10
2021-01-19,2021-01-20,WAYOUT,300.20
2021-01-19,2021-01-20,ZAXDEE,8.30
2021-01-22,2021-01-22,GROVERS GROCERY,35.50
2021-02-04,2021-02-04,PAYMENT,-354.10'''
        _, entries = load_entries(self.account, csv)
        self.assertEquals(len(Entry.objects.all()), 4)

    def test_receipt_amounts_equals_charge_amounts(self):
        csv = '''Transaction Date,Post Date,Transaction Detail,Amount
2021-01-20,2021-01-20,SUPER SUSHI,10.10
2021-01-19,2021-01-20,WAYOUT,300.20
2021-01-19,2021-01-20,ZAXDEE,8.30
2021-01-22,2021-01-22,GROVERS GROCERY,35.50
2021-02-04,2021-02-04,PAYMENT,-354.10'''
        _, entries = load_entries(self.account, csv)
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
        _, entries = load_entries(self.account, csv)

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
        account = Account.objects.first()
        self.assertEquals(account.balance, Decimal('902.92'))

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
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, reverse('summary'))

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
        response = self.client.get(reverse('process'))
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, reverse('summary'))

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

    def test_deleting_last_entry_deletes_receipt_and_items(self):
        entry = Entry.objects.first()
        num_receipts = len(Receipt.objects.all())
        num_items = len(Item.objects.all())
        entry.delete()
        self.assertEquals(len(Receipt.objects.all()), num_receipts - 1)
        self.assertEquals(len(Item.objects.all()), num_items - 1)

    def test_load_entries_duplicates(self):
        num_entries = len(Entry.objects.all())
        csv = '''"Date","Description","Amount"
01/11/2021,"PAYFRIEND",-30
01/11/2021,"WALLSHOP",-62.57
01/10/2021,"MICKEY KING",-4.51
01/9/2021,"PAYCHECK",1000.00'''
        load_entries(self.account, csv)
        self.assertEquals(len(Entry.objects.all()), num_entries)

        csv = '''"Date","Description","Amount"
01/12/2021,"NEW ENTRY",-30
01/11/2021,"PAYFRIEND",-30
01/11/2021,"WALLSHOP",-62.57
01/10/2021,"MICKEY KING",-4.51
01/9/2021,"PAYCHECK",1000.00'''
        load_entries(self.account, csv)
        self.assertEquals(len(Entry.objects.all()), num_entries + 1)

    def test_deleting_load_entries_deletes_entries_and_receipts(self):
        csv = '''"Date","Description","Amount"
01/11/2021,"NEW PAYFRIEND",-30
01/11/2021,"NEW WALLSHOP",-62.57
01/10/2021,"NEW MICKEY KING",-4.51
01/9/2021,"NEW PAYCHECK",1000.00'''
        load, _ = load_entries(self.account, csv)

        num_entries = len(Entry.objects.all())
        num_receipts = len(Receipt.objects.all())

        load.delete()

        self.assertEquals(len(Entry.objects.all()), num_entries - 4)
        self.assertEquals(len(Receipt.objects.all()), num_receipts - 4)

    def test_access_limited_to_user(self):
        User.objects.create_user(
           'testuser2', 'testuser2@example.com', 'password').save()
        self.client.login(username='testuser2', password='password')
        response = self.client.get(reverse('account-detail', kwargs={'pk': 1}))
        self.assertEquals(response.status_code, 404)
        response = self.client.get(reverse('envelope-detail', kwargs={'pk': 1}))
        self.assertEquals(response.status_code, 404)

    def test_dark_mode_toggle(self):
        response = self.client.get('/')
        self.assertIn('data-bs-theme="dark"', response.content.decode())
        self.client.get(reverse('toggle-theme'))
        response = self.client.get('/')
        self.assertNotIn('data-bs-theme="dark"', response.content.decode())

    def test_no_anonymous_settings(self):
        with self.assertRaises(Settings.DoesNotExist):
            Settings.objects.for_user(AnonymousUser)

    def test_account_initial_balance(self):
        account = Account.objects.first()
        self.assertEquals(account.balance, Decimal('902.92'))
        account.initial_balance = 1000
        self.assertEquals(account.balance, Decimal('1902.92'))
