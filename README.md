Backend - Portfolio (Django)
=================================

Résumé
------
Ce dossier contient la partie backend du portfolio : une API REST construite avec Django et Django REST Framework. Elle gère les ressources principales du portfolio (utilisateurs, projets, expériences, compétences, blog, etc.), la gestion des médias et l'authentification.

Principales caractéristiques
----------------------------
- API RESTful avec DRF (ViewSets, Serializers, Routers)
- Authentification token/session pour les opérations protégées
- Pagination, recherche et filtrage pour les listes
- Gestion des médias (images, CV, fichiers) en développement via MEDIA_ROOT
- Architecture modulaire : apps séparées (core, users, projects, experiences, skills, blog...)

Stack technique
---------------
- Python 3.x
- Django
- Django REST Framework
- django-filter (filtrage des listes)
- Pillow (gestion des images)
- PostgreSQL ou SQLite (selon configuration)

Installation locale (PowerShell)
-------------------------------
# Création et activation d'un environnement virtuel
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Installation des dépendances
pip install -r requirements.txt

# Copier le fichier d'exemple d'environnement et l'adapter
copy .env.example .env
# éditer .env pour renseigner SECRET_KEY, DATABASE_URL, etc.

Préparer la base de données et exécuter le serveur
-------------------------------------------------
# Appliquer les migrations
python manage.py migrate

# Créer un super-utilisateur (si besoin)
python manage.py createsuperuser

# Lancer le serveur de développement
python manage.py runserver

Configuration additionnelle
---------------------------
- Assurez-vous que 'django_filters' est présent dans INSTALLED_APPS si vous utilisez django-filter.
- Pour le support des images, installez Pillow : pip install Pillow
- MEDIA_ROOT doit exister ou Django le créera automatiquement en développement.

Endpoints API (exemples)
------------------------
Les routes sont exposées sous /api/ (selon portfolio/urls.py)
- GET  /api/experiences/            : lister les expériences (publique)
- GET  /api/experiences/{id}/       : récupérer une expérience (publique)
- POST /api/experiences/            : créer une expérience (authentifié)
- PUT/PATCH /api/experiences/{id}/  : modifier une expérience (authentifié)
- DELETE /api/experiences/{id}/     : supprimer une expérience (authentifié)
- DELETE /api/experiences/delete_all/: supprimer toutes les expériences (authentifié)

Authentification
----------------
Le backend supporte l'authentification pour les opérations de création/modification/suppression. Utilisez les méthodes configurées dans le projet (Token, JWT ou session). Exemple header :
Authorization: Token <votre_token>

Tests
-----
- Les tests unitaires se trouvent dans chaque app (fichiers tests.py).
- Lancer la suite de tests : python manage.py test

Bonnes pratiques
----------------
- Ne pas committer les secrets : utilisez .env et .gitignore
- Versionner les migrations
- Valider les uploads média (taille/type) dans les validators des modèles si nécessaire

Contribuer
----------
- Ouvrir une branche dédiée pour votre feature/fix
- Ajouter ou mettre à jour les tests
- Proposer une Pull Request décrivant le changement

Licence
-------
Référez-vous au fichier LICENSE à la racine du projet (le cas échéant).

Contact
-------
Pour toute question sur le backend, ouvrir une issue dans le dépôt ou contacter le mainteneur du projet.
