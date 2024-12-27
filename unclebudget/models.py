from datetime import date

from django.contrib.auth.models import AnonymousUser, User
from django.db import models
from django.urls import reverse

from . import cache


class Account(models.Model):
    name = models.TextField()
    start_date = models.DateField()

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ["name"]

    @property
    def balance(self):
        # We could calculate this in the DB, but sqlite3 doesn't have a
        # decimal type, so do it here instead for accuracy
        return -sum([entry.amount for entry in self.entry_set.all()])

    def get_absolute_url(self):
        return reverse("account-detail", kwargs={"pk": self.pk})

    def __str__(self):
        return f"{self.name}"


class Entry(models.Model):
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    date = models.DateField()
    description = models.TextField()

    account = models.ForeignKey("Account", on_delete=models.CASCADE)
    load = models.ForeignKey("Load", null=True, blank=True, on_delete=models.CASCADE)

    expected = models.BooleanField(default=False)

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ["-date", "-amount"]

    @property
    def balance(self):
        # We could calculate this in the DB, but sqlite3 doesn't have a
        # decimal type, so do it here instead for accuracy
        return self.amount - sum([item.amount for item in self.item_set.all()])

    @property
    def balanced(self):
        return self.balance == 0

    def get_absolute_url(self):
        return reverse("entry-detail", kwargs={"pk": self.pk})

    def save(self, **kwargs):
        super().save(**kwargs)

        cache.clear_account_balance(self.account)

        unbalanced = cache.get_unbalanced_entries(self.user)

        if self.balanced:
            if self in unbalanced:
                unbalanced.remove(self)
        else:
            unbalanced.add(self)

        cache.set_unbalanced_entries(self.user, unbalanced)

        for item in self.item_set.all():
            cache.clear_item_date(item)

    def __str__(self):
        return f"{self.account.name}: {self.date} ${self.amount} {self.description}"


class Envelope(models.Model):
    name = models.TextField()
    description = models.TextField(blank=True)
    pinned = models.BooleanField(default=False)

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ["name"]

    @property
    def balance(self):
        # We could calculate this in the DB, but sqlite3 doesn't have a
        # decimal type, so do it here instead for accuracy
        return -sum([item.amount for item in self.item_set.all()])

    def get_absolute_url(self):
        return reverse("envelope-detail", kwargs={"pk": self.pk})

    def __str__(self):
        return f"{self.name}"


class Item(models.Model):
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    description = models.TextField()

    envelope = models.ForeignKey("Envelope", on_delete=models.CASCADE)
    entry = models.ForeignKey("Entry", on_delete=models.CASCADE)
    tags = models.ManyToManyField("Tag")

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ["-entry__date", "-amount"]

    def save(self, **kwargs):
        # Item amount signs always match their entries
        if (self.entry.amount > 0 and self.amount < 0) or (
            self.entry.amount < 0 and self.amount > 0
        ):
            self.amount *= -1

        super().save(**kwargs)

        cache.clear_envelope_balance(self.envelope)

        unbalanced = cache.get_unbalanced_entries(self.user)

        if self.entry.balanced:
            if self.entry in unbalanced:
                unbalanced.remove(self.entry)
        else:
            unbalanced.add(self.entry)

        cache.set_unbalanced_entries(self.user, unbalanced)

    def __str__(self):
        return (
            f"{self.envelope.name}: {self.entry.date} ${self.amount} {self.description}"
        )


class Load(models.Model):
    loader = models.TextField()
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ["-timestamp"]

    def delete(self, *args, **kwargs):
        for entry in self.entry_set.all():
            entry.delete()
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.loader}: {self.entry_set.first().account} {self.timestamp}"


class Note(models.Model):
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


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
    beginning_of_time = models.DateField(default=date.fromtimestamp(0))
    dark_mode = models.BooleanField(default=True)

    small_change_envelope = models.ForeignKey(
        Envelope,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    small_change_threshold = models.DecimalField(
        max_digits=9, decimal_places=2, default=1.00
    )

    transfer_envelope = models.ForeignKey(
        Envelope,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    objects = UserDataManager()
