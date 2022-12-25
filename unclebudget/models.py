from django.contrib.auth.models import User
from django.db import models


class Account(models.Model):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    initial_balance = models.DecimalField(max_digits=9, decimal_places=2)
    start_date = models.DateField()

    @property
    def balance(self):
        balance = 0
        for entry in self.entry_set.all():
            balance += entry.amount

        return -balance

    def __str__(self):
        return f'{self.name}'


class Entry(models.Model):
    account = models.ForeignKey('Account', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    date = models.DateField()
    description = models.CharField(max_length=255)
    load = models.ForeignKey(
        'Load',
        null=True, blank=True,
        on_delete=models.CASCADE,
    )
    receipt = models.ForeignKey(
        'Receipt',
        on_delete=models.PROTECT,
    )
    transfer_to = models.OneToOneField(
        'self',
        related_name='transfer_from',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={'receipt': None, 'transfer_to': None},
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    @property
    def amount_str(self):
        if self.amount > 0:
            return f'${self.amount}'
        else:
            return f'(${-self.amount})'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.receipt.save()

    def __str__(self):
        return f'{self.date} {self.amount_str} {self.description}'


class Envelope(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(
        'self',
        null=True, blank=True,
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    @property
    def balance(self):
        balance = 0
        for item in self.item_set.all():
            balance += item.amount

        return -balance

    def __str__(self):
        if self.parent:
            return f'{self.parent}: {self.name}'
        return f'{self.name}'


class Item(models.Model):
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    description = models.CharField(max_length=255)
    envelope = models.ForeignKey('Envelope', on_delete=models.CASCADE)
    receipt = models.ForeignKey(
        'Receipt',
        null=True, blank=True,
        on_delete=models.SET_NULL,
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    @property
    def amount_str(self):
        if self.amount > 0:
            return f'${self.amount}'
        else:
            return f'(${-self.amount})'

    @property
    def date(self):
        return self.receipt.entry_set.first().date

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.receipt.save()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.receipt.save()

    def __str__(self):
        return f'{self.date} {self.amount_str} {self.description}'


class Load(models.Model):
    loader = models.CharField(max_length=255)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.timestamp} {self.loader}'


class Receipt(models.Model):
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    balance = models.DecimalField(max_digits=9, decimal_places=2)
    date = models.DateField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    @property
    def balanced(self):
        return self.balance == 0

    def save(self, *args, **kwargs):
        if self.pk == None:
            # We need to save it before we can run the calculations below
            # balanced is required, so set it temporarily
            self.balance = 0
            super().save(*args, **kwargs)

        self.balance = (
            sum([entry.amount for entry in self.entry_set.all()]) -
            sum([item.amount for item in self.item_set.all()])
        )
        first_entry = self.entry_set.first()
        if first_entry:
            self.date = first_entry.date

        super().save(*args, **kwargs)

    def __str__(self):
        return f'#{self.id}'
