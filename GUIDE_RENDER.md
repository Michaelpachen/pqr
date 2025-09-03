# 🚀 Guide de déploiement sur Render.com

## Étapes de déploiement

### 1. Préparer le code
✅ **Déjà fait !** Tous les fichiers sont prêts dans l'archive.

### 2. Créer un compte Render
1. Allez sur **https://render.com**
2. Cliquez sur **"Get Started for Free"**
3. Créez un compte (GitHub recommandé)

### 3. Créer un nouveau service Web
1. Dans le dashboard Render, cliquez **"New +"**
2. Sélectionnez **"Web Service"**
3. Choisissez **"Build and deploy from a Git repository"**

### 4. Connecter votre repository
**Option A - GitHub (RECOMMANDÉ) :**
1. Créez un repository GitHub
2. Uploadez tous les fichiers de l'archive
3. Connectez le repository à Render

**Option B - Upload direct :**
1. Sélectionnez **"Public Git Repository"**
2. Utilisez l'URL de votre repository

### 5. Configuration du service
```
Name: pqr-aggregator
Region: Frankfurt (EU) ou Oregon (US)
Branch: main
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
```

### 6. Variables d'environnement (optionnel)
```
PYTHON_VERSION=3.11.0
```

### 7. Ajouter une base de données PostgreSQL (GRATUIT)
1. Dans le dashboard, cliquez **"New +"**
2. Sélectionnez **"PostgreSQL"**
3. Nom: `pqr-database`
4. Plan: **Free** (100MB, suffisant)
5. Région: **Même que le service web**

### 8. Connecter la base de données
1. Retournez dans votre service web
2. Allez dans **"Environment"**
3. Ajoutez la variable : `DATABASE_URL` = `[URL de votre PostgreSQL]`
4. L'URL se trouve dans les détails de votre base PostgreSQL

### 9. Déployer
1. Cliquez **"Create Web Service"**
2. **Attendez 3-5 minutes** pour le build
3. Votre site sera disponible sur `https://votre-app.onrender.com`

## ✅ Fonctionnalités après déploiement

- **Collecte RSS automatique** toutes les 15 minutes
- **68 sources** de presse régionale française
- **Interface moderne** responsive
- **Recherche** dans tous les articles
- **API REST** complète
- **Base de données PostgreSQL** gratuite

## 🔧 Dépannage

**Problème de build :**
- Vérifiez que `requirements.txt` est présent
- Vérifiez la version Python dans `runtime.txt`

**Problème de base de données :**
- Vérifiez que `DATABASE_URL` est correctement configurée
- L'app fonctionne aussi sans PostgreSQL (SQLite local)

**Collecte RSS qui ne fonctionne pas :**
- Attendez 15 minutes après le déploiement
- Vérifiez les logs dans Render dashboard

## 📊 Limites du plan gratuit Render

- **750 heures/mois** (suffisant)
- **Base PostgreSQL** : 100MB (largement suffisant)
- **Mise en veille** après 15min d'inactivité
- **Réveil automatique** à la première visite

## 🎯 URL finale

Votre agrégateur sera accessible sur :
`https://votre-nom-app.onrender.com`

**Exemple :** `https://pqr-aggregator-abc123.onrender.com`

