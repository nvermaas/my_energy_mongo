from django.urls import path

from . import views

urlpatterns = [
    # ex: /my_energy/
    path('', views.IndexView.as_view()),

    # /my_energy/api/getseries?sn=15-49-002-081&from=2019-01-14&to=2019-01-15&resolution=Hour
    path('api/getseries', views.GetSeriesView, name='getseries-view'),

]