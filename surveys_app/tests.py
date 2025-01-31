import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from .models import Survey, Question, Response
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

@pytest.mark.django_db
def test_create_survey_view():
    client = APIClient()

    # Création d'un utilisateur (créateur)
    creator = User.objects.create_user(username="creator", email="creator@example.com", password="password123")
    client.force_authenticate(user=creator)

    # Requête pour créer un sondage
    url = reverse("survey-step1")  # Assure-toi que c'est le bon nom dans tes URL
    data = {
        "title": "Test Survey",
        "start_date": timezone.now().isoformat(),
        "end_date": (timezone.now() + timedelta(days=7)).isoformat()
    }
    response = client.post(url, data)

    assert response.status_code == 201
    assert Survey.objects.count() == 1
    survey = Survey.objects.first()
    assert survey.title == "Test Survey"
    assert survey.creator == creator


@pytest.mark.django_db
def test_answer_survey_view():
    client = APIClient()

    # Création d'un créateur et d'un participant
    creator = User.objects.create_user(username="creator", email="creator@example.com", password="password123")
    participant = User.objects.create_user(username="participant", email="participant@example.com", password="password123")

    # Création d'un sondage et d'une question
    survey = Survey.objects.create(title="Test Survey", creator=creator, start_date=timezone.now(), end_date=timezone.now() + timedelta(days=7))
    question = Question.objects.create(survey=survey, text="What is your favorite color?")

    client.force_authenticate(user=participant)

    # Répondre à la question
    url = reverse("answer-survey", kwargs={"question_id": question.uid})
    data = {"text": "Blue"}
    response = client.post(url, data)

    assert response.status_code == 201
    assert Response.objects.count() == 1
    response_obj = Response.objects.first()
    assert response_obj.question == question
    assert response_obj.text == "Blue"
    assert response_obj.user == participant


@pytest.mark.django_db
def test_edit_survey_permissions():
    client = APIClient()

    # Création d'un créateur et d'un autre utilisateur
    creator = User.objects.create_user(username="creator", email="creator@example.com", password="password123")
    other_user = User.objects.create_user(username="other_user", email="other@example.com", password="password123")

    # Création d'un sondage
    survey = Survey.objects.create(title="Test Survey", creator=creator, start_date=timezone.now(), end_date=timezone.now() + timedelta(days=7))

    # Tentative de modification par un utilisateur non créateur
    client.force_authenticate(user=other_user)
    url = reverse("survey-update", kwargs={"pk": survey.uid})
    data = {"title": "Modified Survey"}
    response = client.put(url, data)

    assert response.status_code == 403  # Permission refusée
    survey.refresh_from_db()
    assert survey.title == "Test Survey"  # Pas de modification


@pytest.mark.django_db
def test_multiple_responses():
    client = APIClient()

    # Création d'un créateur et d'un participant
    creator = User.objects.create_user(username="creator", email="creator@example.com", password="password123")
    participant = User.objects.create_user(username="participant", email="participant@example.com", password="password123")

    # Création d'un sondage et de plusieurs questions
    survey = Survey.objects.create(title="Test Survey", creator=creator, start_date=timezone.now(), end_date=timezone.now() + timedelta(days=7))
    question1 = Question.objects.create(survey=survey, text="What is your favorite color?")
    question2 = Question.objects.create(survey=survey, text="What is your favorite animal?")

    client.force_authenticate(user=participant)

    # Réponse à la première question
    url1 = reverse("answer-survey", kwargs={"question_id": question1.uid})
    response1 = client.post(url1, {"text": "Blue"})
    assert response1.status_code == 201

    # Réponse à la deuxième question
    url2 = reverse("answer-survey", kwargs={"question_id": question2.uid})
    response2 = client.post(url2, {"text": "Dog"})
    assert response2.status_code == 201

    assert Response.objects.count() == 2


@pytest.mark.django_db
def test_unique_response_validation():
    client = APIClient()

    # Création d'un créateur et d'un participant
    creator = User.objects.create_user(username="creator", email="creator@example.com", password="password123")
    participant = User.objects.create_user(username="participant", email="participant@example.com", password="password123")

    # Création d'un sondage et d'une question
    survey = Survey.objects.create(title="Test Survey", creator=creator, start_date=timezone.now(), end_date=timezone.now() + timedelta(days=7))
    question = Question.objects.create(survey=survey, text="What is your favorite color?")

    client.force_authenticate(user=participant)

    # Première réponse
    url = reverse("answer-survey", kwargs={"question_id": question.uid})
    response1 = client.post(url, {"text": "Blue"})
    assert response1.status_code == 201

    # Deuxième réponse (devrait échouer)
    response2 = client.post(url, {"text": "Red"})
    assert response2.status_code == 400  # Erreur de validation
    assert Response.objects.count() == 1

    assert response2.status_code == 400  # Erreur de validation
    assert Response.objects.count() == 1
