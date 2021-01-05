from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
import datetime
import functools
import random

# Create your models here.
def generateString(length=18, alphabet='abcdefghjkmnopqrstuvwxyz23456789'):
    return ''.join(random.choices(alphabet, k=length))

generateIdentifierId = functools.partial(generateString, 13) 
generateTokenSecret = functools.partial(generateString, 13)

class Token(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    issued = models.DateTimeField(auto_now_add=True)
    secret = models.CharField(
        default=generateIdentifierId,
        max_length=255, 
        editable=False
    )

    validDaysUnused = models.IntegerField(default=30)
    validDaysAfterFirstUse = models.IntegerField(default=1)
    firstUsed = models.DateTimeField(null=True, blank=True)

    # ...
    def __str__(self):
        return self.secret

    def used(self):
        return self.firstUsed != None

    def expiration(self):
        if self.used():
            return self.firstUsed + datetime.timedelta(
                days=self.validDaysAfterFirstUse
            )
        else:
            return self.issued + datetime.timedelta(
                days=self.validDaysUnused
            )
    # ...
    def valid(self):
        return self.expiration() >= timezone.now()

    expiration.admin_order_field = 'expiration'
    expiration.short_description = 'expiration date'

    valid.admin_order_field = 'valid'
    valid.boolean = True
    valid.short_description = 'valid'



class Identifier(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    id = models.CharField(
        primary_key=True, 
        default=generateIdentifierId,
        max_length=255, 
        editable=False
    )














