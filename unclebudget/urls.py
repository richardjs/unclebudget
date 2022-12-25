from django.urls import path

from unclebudget.views import *


urlpatterns = [ 
    path('accounts', AccountList.as_view(), name='account-list'),
    path('accounts/<int:pk>', AccountDetail.as_view(), name='account-detail'),
    path('envelopes', EnvelopeList.as_view(), name='envelope-list'),
    path('envelopes/<int:pk>', EnvelopeDetail.as_view(), name='envelope-detail'),
    path('process', process, name='process'),
    path('receipt/<int:pk>', receipt, name='receipt'),
]
