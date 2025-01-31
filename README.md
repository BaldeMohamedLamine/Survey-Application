# Application de Sondage

## Description
Ceci est une application de sondage basée sur Django qui permet aux utilisateurs de créer, gérer et participer à des sondages. L'application prend en charge l'authentification des utilisateurs et la gestion des rôles, permettant différentes fonctionnalités pour les créateurs et les participants.

## Fonctionnalités
- Authentification des utilisateurs avec des rôles personnalisés (créateur et participant).
- Création et gestion de sondages par les créateurs.
- Participation aux sondages par les utilisateurs authentifiés.
- Gestion dynamique des questions et des choix au sein des sondages.
- Affichage des résultats des sondages après la date de fin.
- Journalisation et gestion des erreurs pour faciliter le débogage.

## Technologies Utilisées
- Django 4.2
- Python 3.x
- HTML/CSS pour le frontend
- SQLite (par défaut) ou toute autre base de données prise en charge par Django.

## Installation et Démarrage du Projet
### Étape 1 : Cloner le Dépôt
Clonez le dépôt Git en utilisant la commande suivante :
```bash
git clone <url-du-dépôt>
cd <répertoire-du-projet>
```
### Étape 2 : Créer un Environnement Virtuel
Créez un environnement virtuel pour isoler les dépendances du projet :
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows utilisez `venv\Scripts\activate`
```
### Étape 3 : Installer les Dépendances
Installez les packages requis pour le projet en utilisant le fichier `requirements.txt` :
```bash
pip install -r requirements.txt
```
### Étape 4 : Exécuter les Migrations de la Base de Données
Exécutez les migrations pour configurer la base de données :
```bash
python manage.py migrate
```
### Étape 5 : Démarrer le Serveur de Développement
Démarrez le serveur de développement pour accéder à l'application :
```bash
python manage.py runserver
```

## Utilisation
- Accédez à l'application à l'adresse `http://127.0.0.1:8000/`.
- Les utilisateurs peuvent s'inscrire, se connecter, créer des sondages et participer à des sondages existants.

## Remerciements
- Mr Harouna Diallo
- Nimba Hub
- 1000 Tech leaders
- Tutoriels et ressources en ligne pour le développement Django.
