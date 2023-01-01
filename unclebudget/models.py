from django.contrib.auth.models import AnonymousUser, User
from django.db import models


class Account(models.Model):
    name = models.TextField()
    initial_balance = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    start_date = models.DateField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ['name']

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
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-date']

    @property
    def balance(self):
        item_amount_sum = self.item_set.aggregate(models.Sum('amount'))['amount__sum'] or 0
        return self.amount - item_amount_sum

    @property
    def balanced(self):
        return self.balance == 0

    def __str__(self):
        return f'{self.date} ${self.amount} {self.description}'


class Envelope(models.Model):
    name = models.TextField()
    initial_balance = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ['name']

    @property
    def balance(self):
        balance = self.initial_balance
        for item in self.item_set.all():
            balance -= item.amount

        return balance

    def delete(self):
        for item in self.item_set.all():
            item.delete()
        super().delete(*args, **kwargs)

    def __str__(self):
        return f'{self.name}'


class Item(models.Model):
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    description = models.TextField()
    envelope = models.ForeignKey('Envelope', on_delete=models.PROTECT)
    entry = models.ForeignKey('Entry', on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tags = models.ManyToManyField('Tag')

    #class Meta:
    #    ordering = ['-date']

    def __str__(self):
        return f'{self.date} {self.amount} {self.description}'


class Load(models.Model):
    loader = models.TextField()
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-timestamp']

    def delete(self, *args, **kwargs):
        for entry in self.entry_set.all():
            entry.delete()
        super().delete(*args, **kwargs)

    def __str__(self):
        return f'{self.timestamp} {self.loader}'


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


class Tag(models.Model):
    name = models.TextField()
    user = models.OneToOneField(User, on_delete=models.CASCADE)
