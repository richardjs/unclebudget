from django.contrib.auth.models import AnonymousUser, User
from django.db import models


class AccountManager(models.Manager):
    def user_balance(self, user):
        return sum([
            account.balance
            for account in Account.objects.filter(user=user)
        ])


class Account(models.Model):
    name = models.TextField()
    initial_balance = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    start_date = models.DateField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    objects = AccountManager()

    @property
    def balance(self):
        balance = self.initial_balance
        for entry in self.entry_set.all():
            balance -= entry.amount

        return balance

    def __str__(self):
        return f'{self.name}'


class Entry(models.Model):
    account = models.ForeignKey('Account', on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    date = models.DateField()
    description = models.TextField()
    load = models.ForeignKey('Load', null=True, blank=True, on_delete=models.PROTECT)
    receipt = models.ForeignKey('Receipt', on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    @property
    def amount_str(self):
        if self.amount > 0:
            return f'${self.amount}'
        else:
            return f'(${-self.amount})'

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        if len(self.receipt.entry_set.all()) == 0:
            self.receipt.delete()
            return
        self.receipt.save()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.receipt.save()

    def __str__(self):
        return f'{self.date} {self.amount_str} {self.description}'


class EnvelopeManager(models.Manager):
    def user_balance(self, user):
        return sum([
            envelope.balance
            for envelope in Envelope.objects.filter(user=user)
        ])


class Envelope(models.Model):
    name = models.TextField()
    initial_balance = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    objects = EnvelopeManager()

    @property
    def balance(self):
        balance = 0
        for item in self.item_set.all():
            balance += item.amount

        return -balance

    def delete(self):
        for item in self.item_set.all():
            item.delete()
        super().delete(*args, **kwargs)

    def __str__(self):
        return f'{self.name}'


class Item(models.Model):
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    date = models.DateField(blank=True, null=True)
    description = models.TextField()
    envelope = models.ForeignKey('Envelope', on_delete=models.PROTECT)
    receipt = models.ForeignKey('Receipt', on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.receipt.save()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.receipt.save()

        if self.receipt.entry_set.exists():
            receipt_date = self.receipt.entry_set.first().date
            if self.date != receipt_date:
                self.date = receipt_date
                self.save()

    def __str__(self):
        return f'{self.date} {self.amount} {self.description}'


class Load(models.Model):
    loader = models.TextField()
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def delete(self, *args, **kwargs):
        for entry in self.entry_set.all():
            entry.delete()
        super().delete(*args, **kwargs)

    def __str__(self):
        return f'{self.timestamp} {self.loader}'


class Receipt(models.Model):
    balance = models.DecimalField(max_digits=9, decimal_places=2)
    date = models.DateField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    @property
    def amount(self):
        return sum([entry.amount for entry in self.entry_set.all()])

    @property
    def balanced(self):
        return self.balance == 0

    def delete(self, *args, **kwargs):
        for entry in self.entry_set.all():
            entry.delete()
        for item in self.item_set.all():
            item.delete()
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        # We need to save a new object before we can run the calculations below
        if self.pk == None:
            # balance is required, so set it temporarily
            self.balance = 0
            super().save(*args, **kwargs)

        self.balance = (
            sum([entry.amount for entry in self.entry_set.all()]) -
            sum([item.amount for item in self.item_set.all()])
        )

        if self.entry_set.exists():
            self.date = self.entry_set.first().date

        super().save(*args, **kwargs)

    def __str__(self):
        return f'#{self.id}'


class SettingsManager(models.Manager):
    def for_user(self, user):
        if user == AnonymousUser:
            raise Settings.DoesNotExist
        try:
            settings = self.get(user=user)
        except Settings.DoesNotExist:
            settings = Settings()
            settings.user = user
            settings.save()
        return settings


class Settings(models.Model):
    dark_mode = models.BooleanField(default=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    objects = SettingsManager()
