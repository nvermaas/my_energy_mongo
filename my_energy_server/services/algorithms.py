import os
import logging
import datetime, time
import requests
import json

from calendar import monthrange
from django.db.models import Sum, Min, Max, Avg
from my_energy_server.models import Configuration, EnergyRecord
from .common import timeit
from .growatt import hash_password, GrowattApi, Timespan

from django.conf import settings


DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DJANGO_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

logger = logging.getLogger(__name__)


def record_contains_zero(record):
    if (record.kwh_181==0) or (record.kwh_182==0) or (record.gas==0):
        return True
    else:
        return False


def get_minutes(param_from,param_to):
    """
    return minutes between 2 dates
    :param param_from:
    :param param_to:
    :return:
    """
    date_from = datetime.datetime.strptime(param_from, DATE_FORMAT)
    date_to = datetime.datetime.strptime(param_to, DATE_FORMAT)
    minutes = (date_to - date_from).total_seconds() / 60.0
    return int(minutes)


def get_expected_number_of_records(param_from, param_to, resolution_in_minutes):
    """
    return records between 2 dates
    :param param_from:
    :param param_to:
    :return:
    """
    date_from = datetime.datetime.strptime(param_from, DATE_FORMAT)
    date_to = datetime.datetime.strptime(param_to, DATE_FORMAT)
    seconds = int((date_to - date_from).total_seconds())
    records = round(seconds / int(60 * resolution_in_minutes))
    #logger.info('expected_number_of_records = '+str(records))
    return int(records)


def get_step(resolution,timestamp):
    '''
    Determine the step size in minutes through the data based on resolution.
    If the resolution in a month then the size differs per month, and even per year.
    :param resolution:
    :param rec:
    :return:
    '''
    if resolution.upper() == 'ONEMINUTE':
        step = 1

    if resolution.upper() == '5MINUTES':
        step = 5

    if resolution.upper() == 'FIVEMINUTES':
        step = 5

    if resolution.upper() == '15MINUTES':
        step = 15


    if resolution.upper() == 'HOUR':
        step = 60

    elif resolution.upper() == 'DAY':
        step = 60 * 24

    elif resolution.upper() == 'WEEK':
        step = 60 * 24 * 7

    elif resolution.upper() == 'MONTH':

        if timestamp!=None:
            year = timestamp.year
            month = timestamp.month
            startday,number_of_days = monthrange(year, month)
            step = 60 * 24 * number_of_days
        else:
            # skip to the end of the year
            step = 60 * 24 * 365

    elif resolution.upper() == 'YEAR':
        step = 60 * 24 * 365

    return step


def get_previous_record(timestamp_from, timestamp):
    """
    When no data was found at the requested timestamp, then step back per minute until
    a record containing data was found.
    :param timestamp:
    :return:
    """

    # select the range and retrieve the last record (the latest timestamp)
    try:
        queryset = EnergyRecord.objects.filter(timestamp__range=[timestamp_from, timestamp])
        last_record = queryset.latest('timestamp')
    except:
        # if there is no last_record, then return an empty record
        last_record = EnergyRecord(kwh_181=0, kwh_182=0, kwh_281=0, kwh_282=0, gas=0, growatt_power=0, growatt_power_today=0)

    logger.info('get_previous_record = '+str(last_record))
    return last_record


@timeit
def get_average_from_dataset(timestamp_from, timestamp_to, dataset):
    query = dataset + '__avg'
    avg_value = EnergyRecord.objects.filter(timestamp__range=[timestamp_from, timestamp_to]).aggregate(Avg(dataset))[query]
    if avg_value == None:
        avg_value = 0.0
    return avg_value


@timeit
def get_sum_from_dataset(timestamp_from, timestamp_to, dataset):
    query = dataset + '__sum'
    sum_value = EnergyRecord.objects.filter(timestamp__range=[timestamp_from, timestamp_to]).aggregate(Sum(dataset))[query]
    if sum_value == None:
        sum_value = 0.0
    return sum_value


@timeit
def get_min_from_dataset(timestamp_from, timestamp_to, dataset):
    query = dataset + '__min'
    min_value = EnergyRecord.objects.filter(timestamp__range=[timestamp_from, timestamp_to]).aggregate(Min(dataset))[query]
    if min_value == None:
        min_value = 0.0
    return min_value


@timeit
def get_max_from_dataset(timestamp_from, timestamp_to, dataset):
    query = dataset + '__max'
    max_value = EnergyRecord.objects.filter(timestamp__range=[timestamp_from, timestamp_to]).aggregate(Max(dataset))[query]
    if max_value == None:
        max_value = 0.0
    return max_value


def get_next_month_timestamp(timestamp):
    year = timestamp.year
    month = timestamp.month
    startday, number_of_days = monthrange(year, month)
    next_timestamp = timestamp + datetime.timedelta(days=number_of_days)
    return next_timestamp

@timeit
def get_data(param_to,param_from,resolution):
    """
    Structure the data in a json format as expected by the EnergyView frontend
    For compatibility reasons I use the same format as the Qurrent Qservice

    :param param_to: upper timestamp limit (to)
    :param param_from: lower timestamp limit (from
    :param resolution:
    :return: data[], json structure with structured and calculated data
    """
    logger.info('get_data(' + param_to +',' + param_from + ',' + resolution + ')')

    # initialize
    data = []
    my_netlow_list = []
    my_nethigh_list = []
    my_consumption_list = []
    my_gas_list = []
    my_generation_list = []
    my_growatt_list = []

    last_record = None

    timestamp_param_from = datetime.datetime.strptime(param_from, DATE_FORMAT)
    resolution_in_minutes = get_step(resolution, timestamp_param_from)

    # determine the dimensions of the requested data
    records_expected = get_expected_number_of_records(param_from, param_to, resolution_in_minutes)

    rec0 = EnergyRecord(kwh_181=0, kwh_182=0, kwh_281=0, kwh_282=0, gas=0, growatt_power=0, growatt_power_today=0)

    timestamp = timestamp_param_from

    try:
        rec1 = EnergyRecord.objects.get(timestamp=timestamp)
    except:
        # record not found, fake it by getting the previous one.
        rec1 = get_previous_record(timestamp_param_from, timestamp)

    # loop through the number of expected records
    for i in range(records_expected):

        if resolution == 'Month':
            next_timestamp = get_next_month_timestamp(timestamp)
        else:
            next_timestamp = timestamp + datetime.timedelta(minutes=resolution_in_minutes)

        try:
            rec2 = EnergyRecord.objects.get(timestamp=next_timestamp)
        except:
            # record not found, find the last record with data and use that
            if (last_record==None):
                # the last record is the same throughout the calculation, so only determine it once.
                last_record = get_previous_record(timestamp_param_from, timestamp=next_timestamp)
                last_record.growatt_power = 0 # to let the unfinished graph go to the x-axis
            #logger.info('last_record = '+str(last_record))
            rec2 = last_record


        # determine the values for the return structure
        delta_kwh_181 = rec2.kwh_181 - rec1.kwh_181
        delta_kwh_182 = rec2.kwh_182 - rec1.kwh_182
        delta_kwh_281 = rec2.kwh_281 - rec1.kwh_281
        delta_kwh_282 = rec2.kwh_282 - rec1.kwh_282

        delta_netlow = delta_kwh_181 - delta_kwh_281
        my_netlow_list.append(delta_netlow)

        delta_nethigh = delta_kwh_182 - delta_kwh_282
        my_nethigh_list.append(delta_nethigh)

        delta_generation = delta_kwh_281 + delta_kwh_282
        my_generation_list.append(delta_generation)

        delta_gas = rec2.gas - rec1.gas
        my_gas_list.append(delta_gas)


        # --- add solar panel data -----------------------------------------
        if rec2.growatt_power==None:
            rec2.growatt_power = 0

        if rec2.growatt_power_today==None:
            rec2.growatt_power = 0

        # The Wph (what per hour) value is stored per 5 minutes in the database.
        # So to get the watts produced per hour I need to sum up all those 5 minute slices
        # and divide the sum by 12 (60 / 5 minutes).
        growatt_power = float(get_sum_from_dataset(timestamp, next_timestamp, 'growatt_power')/12)
        my_growatt_list.append(growatt_power)

        if growatt_power>0:
            delta_consumption = delta_netlow + delta_nethigh + growatt_power
        else:
            # old values, before the solar panel data was in the database
            delta_consumption = delta_kwh_181 + delta_kwh_182

        if delta_consumption<0:
            print(delta_consumption)

        my_consumption_list.append(delta_consumption)

        rec1 = rec2
        timestamp = next_timestamp


    # construct the json structure

    netlow_record = {}
    total_kwh_low = sum(my_netlow_list)
    netlow_record['data'] = my_netlow_list
    netlow_record['type'] = 'NetLow'
    netlow_record['total'] = total_kwh_low
    netlow_record['energyType'] = 'NetLow' # kept for backward compatibility
    print(str(netlow_record))

    nethigh_record = {}
    total_kwh_high = sum(my_nethigh_list)
    nethigh_record['data'] = my_nethigh_list
    nethigh_record['type'] = 'NetHigh'
    nethigh_record['total'] = total_kwh_high
    nethigh_record['energyType'] = 'NetHigh' # kept for backward compatibility
    print(str(nethigh_record))

    consumption_record = {}
    total_consumption = sum(my_consumption_list)
    consumption_record['data'] = my_consumption_list
    consumption_record['type'] = 'Consumption'
    consumption_record['total'] = total_consumption
    consumption_record['energyType'] = 'Consumption' # kept for backward compatibility
    print(str(consumption_record))

    generation_record = {}
    total_generation = sum(my_generation_list)
    generation_record['data'] = my_generation_list
    generation_record['type'] = 'Generation'
    generation_record['total'] = total_generation
    generation_record['energyType'] = 'Generation' # kept for backward compatibility
    print(str(generation_record))

    gas_record = {}
    total_gas = sum(my_gas_list)
    gas_record['data'] = my_gas_list
    gas_record['type'] = 'Gas'
    gas_record['total'] = total_gas
    gas_record['energyType'] = 'Gas' # kept for backward compatibility
    print(str(gas_record))

    # construct solar panels record with with the accumulated live data
    growatt_record = {}
    try:
        growatt_record['type'] = 'Solar Panels'
        growatt_record['data'] = my_growatt_list

        # add the cumulative total for this day so far
        # growatt_total = rec2.growatt_power_today
        # growatt_record['total'] = growatt_total

        # if growatt_total==0:
            # due to a bug in the growatt data the total power seems to be reset about 10 to 15 minutes before midnight
            # because the sun doesn't usually shine around midnight, I can retrieve the value an hour earlier

        #    hour_earlier_rec = EnergyRecord.objects.get(timestamp=timestamp - datetime.timedelta(hours=1))
        #    growatt_total = hour_earlier_rec.growatt_power_today

        # growatt_total = round(sum(my_growatt_list)/100) / 10
        rowatt_total = sum(my_growatt_list)
        growatt_record['total'] = rowatt_total
        print(str(growatt_record))
    except:
        pass

    data.append(netlow_record)
    data.append(consumption_record)
    data.append(nethigh_record)
    data.append(gas_record)
    data.append(generation_record)

    # solar panels
    data.append(growatt_record)
    return data

