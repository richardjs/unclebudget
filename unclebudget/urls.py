from django.urls import path

from unclebudget.views import *


urlpatterns = [ 
    path('accounts', AccountList.as_view()),
    path('accounts/<int:pk>', AccountDetail.as_view(), name='accounts-list'),
    path('envelopes', EnvelopeList.as_view()),
    path('envelopes/<int:pk>', EnvelopeDetail.as_view()),
    path('process', process_receipt, name='process_receipt'),
]
