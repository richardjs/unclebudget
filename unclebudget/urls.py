from django.urls import path

from unclebudget.views import *


urlpatterns = [ 
    path('', summary, name='summary'),
    path('accounts/<int:pk>', AccountDetail.as_view(), name='account-detail'),
    path('envelopes/<int:pk>', EnvelopeDetail.as_view(), name='envelope-detail'),
    path('process', process, name='process'),
    path('receipt/<int:pk>', receipt, name='receipt'),
    path('upload', upload, name='upload'),
]
