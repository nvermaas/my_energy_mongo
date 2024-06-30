from django.db import models

# Create your models here.
from django.db import models

class EnergyRecord(models.Model):
    timestamp = models.DateTimeField(primary_key=True, null=False)

    # electrical power and gas fields
    kwh_181 = models.IntegerField(null = True)
    kwh_182 = models.IntegerField(null = True)
    kwh_281 = models.IntegerField(null = True)
    kwh_282 = models.IntegerField(null = True)
    gas = models.IntegerField(null = True)

    # solar panels
    growatt_power = models.IntegerField(null = True)
    growatt_power_today = models.FloatField(null=True)

    def __str__(self):
        s = str(self.timestamp)+"," + \
            str(self.kwh_181) + "," + str(self.kwh_182) + "," + str(self.kwh_281)+","+str(self.kwh_282)+\
            ","+str(self.gas)+", "+str(self.growatt_power)+")"
        return s


class Configuration(models.Model):
    timestamp_last_update = models.DateTimeField(null=False)
