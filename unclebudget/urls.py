from django.urls import path

from unclebudget.views import *


urlpatterns = [
    path("", summary, name="summary"),
    path("account/<int:pk>", account_detail, name="account-detail"),
    path("all", all, name="all"),
    path("entry/<int:pk>", entry_detail, name="entry-detail"),
    path("entry/<int:pk>/skip", entry_skip, name="entry-skip"),
    path("envelope/<int:pk>", envelope_detail, name="envelope-detail"),
    path("envelope/new", EnvelopeCreateView.as_view(), name="envelope-create"),
    path("envelope/transfer", envelope_transfer, name="envelope-transfer"),
    path("expect", expect, name="expect"),
    path("login", LoginView.as_view(), name="login"),
    path("process", process, name="process"),
    path(
        "report/expenses-by-month",
        report_expenses_by_month,
        name="report-expenses-by-month",
    ),
    path("report/income", report_income, name="report-income"),
    path("upload", upload, name="upload"),
    path("toggle-theme", toggle_theme, name="toggle-theme"),
]
