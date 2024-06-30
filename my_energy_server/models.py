from django.db import models

# Create your models here.
from django.db import models
from mongoengine import Document, DateTimeField, IntField, FloatField

class EnergyRecord(Document):
    timestamp = DateTimeField(primary_key=True, required=True)

    # electrical power and gas fields
    kwh_181 = IntField(null=True)
    kwh_182 = IntField(null=True)
    kwh_281 = IntField(null=True)
    kwh_282 = IntField(null=True)
    gas = IntField(null=True)

    # solar panels
    growatt_power = IntField(null=True)
    growatt_power_today = FloatField(null=True)

    meta = {
        'collection': 'energy_records'
    }

    def __str__(self):
        s = str(self.timestamp)+"," + \
            str(self.kwh_181) + "," + str(self.kwh_182) + "," + str(self.kwh_281)+","+str(self.kwh_282)+\
            ","+str(self.gas)+", "+str(self.growatt_power)+")"
        return s


    def __repr__(self):
        s = str(self.timestamp)+"," + \
            str(self.kwh_181) + "," + str(self.kwh_182) + "," + str(self.kwh_281)+","+str(self.kwh_282)+\
            ","+str(self.gas)+", "+str(self.growatt_power)+")"
        return s

class Configuration(Document):
    timestamp_last_update = DateTimeField(primary_key=True, required=True)
