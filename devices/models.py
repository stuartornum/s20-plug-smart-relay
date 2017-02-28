from __future__ import unicode_literals

from django.db import models


class Device(models.Model):
    name = models.CharField(max_length=30)
    location = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField()
    mac = models.CharField(max_length=17)
    state = models.BooleanField(default=False)

    def __str__(self):
        return '{0} | ID: {1}'.format(self.name, self.id)

