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

    def test_first_loader(self):
        csv = '''"Date","Description","Amount"
01/12/2021,"Pending: BOBS GAS",-20
01/11/2021,"Daily Ledger Bal",,10000.00,,
01/11/2021,"PAYFRIEND",-30
01/11/2021,"WALLSHOP",-62.57
01/10/2021,"MICKEY KING",-4.51'''
        charges = load(self.account, csv)
        self.assertEquals(len(Charge.objects.all()), 3)

    def test_second_loader(self):
        csv = '''Transaction Date,Post Date,Transaction Detail,Amount
2021-01-20,2021-01-20,SUPER SUSHI,10.10
2021-01-19,2021-01-20,WAYOUT,300.20
2021-01-19,2021-01-20,ZAXDEE,8.30
2021-01-22,2021-01-22,GROVERS GROCERY,35.50
2021-02-04,2021-02-04,PAYMENT,-354.10'''
        charges = load(self.account, csv)
        self.assertEquals(len(Charge.objects.all()), 5)
