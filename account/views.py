from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils.timezone import now
import logging

from .forms import CustomUserCreationForm
from .forms import UserUpdateForm
from .models import User

# Configurer le logger
logger = logging.getLogger(__name__)

def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.password = make_password(form.cleaned_data['password'])  # Hachage du mot de passe
            user.is_active = False  # Désactiver jusqu'à confirmation de l'email
            user.generate_confirmation_token()
            user.save()
            logger.info(f"Utilisateur enregistré : {user.username}")

            # Envoyer un email de confirmation
            confirmation_url = request.build_absolute_uri(
                f"/account/confirm-email/{user.confirmation_token}/"
            )
            send_mail(
                "Confirmez votre adresse e-mail",
                f"Cliquez ici pour confirmer votre email : {confirmation_url}",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
            )
            messages.success(request, "Votre compte a été créé. Vérifiez votre email pour confirmer.")
            return redirect("account:login")
        else:
            logger.error(f"Formulaire invalide : {form.errors}")
    else:
        form = CustomUserCreationForm()

    return render(request, "account/register.html", {"form": form})

def custom_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_page = request.GET.get('next', 'surveys_app:home')
            messages.success(request, "Bienvenue, vous êtes connecté !")
            return redirect(next_page)
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    else:
        form = AuthenticationForm()

    return render(request, "account/login.html", {"form": form})


def confirm_email(request, token):
    user = get_object_or_404(User, confirmation_token=token)
    user.email_confirmed = True
    user.is_active = True
    user.confirmation_token = ""
    user.save()

    messages.success(request, "Votre email a été confirmé. Vous pouvez vous connecter.")
    return redirect("account:login")

@login_required
def profile(request):
    user = request.user
    created_surveys = user.created_surveys_count()
    submitted_responses = user.submitted_responses_count()
    
    context = {
        'user': user,
        'created_surveys': created_surveys,
        'submitted_responses': submitted_responses,
    }
    return render(request, 'account/profile.html', context)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre profil a été mis à jour avec succès.')
            return redirect('account:profile')
    else:
        form = UserUpdateForm(instance=request.user)

    return render(request, 'account/edit_profile.html', {'form': form})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Votre mot de passe a été modifié avec succès.')
            return redirect('account:profile')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'account/change_password.html', {'form': form})

#Demander un lien de réinitialisation
def request_password_reset(request):
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = User.objects.get(email=email)
            user.generate_password_reset_token()
            reset_url = request.build_absolute_uri(f"/account/reset-password/{user.reset_password_token}/")
            send_mail(
                "Réinitialisation de votre mot de passe",
                f"Cliquez ici pour réinitialiser votre mot de passe : {reset_url}",
                settings.DEFAULT_FROM_EMAIL,
                [email],
            )
            messages.success(request, "Un email de réinitialisation a été envoyé.")
        except User.DoesNotExist:
            messages.error(request, "Aucun compte trouvé avec cet email.")
    return render(request, "account/request_password_reset.html")


def reset_password(request, token):
    try:
        user = User.objects.get(reset_password_token=token)
        if user.reset_token_expires_at < now():
            messages.error(request, "Le lien de réinitialisation a expiré.")
            return redirect("account:request_password_reset")
    except User.DoesNotExist:
        messages.error(request, "Lien de réinitialisation invalide.")
        return redirect("account:request_password_reset")

    if request.method == "POST":
        password = request.POST.get("password")
        password_confirm = request.POST.get("password_confirm")
        if password == password_confirm:
            user.password = make_password(password)
            user.reset_password_token = None
            user.reset_token_expires_at = None
            user.save()
            messages.success(request, "Votre mot de passe a été réinitialisé.")
            return redirect("account:login")
        else:
            messages.error(request, "Les mots de passe ne correspondent pas.")

    return render(request, "account/reset_password.html", {"token": token})

def logout_view(request):
    logout(request)
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect('account:login')
