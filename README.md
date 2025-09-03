# Agrégateur PQR - Railway Deployment

## Description
Agrégateur de nouvelles de la Presse Quotidienne Régionale française.
Collecte automatique de 68 sources RSS couvrant toutes les régions françaises.

## Fonctionnalités
- ✅ Collecte RSS en temps réel de 68 sources
- ✅ 18 régions françaises couvertes
- ✅ Interface moderne et responsive
- ✅ Recherche dans les articles
- ✅ Collecte automatique toutes les 15 minutes
- ✅ API REST complète

## Sources
- **42 journaux PQR** (Le Parisien, Ouest-France, Sud Ouest, etc.)
- **18 radios France Bleu** (une par région)
- **8 médias locaux** spécialisés

## Déploiement sur Railway

### 1. Prérequis
- Compte Railway.app
- Repository Git

### 2. Déploiement
1. Connectez votre repository à Railway
2. Railway détecte automatiquement Python
3. Les dépendances sont installées via `requirements.txt`
4. L'application démarre avec `gunicorn app:app`

### 3. Configuration
Aucune configuration supplémentaire nécessaire.
La base de données SQLite est créée automatiquement.

### 4. Fonctionnement
- Collecte initiale au démarrage
- Collecte automatique toutes les 15 minutes
- Interface accessible sur l'URL Railway

## API Endpoints
- `GET /api/regions` - Liste des régions
- `GET /api/regions/{region}/articles` - Articles d'une région
- `GET /api/articles/top` - Top articles
- `GET /api/stats` - Statistiques
- `GET /api/search?q={query}` - Recherche
- `POST /api/collect` - Déclencher collecte manuelle

## Technologies
- **Backend**: Python 3.11, Flask, SQLite
- **Frontend**: HTML5, CSS3, JavaScript ES6
- **Déploiement**: Railway.app, Gunicorn
- **RSS**: feedparser, requests

## Auteur
Créé pour l'agrégation d'actualités régionales françaises.

