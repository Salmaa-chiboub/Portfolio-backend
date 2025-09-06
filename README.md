# Backend Portfolio - API Django REST

## Aperçu
Ce dépôt contient le backend d'un portfolio professionnel construit avec Django REST Framework. L'API fournit des points de terminaison pour gérer le contenu dynamique d'un portfolio en ligne, y compris les projets, les expériences professionnelles, les compétences et les articles de blog.

## Fonctionnalités principales

### Architecture & Structure
- Architecture modulaire avec applications Django séparées
- API RESTful avec Django REST Framework (DRF)
- Gestion des médias avec Cloudinary
- Base de données PostgreSQL prête pour la production
- Configuration sécurisée avec variables d'environnement

### Sécurité
- Authentification JWT (JSON Web Tokens)
- Protection CSRF et CORS configurée
- Sécurité renforcée avec django-axes
- Validation des entrées utilisateur

### Gestion des médias
- Stockage cloud avec Cloudinary
- Gestion optimisée des images avec Pillow
- Téléchargement sécurisé des fichiers

## Configuration requise

- Python 3.8+
- PostgreSQL 12+
- Compte Cloudinary (pour le stockage des médias)

## Installation

1. **Cloner le dépôt**
   ```bash
   git clone [URL_DU_REPO]
   cd Portfolio-backend
   ```

2. **Configurer l'environnement virtuel**
   ```powershell
   # Windows
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurer les variables d'environnement**
   ```bash
   cp .env.example .env
   # Éditer le fichier .env avec vos configurations
   ```

5. **Configurer la base de données**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **Lancer le serveur de développement**
   ```bash
   python manage.py runserver
   ```

## Points de terminaison API

### Authentification
- `POST /api/token/` - Obtenir un token JWT
- `POST /api/token/refresh/` - Rafraîchir un token JWT

### Applications principales

#### Blog (`/api/blog/`)
- Gestion des articles de blog
- Commentaires et catégories
- Médias associés

#### Compétences (`/api/skills/`)
- Gestion des compétences techniques
- Catégorisation par domaine
- Niveaux de maîtrise

#### Projets (`/api/projects/`)
- Portfolio des projets
- Détails techniques et démonstrations
- Liens vers les dépôts et démos

#### Expériences (`/api/experiences/`)
- Parcours professionnel
- Réalisations et responsabilités
- Références et preuves

## Variables d'environnement

Créez un fichier `.env` à la racine avec les variables suivantes :

```
SECRET_KEY=votre_secret_key
DEBUG=True
DATABASE_URL=postgres://user:password@localhost:5432/portfolio
django_cloudinary_url=cloudinary://key:secret@cloud_name
```

## Tests

```bash
# Lancer tous les tests
python manage.py test

# Lancer les tests d'une application spécifique
python manage.py test blog
```

## Déploiement

### Prérequis
- Compte sur un service de déploiement (Heroku, Railway, etc.)
- Base de données PostgreSQL en production
- Configuration Cloudinary pour les médias

### Étapes de déploiement
1. Configurer les variables d'environnement en production
2. Désactiver le mode debug
3. Configurer un nom de domaine et SSL
4. Configurer un serveur WSGI (Gunicorn, uWSGI)
5. Configurer un serveur web (Nginx, Apache)

## Contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/ma-nouvelle-fonctionnalite`)
3. Commiter les changements (`git commit -am 'Ajouter une fonctionnalité'`)
4. Pousser vers la branche (`git push origin feature/ma-nouvelle-fonctionnalite`)
5. Ouvrir une Pull Request

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## Contact

Pour toute question ou suggestion, veuillez ouvrir une issue sur le dépôt ou contacter le mainteneur du projet.
