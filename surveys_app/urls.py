from __future__ import annotations

from django.urls import path

from surveys_app import views
app_name = "surveys_app"

urlpatterns = [
    path('', views.HomeView.as_view(), name="home"),
    path('liste/', views.SurveyListView.as_view(), name="survey-list"),
    path('create_survey/', views.SurveyStep1View.as_view(), name="survey-step1"),
    path('create_survey/<uuid:uid>/questions/', views.SurveyStep2View.as_view(), name="survey-step2"),
    path('publish/<uuid:uid>/', views.PublishSurveyView.as_view(), name='publish-survey'),
    path('survey/<uuid:uid>/response/', views.SurveyResponseView.as_view(), name='survey_response'),
    path('survey/<uuid:pk>/results/', views.SurveyResultsView.as_view(), name='survey-results'),
    path('survey/<uuid:uid>/thank-you/', views.thank_you, name='thank_you'),
    path('survey/update/<uuid:pk>/', views.SurveyUpdateView.as_view(), name='survey-update'),
    path('survey/delete/<uuid:pk>/', views.SurveyDeleteView.as_view(), name='survey-delete'),
    path('survey/<uuid:pk>/duplicate/', views.DuplicateSurveyView.as_view(), name='duplicate-survey'),
    path('survey/<uuid:pk>/export/', views.ExportSurveyResultsView.as_view(), name='export-survey-results'),
]
