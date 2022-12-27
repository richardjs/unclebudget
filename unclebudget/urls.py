from django.urls import path

from unclebudget.views import *


urlpatterns = [ 
    path('', summary, name='summary'),

    path('accounts/<int:pk>', account_detail, name='account-detail'),
    path('envelopes/<int:pk>', envelope_detail, name='envelope-detail'),
    path('receipt/<int:pk>', receipt, name='receipt'),

    path('process', process, name='process'),
    path('upload', upload, name='upload'),

    path('toggle-theme', toggle_theme, name='toggle-theme'),
]
