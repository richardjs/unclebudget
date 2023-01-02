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
            start_date=datetime(1970, 1, 1).date()
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


class ModelsTestCase(TestCase):
    def setUp(self):
        User.objects.create_user(
           'testuser', 'testuser@example.com', 'password').save()
        self.user = User.objects.get()
        self.client.login(username='testuser', password='password')

        self.account = Account(
            name='Test Account', user=self.user,
            start_date=datetime(1970, 1, 1).date()
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
                entry=entry,
                envelope=self.envelope,
            )
            item.save()

    def test_account_balance(self):
        account = Account.objects.first()
        self.assertEquals(account.balance, Decimal('902.92'))

    def test_receipts_balanced(self):
        for entry in Entry.objects.all():
            self.assertTrue(Entry.balanced)

        entry = Entry.objects.first()
        item = entry.item_set.first()
        item.amount = item.amount + 1
        item.save()
        self.assertFalse(entry.balanced)

    def test_process_entry(self):
        response = self.client.get(reverse('process'))
        # Everything is balanced in initial conditions
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, reverse('summary'))

        # Unbalance the entry
        item = Item.objects.first()
        item.amount = item.amount + 1
        item.save()
        # Process URL should take you to the page for the entry
        response = self.client.get(reverse('process'), follow=True)
        self.assertEquals(response.context['entry'], item.entry)

        # Rebalance the entry with the web interface
        self.client.post(reverse('entry-detail', kwargs={'pk': item.entry.id}), {
            'item_id': item.id,
            'item_envelope': item.envelope.id,
            'item_amount': item.amount - 1,
            'item_description': '',
        })

        # Entry should be balanced now
        response = self.client.get(reverse('process'))
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, reverse('summary'))

    def test_changing_item_changes_entry_balance(self):
        item = Item.objects.first()
        item.amount += 1
        item.save()
        self.assertFalse(item.entry.balanced)
        item.amount -= 1
        item.save()
        self.assertTrue(item.entry.balanced)
        item.delete()
        self.assertFalse(item.entry.balanced)

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

    def test_deleting_load_entries_deletes_entries(self):
        csv = '''"Date","Description","Amount"
01/11/2021,"NEW PAYFRIEND",-30
01/11/2021,"NEW WALLSHOP",-62.57
01/10/2021,"NEW MICKEY KING",-4.51
01/9/2021,"NEW PAYCHECK",1000.00'''
        load, _ = load_entries(self.account, csv)

        num_entries = len(Entry.objects.all())
        load.delete()
        self.assertEquals(len(Entry.objects.all()), num_entries - 4)

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
        with self.assertRaises(UserData.DoesNotExist):
            UserData.objects.for_user(AnonymousUser)
