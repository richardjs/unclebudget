from decimal import Decimal
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User, AnonymousUser
from django.test import TestCase
from django.urls import reverse

from . import cache, stats
from .loader import load_entries
from .models import *


class LoaderTestCase(TestCase):
    def setUp(self):
        User.objects.create_user("testuser", "testuser@example.com", "password").save()
        self.user = User.objects.get()
        self.client.login(username="testuser", password="password")

        self.account = Account(
            name="Test", user=self.user, start_date=datetime(1970, 1, 1).date()
        )
        self.account.save()

    def test_first_load_entries(self):
        csv = """"Date","Description","Amount"
01/12/2021,"Pending: BOBS GAS",-20
01/11/2021,"Daily Ledger Bal",,10000.00,,
01/11/2021,"PAYFRIEND",-30
01/11/2021,"WALLSHOP","-6,200.57"
01/10/2021,"MICKEY KING",-4.51"""
        _, entries = load_entries(self.account, csv)
        self.assertEqual(len(Entry.objects.all()), 3)

    def test_second_load_entries(self):
        csv = """Transaction Date,Post Date,Transaction Detail,Amount
2021-01-20,2021-01-20,SUPER SUSHI,10.10
2021-01-19,2021-01-20,WAYOUT,300.20
2021-01-19,2021-01-20,ZAXDEE,"8,123.30"
2021-01-22,2021-01-22,GROVERS GROCERY,3,5.50
2021-02-04,2021-02-04,PAYMENT,-354.10"""
        _, entries = load_entries(self.account, csv)
        self.assertEqual(len(Entry.objects.all()), 5)

    def test_load_entries_and_dawn_of_time(self):
        csv = """Transaction Date,Post Date,Transaction Detail,Amount
1969-12-31,2021-01-20,SUPER SUSHI,10.10
2021-01-19,2021-01-20,WAYOUT,300.20
2021-01-19,2021-01-20,ZAXDEE,8.30
2021-01-22,2021-01-22,GROVERS GROCERY,35.50
2021-02-04,2021-02-04,PAYMENT,-354.10"""
        _, entries = load_entries(self.account, csv)
        self.assertEqual(len(Entry.objects.all()), 4)

    def test_expected_entry(self):
        Entry(
            amount=30,
            date=datetime.now(),
            description="payfriend purchase",
            account=self.account,
            expected=True,
            user=self.user,
        ).save()

        csv = """"Date","Description","Amount"
01/12/2021,"Pending: BOBS GAS",-20
01/11/2021,"Daily Ledger Bal",,10000.00,,
01/11/2021,"PAYFRIEND",-30
01/11/2021,"WALLSHOP","-6,200.57"
01/10/2021,"MICKEY KING",-4.51"""

        _, entries = load_entries(self.account, csv)
        self.assertEqual(len(Entry.objects.all()), 3)

    def test_small_change(self):
        envelope = Envelope.objects.create(
            name="Small Change",
            user=self.user,
        )
        envelope.save()

        user_data = UserData.objects.for_user(self.user)
        user_data.small_change_envelope = envelope
        user_data.save()

        csv = """"Date","Description","Amount"
01/12/2021,"Pending: BOBS GAS",-20
01/11/2021,"Daily Ledger Bal",,10000.00,,
01/11/2021,"PAYFRIEND",-30
01/11/2021,"WALLSHOP","-6,200.57"
01/10/2021,"MICKEY KING",-0.51"""

        load_entries(self.account, csv)

        self.assertEqual(envelope.item_set.count(), 1)
        self.assertEqual(envelope.item_set.first().amount, Decimal("0.51"))


class ModelsTestCase(TestCase):
    def setUp(self):
        User.objects.create_user("testuser", "testuser@example.com", "password").save()
        self.user = User.objects.get()
        self.client.login(username="testuser", password="password")

        self.account = Account(
            name="Test Account", user=self.user, start_date=datetime(1970, 1, 1).date()
        )
        self.account.save()

        csv = """"Date","Description","Amount"
01/11/2021,"PAYFRIEND",-30
01/11/2021,"WALLSHOP",-62.57
01/10/2021,"MICKEY KING",-4.51
01/9/2021,"PAYCHECK",1000.00"""
        _, entries = load_entries(self.account, csv)

        self.envelope = Envelope(
            name="Test Envelope",
            user=self.user,
        )
        self.envelope.save()

        self.envelope2 = Envelope(
            name="Test Envelope 2",
            user=self.user,
        )
        self.envelope2.save()

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
        self.assertEqual(account.balance, Decimal("902.92"))

    def test_entriess_balanced(self):
        for entry in Entry.objects.all():
            self.assertTrue(Entry.balanced)

        entry = Entry.objects.first()
        item = entry.item_set.first()
        item.amount = item.amount + 1
        item.save()
        self.assertFalse(entry.balanced)

    def test_process_entry(self):
        response = self.client.get(reverse("process"))
        # Everything is balanced in initial conditions
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("summary"))

        # Unbalance the entry
        item = Item.objects.first()
        item.amount = item.amount + 1
        item.save()
        # Process URL should take you to the page for the entry
        response = self.client.get(reverse("process"), follow=True)
        self.assertEqual(response.context["entry"], item.entry)

        # Rebalance the entry with the web interface
        self.client.post(
            reverse("entry-detail", kwargs={"pk": item.entry.id}),
            {
                "item_id": item.id,
                "item_envelope": item.envelope.id,
                "item_amount": item.amount - 1,
                "item_description": "",
            },
        )

        # Entry should be balanced now
        response = self.client.get(reverse("process"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("summary"))

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
        csv = """"Date","Description","Amount"
01/11/2021,"PAYFRIEND",-30
01/11/2021,"WALLSHOP",-62.57
01/10/2021,"MICKEY KING",-4.51
01/9/2021,"PAYCHECK",1000.00"""
        load_entries(self.account, csv)
        self.assertEqual(len(Entry.objects.all()), num_entries)

        csv = """"Date","Description","Amount"
01/12/2021,"NEW ENTRY",-30
01/11/2021,"PAYFRIEND",-30
01/11/2021,"WALLSHOP",-62.57
01/10/2021,"MICKEY KING",-4.51
01/9/2021,"PAYCHECK",1000.00"""
        load_entries(self.account, csv)
        self.assertEqual(len(Entry.objects.all()), num_entries + 1)

    def test_deleting_load_entries_deletes_entries(self):
        csv = """"Date","Description","Amount"
01/11/2021,"NEW PAYFRIEND",-30
01/11/2021,"NEW WALLSHOP",-62.57
01/10/2021,"NEW MICKEY KING",-4.51
01/9/2021,"NEW PAYCHECK",1000.00"""
        load, _ = load_entries(self.account, csv)

        num_entries = len(Entry.objects.all())
        load.delete()
        self.assertEqual(len(Entry.objects.all()), num_entries - 4)

    def test_access_limited_to_user(self):
        User.objects.create_user(
            "testuser2", "testuser2@example.com", "password"
        ).save()
        self.client.login(username="testuser2", password="password")
        response = self.client.get(reverse("account-detail", kwargs={"pk": 1}))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse("envelope-detail", kwargs={"pk": 1}))
        self.assertEqual(response.status_code, 404)

    def test_dark_mode_toggle(self):
        response = self.client.get("/")
        self.assertIn('data-bs-theme="dark"', response.content.decode())
        self.client.get(reverse("toggle-theme"))
        response = self.client.get("/")
        self.assertNotIn('data-bs-theme="dark"', response.content.decode())

    def test_no_anonymous_settings(self):
        with self.assertRaises(UserData.DoesNotExist):
            UserData.objects.for_user(AnonymousUser)

    def test_envelope_create(self):
        response = self.client.post(
            reverse("envelope-create"),
            {
                "name": "Test",
                "description": "this is a test",
            },
            follow=True,
        )
        envelope = response.context["envelope"]
        self.assertEqual(envelope.name, "Test")
        self.assertEqual(envelope.description, "this is a test")

    def test_entry_form_autobalance(self):
        entry = Entry(
            user=self.user,
            account=self.account,
            amount=1000,
            date=datetime.now(),
        )
        entry.save()
        item1 = Item(
            user=self.user,
            entry=entry,
            envelope=self.envelope,
            amount=700,
        )
        item1.save()

        # Create a second item with the web form, leaving the amount blank
        self.client.post(
            entry.get_absolute_url(),
            {
                "item_id": [item1.id, ""],
                "item_envelope": [self.envelope.id, self.envelope.id],
                "item_amount": [700, ""],
                "item_description": ["", ""],
            },
        )

        # The new item's amount should be the remainder of the entry, balancing it
        self.assertTrue(entry.balanced)

    def test_unbalanced_entries_cache(self):
        unbalanced = cache.get_unbalanced_entries(self.user)
        self.assertEqual(len(unbalanced), 0)

        item = Item.objects.first()
        item.amount += 1
        item.save()

        unbalanced = cache.get_unbalanced_entries(self.user)
        self.assertEqual(len(unbalanced), 1)
        self.assertTrue(item.entry in unbalanced)

        item.amount -= 1
        item.save()

        unbalanced = cache.get_unbalanced_entries(self.user)
        self.assertEqual(len(unbalanced), 0)

    def test_balance_caches(self):
        account = Account.objects.first()
        entry = account.entry_set.first()
        item = entry.item_set.first()
        envelope = item.envelope

        self.assertEqual(account.balance, cache.get_account_balance(account))
        self.assertEqual(envelope.balance, cache.get_envelope_balance(envelope))

        item.amount += 1
        item.save()

        self.assertEqual(account.balance, cache.get_account_balance(account))
        self.assertEqual(envelope.balance, cache.get_envelope_balance(envelope))

    def test_item_date_cache(self):
        item = Item.objects.first()
        self.assertEqual(cache.get_item_date(item), item.entry.date)

        item.entry.date = datetime.now()
        item.entry.save()

        self.assertEqual(cache.get_item_date(item), item.entry.date)

    def test_skip_entry(self):
        # Unbalance the first two entries
        entry1 = Entry.objects.get(pk=1)
        item = entry1.item_set.first()
        item.amount = item.amount + 1
        item.save()

        entry2 = Entry.objects.get(pk=2)
        item = entry2.item_set.first()
        item.amount = item.amount + 1
        item.save()

        response = self.client.get(reverse("process"), follow=True)
        self.assertEqual(response.context["entry"], entry1)

        self.client.post(reverse("entry-skip", kwargs={"pk": entry1.id}))
        response = self.client.get(reverse("process"), follow=True)
        self.assertEqual(response.context["entry"], entry2)

        self.client.post(reverse("entry-skip", kwargs={"pk": entry2.id}))
        response = self.client.get(reverse("process"), follow=True)
        self.assertEqual(response.context["entry"], entry1)

    def test_create_expected(self):
        self.client.post(
            "/expect",
            {
                "account_id": self.account.id,
                "amount": 1000,
                "description": "test expected entry creation",
                "item_id": ["", ""],
                "item_envelope": [self.envelope.id, self.envelope2.id],
                "item_amount": [700, ""],
                "item_description": ["", ""],
            },
        )

        expected_entry = Entry.objects.filter(expected=True)
        self.assertEqual(len(expected_entry), 1)
        expected_entry = expected_entry.first()

        item1 = Item.objects.get(entry=expected_entry, envelope=self.envelope)
        item2 = Item.objects.get(entry=expected_entry, envelope=self.envelope2)

        self.assertEqual(item1.amount, 700)
        self.assertEqual(item2.amount, 300)

    def test_entry_form_remove_multiple_items(self):
        entry = Entry.objects.first()

        item = Item.objects.create(
            user=entry.user,
            amount=10,
            description="second item",
            entry=entry,
            envelope=self.envelope2,
        )

        self.client.post(
            reverse("entry-detail", kwargs={"pk": entry.id}),
            {
                "item_id": item.id,
                "item_envelope": "",
                "item_amount": item.amount,
                "item_description": "",
            },
        )

        # Both items should be deleted--one was deleted by having a
        # blank envelope in the above post, and the other wasn't
        # present in the post at all
        self.assertEqual(len(entry.item_set.all()), 0)

    def test_entry_form_autobalance_with_existing_balance(self):
        entry = Entry.objects.first()
        item = entry.item_set.first()
        item.amount -= 10
        item.save()

        self.client.post(
            reverse("entry-detail", kwargs={"pk": entry.id}),
            {
                "item_id": item.id,
                "item_envelope": item.envelope.id,
                "item_amount": "",
                "item_description": "",
            },
        )

        item.refresh_from_db()
        self.assertEqual(item.amount, entry.amount)

    def test_item_sign_match_entry(self):
        entry = Entry.objects.create(
            account=self.account,
            amount=-100,
            date=datetime.now(),
            user=self.user,
        )

        self.client.post(
            reverse("entry-detail", kwargs={"pk": entry.id}),
            {
                "item_id": "",
                "item_envelope": self.envelope.id,
                "item_amount": "10",
                "item_description": "",
            },
        )

        self.assertEqual(entry.item_set.first().amount, -10)

    def test_envelope_transfer(self):
        prior_balance = self.envelope.balance
        prior_item_count = Item.objects.count()

        self.envelope.transfer_income_to(self.envelope2, 300)

        self.assertEqual(self.envelope.balance, prior_balance - 300)
        self.assertEqual(self.envelope2.balance, 300)
        # The transfer doesn't go evenly into existing items, so a new
        # item should have been created
        self.assertEqual(Item.objects.count(), prior_item_count + 1)

    def test_envelope_transfer_form(self):
        prior_balance = self.envelope.balance
        prior_item_count = Item.objects.count()

        self.client.post(
            reverse("envelope-transfer"),
            {
                "from_id": self.envelope.id,
                "amount": 10,
                "to_id": self.envelope2.id,
            },
        )

        self.assertEqual(self.envelope.balance, prior_balance - 10)
        self.assertEqual(self.envelope2.balance, 10)
        self.assertEqual(Item.objects.count(), prior_item_count + 1)


class LoginTestCase(TestCase):
    def setUp(self):
        User.objects.create_user("testuser", "testuser@example.com", "password").save()
        self.user = User.objects.get()

    def test_single_user_login(self):
        with self.settings(UNCLEBUDGET_SINGLE_USER="1"):
            response = self.client.get(reverse("login"))
            # Did we automatically log in?
            self.assertEqual(response.url, settings.LOGIN_REDIRECT_URL)

        with self.settings(UNCLEBUDGET_SINGLE_USER=None):
            response = self.client.get(reverse("login"))
            # Did we get the login form?
            self.assertEqual(response.status_code, 200)
