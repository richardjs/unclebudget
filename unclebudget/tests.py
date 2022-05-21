from django.contrib.auth.models import User
from django.test import TestCase

from .loader import load
from .models import *


class LoaderTestCase(TestCase):
    def setUp(self):
        User.objects.create_user(
           'testuser', 'testuser@example.com', 'password').save()
        self.user = User.objects.get()
        self.client.login(username='testuser', password='password')

        self.account = Account(name='Test', user=self.user)
        self.account.save()

    def test_basic_load(self):
        csv = '''"Date","Description","Amount"
01/12/2021,"Pending: BOBS GAS",-20
01/11/2021,"Daily Ledger Bal",,10000.00,,
01/11/2021,"PAYFRIEND",-30
01/11/2021,"WALLSHOP",-62.57
01/10/2021,"MICKEY KING",-4.51'''
        charges = load(self.account, csv)
