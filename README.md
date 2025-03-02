# Pytune Data

Pytune Data est un package Python centralisant l'accès aux données de l'application Pytune. Il offre une interface unifiée pour interagir avec la base de données, en utilisant Tortoise-ORM pour la gestion des modèles et des requêtes asynchrones.

## Fonctionnalités

- **Gestion des modèles de données** : Définition des entités et relations de la base.
- **CRUD génériques** : Création, lecture, mise à jour et suppression des objets.
- **Services spécialisés** : Fourniture de services métier pour traiter les données spécifiques.
- **Connexion simplifiée** : Initialisation et fermeture automatique des connexions à la base de données.

## Installation

```sh
pip install pytune_data
```

## Configuration

Le package nécessite une base de données PostgreSQL accessible via Tortoise-ORM. Pour l'utiliser, configure la connexion dans un fichier de configuration compatible avec Tortoise.

Exemple de configuration :

```python
DATABASE_URL = "postgres://user:password@localhost:5432/mydatabase"
```

## Utilisation

### Initialisation
Avant d'utiliser les services, il faut initialiser la connexion :

```python
from pytune_data.db import init
await init()
```

### Exemple : Récupération de données

```python
from pytune_data.piano_data_service import get_manufacturers

manufacturers = await get_manufacturers()
print(manufacturers)
```

## Structure du projet

- `pytune_data/models.py` : Définition des modèles de données.
- `pytune_data/schemas.py` : Définition des schémas Pydantic pour validation.
- `pytune_data/crud.py` : Fonctions CRUD de base.
- `pytune_data/db.py` : Gestion de la connexion à la base de données.
- `pytune_data/services/` : Services spécialisés d'accès aux données.

## Contribution

Les contributions sont les bienvenues ! Clone le repo et soumets une PR.

```sh
git clone https://github.com/gdefombelle/pytune_data.git
cd pytune_data
```

## Licence

Ce projet est sous licence MIT.

