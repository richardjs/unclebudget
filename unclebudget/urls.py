from django.urls import path

from unclebudget.views import *


urlpatterns = [ 
    path('', summary, name='summary'),

    path('accounts/<int:pk>', account_detail, name='account-detail'),
    path('envelopes/<int:pk>', EnvelopeDetail.as_view(), name='envelope-detail'),
    path('receipt/<int:pk>', receipt, name='receipt'),

    path('process', process, name='process'),
    path('upload', upload, name='upload'),

    path('toggle_theme', toggle_theme, name='toggle_theme'),
]
