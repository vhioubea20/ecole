# Gestion scolaire

Application web Django en français pour suivre les élèves et gérer les accès du personnel. Les données sont enregistrées dans une base SQLite locale.

## Fonctionnalités

- Connexion et déconnexion avec les mécanismes d'authentification Django.
- Tableau de bord avec les effectifs, classes et inscriptions récentes.
- Recherche et filtrage des dossiers élèves; création, modification et suppression réservées au personnel.
- Inscription avec matricule automatique, choix de classe, photo facultative et coordonnées facultatives du responsable.
- Gestion des classes (création, modification, suppression); la suppression est bloquée si des élèves y sont inscrits.
- Gestion des frais par classe et année scolaire: un montant d'inscription et un montant de scolarité au maximum pour chaque couple classe/année.
- Suivi de scolarité par classe avec échéances d'octobre à juin, historique individuel et gestion des paiements.
- Gestion des comptes, des rôles et de leur activation, réservée au personnel.
- Rôle Admin avec tous les droits; permissions scolaires sélectionnables pour les comptes Utilisateur; photo de profil et courriel facultatif.
- Interface responsive et administration Django disponible sous `/admin/`.

## Installation sous Windows

Depuis le dossier du projet, ouvrez PowerShell. Python 3.10 ou plus récent est requis.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Ouvrez ensuite `http://127.0.0.1:8000/` et connectez-vous avec le compte superutilisateur créé. La commande `createsuperuser` crée le premier administrateur; les autres comptes peuvent ensuite être ajoutés depuis **Utilisateurs**.

Si PowerShell bloque l'activation de l'environnement virtuel, autorisez-la pour la session courante avec `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, puis réactivez l'environnement.

## Vérifications

```powershell
python manage.py check
python manage.py test
```

La clé secrète de développement configurée par défaut ne doit pas être utilisée en production. Pour un déploiement, définissez `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0` et `DJANGO_ALLOWED_HOSTS`, puis configurez HTTPS et une base de données adaptée.
