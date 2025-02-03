import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from .models import Survey, Question, Response ,Choice
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
import uuid



User = get_user_model()

class SurveyCreateTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password', email="creator@example.com", role='creator')
        self.user.save()

    def test_create_survey_view(self):
        self.client.login(username='testuser', password='password')

        data = {
            'title': 'Test Survey',
            'description': 'Une description de test',
            'start_date': '2025-02-01T12:00',
            'end_date': '2025-02-02T12:00',
        }

        response = self.client.post(reverse('surveys_app:survey-step1'), data)

        self.assertEqual(response.status_code, 302)
        survey = Survey.objects.last() 
        survey_uid = survey.uid  
        self.assertRedirects(response, reverse('surveys_app:survey-step2', kwargs={'uid': survey_uid}))

class AnswerSurveyTestCase(TestCase):
    def setUp(self):
        self.participant = User.objects.create_user(username="participant", password="password123",email="participant@example.com", role='participant')
        self.survey = Survey.objects.create(
        title="Test Survey",
        description="Test description",  
        creator=self.participant,  
        start_date=timezone.now(),  
        end_date=timezone.now() + timedelta(days=7), 
        is_published=True  
    )

    def test_answer_survey_view(self):
        logged_in = self.client.login(username="participant", password="password123")
        self.assertTrue(logged_in, "L'utilisateur n'a pas pu se connecter.")

        response = self.client.post(
            reverse("surveys_app:survey_response", kwargs={"uid": self.survey.uid}),
            {"question_1": "Blue"}
        )

        self.assertEqual(response.status_code, 302)


class SurveyPermissionsTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.creator = User.objects.create_user(
            username="creator", email="creator@example.com", password="password123", role='creator'
        )
        self.other_user = User.objects.create_user(
            username="other_user", email="other_user@example.com", password="password123", role='other_user'
        )
        self.survey = Survey.objects.create(
            title="Test Survey",
            creator=self.creator,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=7),
        )
        self.url = reverse("surveys_app:survey-update", kwargs={"pk": self.survey.uid})

    def test_edit_survey_permissions(self):
        self.client.login(username="other_user", password="password123")
        data = {"title": "Modified Survey"}
        response = self.client.put(self.url, data)

        self.assertEqual(response.status_code, 403)

        self.survey.refresh_from_db()
        self.assertEqual(self.survey.title, "Test Survey")  
class MultipleResponsesTestCase(TestCase):
    def setUp(self):
        """Créer un utilisateur et un sondage pour le test."""
        self.user = User.objects.create_user(username="testuser", password="password123",email="testuser@example.com")
        self.client.login(username="testuser", password="password123")

        self.survey = Survey.objects.create(
            uid=uuid.uuid4(), 
            title="Test Survey", 
            is_published = True,
            creator=self.user, 
            start_date=timezone.now(), 
            end_date=timezone.now() + timedelta(days=7)
            
        )

        self.question = Question.objects.create(
            survey=self.survey, 
            text="What is your favorite color?", 
            type="single"
        )

        self.choice1 = Choice.objects.create(question=self.question, text="Blue", uid=uuid.uuid4())
        self.choice2 = Choice.objects.create(question=self.question, text="Red", uid=uuid.uuid4())

        self.url = reverse("surveys_app:survey_response", kwargs={"uid": self.survey.uid})

    def test_multiple_responses(self):
        """Tester qu'un utilisateur ne peut pas répondre plusieurs fois au sondage."""
        response1 = self.client.post(self.url, {"question_{}".format(self.question.uid): str(self.choice1.uid)})
        self.assertEqual(response1.status_code, 302) 

        self.assertTrue(Response.objects.filter(survey=self.survey, user=self.user).exists())

        response2 = self.client.post(self.url, {"question_{}".format(self.question.uid): str(self.choice2.uid)}, follow=True)
        self.assertRedirects(response2, reverse("surveys_app:home")) 