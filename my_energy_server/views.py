
import logging

from rest_framework import generics
from django.http import JsonResponse, HttpResponse

from django.views.generic import ListView

from .models import EnergyRecord, Configuration
from .services import algorithms

logger = logging.getLogger(__name__)


# example: /my_energy
class IndexView(ListView):
    queryset = Configuration.objects.all()
    template_name = 'my_energy_server/index.html'

    # by default this returns the list in an object called object_list, so use 'object_list' in the html page.
    # but if 'context_object_name' is defined, then this returned list is named and can be accessed that way in html.
    context_object_name = 'my_configuration'




# example: /my_energy/timestamp/2019-02-21T06:00:00Z/
class DetailsView(generics.RetrieveUpdateDestroyAPIView):
    model = EnergyRecord
    queryset = EnergyRecord.objects.all()


# example: /my_energy/api/getseries?from=2019-01-14&to=2019-01-15&resolution=Hour
def GetSeriesView(request):

    # read the arguments from the query
    param_to = request.GET.get('to', '2019-03-19')
    param_from = request.GET.get('from', '2019-03-18')
    resolution = request.GET.get('resolution', 'hour')

    data=algorithms.get_data(param_to,param_from,resolution)

    return JsonResponse({
        'result': 'true',
        'data': data,
    })

