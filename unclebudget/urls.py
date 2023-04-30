from django.urls import path

from unclebudget.views import *


urlpatterns = [
    path("", summary, name="summary"),
    path("account/<int:pk>", account_detail, name="account-detail"),
    path("entry/<int:pk>", entry_detail, name="entry-detail"),
    path("envelope/<int:pk>", envelope_detail, name="envelope-detail"),
    path("envelope/new", EnvelopeCreateView.as_view(), name="envelope-create"),
    path("process", process, name="process"),
    path("upload", upload, name="upload"),
    path("toggle-theme", toggle_theme, name="toggle-theme"),
]
