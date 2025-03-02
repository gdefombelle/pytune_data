# Documentation de pytune_data

## Introduction
`pytune_data` est un package Python permettant la gestion et l'interaction avec une base de données PostgreSQL via Tortoise ORM. Il est conçu pour s'intégrer avec `pytune_configuration`, qui gère les pools de connexions. Aucune configuration `.env` n'est requise dans `pytune_data`.

## Installation

```sh
pip install pytune_data
```

## Configuration
La configuration de la base de données est gérée par `pytune_configuration`. `pytune_data` récupère les informations de connexion directement à partir de la classe `Config`.

## Initialisation de la base de données

Pour initialiser la connexion à la base de données PostgreSQL avec Tortoise ORM, utilisez :

```python
from pytune_data.db import init
import asyncio

asyncio.run(init())
```

## Fermeture de la connexion

Pour fermer proprement les connexions à la base de données :

```python
from pytune_data.db import close
import asyncio

asyncio.run(close())
```

## Configuration ORM de Tortoise

Le package génère dynamiquement la configuration de Tortoise ORM :

```python
from pytune_data.db import get_orm_connection

config = get_orm_connection()
print(config)
```

## Gestion des logs

Les logs sont gérés via `pytune_logger`, avec `logger_admin` pour la supervision des connexions.

## Exemple d'utilisation

Voici un exemple d'utilisation dans une application FastAPI :

```python
from fastapi import FastAPI
from pytune_data.db import init, close
import asyncio

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await init()

@app.on_event("shutdown")
async def shutdown_event():
    await close()

@app.get("/")
async def read_root():
    return {"message": "Database is connected!"}
```

## Conclusion

`pytune_data` simplifie la gestion de la connexion à PostgreSQL via Tortoise ORM en intégrant une configuration centralisée et un logging efficace. Il est optimisé pour être utilisé avec `pytune_configuration` sans nécessiter de fichier `.env`.

