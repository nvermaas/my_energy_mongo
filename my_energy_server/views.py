
import logging

from rest_framework import generics
from rest_framework.response import Response

from django_filters import rest_framework as filters
from django.views.generic import ListView

from .models import EnergyRecord, Configuration
from .serializers import EnergyRecordSerializer, ConfigurationSerializer
from .services import algorithms

logger = logging.getLogger(__name__)

# /my_energy/?timestamp__gt=2019-01-05T00:00:00&timestamp__lt=2019-01-06T00:00:00
class EnergyRecordFilter(filters.FilterSet):
    class Meta:
        model = EnergyRecord

        fields = {
            'kwh_181': ['gt', 'lt', 'gte', 'lte', 'contains', 'exact','startswith'],
            'kwh_182': ['gt', 'lt', 'gte', 'lte', 'contains', 'exact', 'startswith'],
            'kwh_281': ['gt', 'lt', 'gte', 'lte', 'contains', 'exact', 'startswith'],
            'kwh_282': ['gt', 'lt', 'gte', 'lte', 'contains', 'exact', 'startswith'],
            'gas': ['gt', 'lt', 'gte', 'lte', 'contains', 'exact', 'startswith'],
            'timestamp': ['gt', 'lt', 'gte', 'lte', 'contains', 'exact', 'startswith'],
            'growatt_power': ['gt', 'lt', 'gte', 'lte','exact'],
            'growatt_power_today': ['gt', 'lt', 'gte', 'lte', 'exact'],
        }

# example: /my_energy
class IndexView(ListView):
    queryset = Configuration.objects.all()
    serializer_class = ConfigurationSerializer
    template_name = 'my_energy_server/index.html'

    # by default this returns the list in an object called object_list, so use 'object_list' in the html page.
    # but if 'context_object_name' is defined, then this returned list is named and can be accessed that way in html.
    context_object_name = 'my_configuration'


# example: /my_energy/list
class ListView(generics.ListCreateAPIView):
    model = EnergyRecord
    queryset = EnergyRecord.objects.all()
    serializer_class = EnergyRecordSerializer

    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = EnergyRecordFilter


# example: /my_energy/timestamp/2019-02-21T06:00:00Z/
class DetailsView(generics.RetrieveUpdateDestroyAPIView):
    logger.info('DetailsView()')
    model = EnergyRecord
    queryset = EnergyRecord.objects.all()
    serializer_class = EnergyRecordSerializer


# example: /my_energy/api/getseries?from=2019-01-14&to=2019-01-15&resolution=Hour
class GetSeriesView(generics.ListAPIView):
    logger.info('GetSeriesView()')
    queryset = EnergyRecord.objects.all()

    # override list and generate a custom response
    def list(self, request, *args, **kwargs):

        # read the arguments from the query
        param_to = self.request.query_params['to']
        param_from = self.request.query_params['from']
        resolution = self.request.query_params['resolution']

        data=algorithms.get_data(param_to,param_from,resolution)

        return Response({
            'result': 'true',
            'data': data,
        })

