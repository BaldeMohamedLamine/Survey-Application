import uuid
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from account.models import User
from django.utils.timezone import now


class Survey(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_published = models.BooleanField(default=False)
    image = models.ImageField(upload_to='', null=True, blank=True)


    def is_editable(self):
        return not self.is_published

    def is_active(self):
        return self.start_date <= timezone.now() <= self.end_date

    def has_responded(self, user):
        return Response.objects.filter(survey=self, user=user).exists()

    def clean(self):
        if self.start_date >= self.end_date:
            raise ValidationError("La date de fin doit être postérieure à la date de début.")
        super().clean()

    def can_participate(self, user):
        if not user.is_authenticated:
            return False
        if not self.is_published:
            return False
        now = timezone.now()
        if now < self.start_date or now > self.end_date:
            return False
        return not Response.objects.filter(survey=self, user=user).exists()

    def get_participation_status(self, user):
        """Retourne le statut de participation pour l'affichage"""
        if not user.is_authenticated:
            return "login_required"

        now = timezone.now()
        if not self.is_published:
            return "not_published"
        if now < self.start_date:
            return "not_started"
        if now > self.end_date:
            return "ended"
        if self.has_responded(user):
            return "already_responded"
        return "can_participate"

    def can_view_results(self, user):
        """Vérifie si l'utilisateur peut voir les résultats"""
        now = timezone.now()
        return (
            user.is_authenticated and (
                user == self.creator or
                now > self.end_date
            )
        )
    @property
    def is_active(self):
        today = now()
        return self.is_published and self.start_date <= today <= self.end_date

    def __str__(self):
        return self.title


class Question(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    QUESTION_TYPES = [
        ("single", "Réponse unique"),
        ("multiple", "Réponse multiple"),
        ("text", "Réponse texte"),
    ]
    text = models.TextField()
    type = models.CharField(max_length=10, choices=QUESTION_TYPES)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name="questions")

    def __str__(self):
        return self.text


class Choice(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    text = models.CharField(max_length=200)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')

    def __str__(self):
        return self.text


class Response(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'survey']
        ordering = ['-created_at']

    def clean(self):
        if not self.survey.is_published:
            raise ValidationError("Le sondage n'est pas publié.")
        if not self.survey.is_active():
            raise ValidationError("Le sondage n'est pas actif.")
        if Response.objects.filter(survey=self.survey, user=self.user).exists():
            raise ValidationError("L'utilisateur a déjà répondu à ce sondage.")
        if self.user == self.survey.creator:
            raise ValidationError("Le créateur du sondage ne peut pas y répondre.")
        super().clean()

    def __str__(self):
        return f"Réponse de {self.user} pour {self.survey}"


class Answer(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE, null=True, blank=True)
    text = models.TextField(null=True, blank=True)

    def clean(self):
        super().clean()
        if self.question.type in ['single', 'multiple'] and not self.choice:
            raise ValidationError({'choice': 'Un choix est requis pour ce type de question'})
        if self.question.type == 'text' and not self.text:
            raise ValidationError({'text': 'Une réponse textuelle est requise pour ce type de question'})
        if self.question.type == 'text' and self.choice:
            raise ValidationError({'choice': 'Un choix ne doit pas être spécifié pour une question textuelle'})
        if self.question.type in ['single', 'multiple'] and self.text:
            raise ValidationError({'text': 'Une réponse textuelle ne doit pas être spécifiée pour ce type de question'})

    def __str__(self):
        if self.choice:
            return f"{self.question.text} - {self.choice.text}"
        return f"{self.question.text} - {self.text}"
