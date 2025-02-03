from .settings import *
import dj_database_url
import environ
import os

env = environ.Env(
    # définir le casting, valeur par défaut
    DEBUG=(bool, False)
)
# Définir le répertoire de base du proje
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Prendre les variables d'environnement du fichier .env
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY')

DEBUG = env('DEBUG')
DJANGO_SETTINGS_MODULE =env('DJANGO_SETTINGS_MODULE')
    
ALLOWED_HOSTS = env('ALLOWED_HOSTS').split(',') 
DATABASES = {'default':dj_database_url.config(conn_health_checks=True)}