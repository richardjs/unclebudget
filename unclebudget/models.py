from django.contrib.auth.models import AnonymousUser, User
from django.db import models
from django.urls import reverse


class Account(models.Model):
    name = models.TextField()
    start_date = models.DateField()

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ['name']

    @property
    def balance(self):
        # We could calculate this in the DB, but sqlite3 doesn't have a
        # decimal type, so do it here instead for accuracy
        return -sum([entry.amount for entry in self.entry_set.all()])

    def get_absolute_url(self):
        return reverse('account-detail', kwargs={'pk': self.pk})

    def __str__(self):
        return f'{self.name}'


class Entry(models.Model):
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    date = models.DateField()
    description = models.TextField()

    account = models.ForeignKey('Account', on_delete=models.CASCADE)
    load = models.ForeignKey('Load', null=True, blank=True, on_delete=models.CASCADE)

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-date', '-amount']

    @property
    def balance(self):
        # We could calculate this in the DB, but sqlite3 doesn't have a
        # decimal type, so do it here instead for accuracy
        return self.amount - sum([item.amount for item in self.item_set.all()])

    @property
    def balanced(self):
        return self.balance == 0

    def get_absolute_url(self):
        return reverse('entry-detail', kwargs={'pk': self.pk})

    def __str__(self):
        return f'{self.account.name}: {self.date} ${self.amount} {self.description}'


class Envelope(models.Model):
    name = models.TextField()
    description = models.TextField(blank=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ['name']

    @property
    def balance(self):
        # We could calculate this in the DB, but sqlite3 doesn't have a
        # decimal type, so do it here instead for accuracy
        return -sum([item.amount for item in self.item_set.all()])

    def get_absolute_url(self):
        return reverse('envelope-detail', kwargs={'pk': self.pk})

    def __str__(self):
        return f'{self.name}'


class Item(models.Model):
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    description = models.TextField()

    envelope = models.ForeignKey('Envelope', on_delete=models.CASCADE)
    entry = models.ForeignKey('Entry', on_delete=models.CASCADE)
    tags = models.ManyToManyField('Tag')

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-entry__date', '-amount']

    def __str__(self):
        return f'{self.envelope.name}: {self.entry.date} ${self.amount} {self.description}'


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
        return f'{self.loader}: {self.entry_set.first().account} {self.timestamp}'


class Tag(models.Model):
    name = models.TextField()

    user = models.OneToOneField(User, on_delete=models.CASCADE)


class UserDataManager(models.Manager):
    def for_user(self, user):
        if user == AnonymousUser:
            raise UserData.DoesNotExist
        try:
            settings = self.get(user=user)
        except UserData.DoesNotExist:
            settings = UserData()
            settings.user = user
            settings.save()
        return settings


class UserData(models.Model):
    dark_mode = models.BooleanField(default=True)

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    objects = UserDataManager()
