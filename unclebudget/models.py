from django.contrib.auth.models import User
from django.db import models


class Account(models.Model):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    @property
    def balance(self):
        balance = 0
        for entry in self.entry_set.all():
            balance += entry.amount

        return -balance


class Entry(models.Model):
    account = models.ForeignKey('Account', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    date = models.DateField()
    description = models.CharField(max_length=255)
    load = models.ForeignKey(
        'load',
        null=True, blank=True,
        on_delete=models.CASCADE,
    )
    receipt = models.ForeignKey(
        'self',
        null=True, blank=True,
        on_delete=models.SET_NULL,
    )
    transfer_to = models.OneToOneField(
        'self',
        related_name='transfer_from',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={'receipt': None, 'transfer_to': None},
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class Envelope(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class Item(models.Model):
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    description = models.CharField(max_length=255)
    receipt = models.ForeignKey(
        'Receipt',
        null=True, blank=True,
        on_delete=models.SET_NULL,
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class Load(models.Model):
    loader = models.CharField(max_length=255)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class Receipt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
