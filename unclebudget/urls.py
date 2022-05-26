from django.urls import path

from unclebudget.views import *


urlpatterns = [ 
    path('accounts', AccountList.as_view()),
    path('accounts/<int:id>', AccountDetail.as_view()),
    path('envelopes', EnvelopeList.as_view()),
    path('envelopes/<int:id>', EnvelopeDetail.as_view()),
]
