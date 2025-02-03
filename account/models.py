from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.crypto import get_random_string

class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, role='participant'):
        if not email:
            raise ValueError('Les utilisateurs doivent avoir une adresse e-mail')
        user = self.model(username=username, email=self.normalize_email(email), role=role)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None):
        user = self.create_user(username, email, password)  
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('creator', 'Créateur'),
        ('participant', 'Participant'),
    ]
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=11, choices=ROLE_CHOICES, default='participant')
    email_confirmed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    confirmation_token = models.CharField(max_length=64, blank=True, null=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    objects = UserManager()

    def get_by_natural_key(self, username):
        return self.get(username=username)

    def generate_confirmation_token(self):
        self.confirmation_token = get_random_string(length=64)
        self.save()

    def __str__(self):
        return self.username

    def is_creator(self):
        return self.role == 'creator'

    def is_participant(self):
        return self.role == 'participant'

    def created_surveys_count(self):
        from surveys_app.models import Survey 
        return Survey.objects.filter(creator=self).count()

    def submitted_responses_count(self):
        from surveys_app.models import Response  
        return Response.objects.filter(user=self).count()


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    additional_info = models.TextField(blank=True, null=True)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if not hasattr(instance, 'profile'):
        Profile.objects.create(user=instance)
    instance.profile.save()
