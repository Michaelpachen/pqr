#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import feedparser
import requests
from urllib.parse import urljoin
import threading
import time
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# Route principale pour servir l'index
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

# Configuration de la base de données
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    # PostgreSQL sur Render
    import psycopg2
    from urllib.parse import urlparse
    DATABASE = DATABASE_URL
    USE_POSTGRES = True
else:
    # SQLite en local
    DATABASE = 'pqr_articles.db'
    USE_POSTGRES = False

# Sources RSS complètes - 68 sources
RSS_SOURCES = {
    'Auvergne-Rhône-Alpes': [
        {'name': 'Le Dauphiné libéré', 'url': 'https://www.ledauphine.com/rss'},
        {'name': 'Le Progrès', 'url': 'https://www.leprogres.fr/rss'},
        {'name': 'La Montagne', 'url': 'https://www.lamontagne.fr/rss'},
        {'name': 'L\'Éveil de la Haute-Loire', 'url': 'https://www.leveil.fr/rss'},
        {'name': 'France Bleu Isère', 'url': 'https://www.francebleu.fr/rss/a-la-une/isere'},
        {'name': 'Lyon Mag', 'url': 'https://www.lyonmag.com/rss.xml'}
    ],
    'Bourgogne-Franche-Comté': [
        {'name': 'Le Journal de Saône-et-Loire', 'url': 'https://www.lejsl.com/rss'},
        {'name': 'Le Bien public', 'url': 'https://www.bienpublic.com/rss'},
        {'name': 'L\'Yonne républicaine', 'url': 'https://www.lyonne.fr/rss'},
        {'name': 'L\'Est républicain', 'url': 'https://www.estrepublicain.fr/rss'},
        {'name': 'France Bleu Bourgogne', 'url': 'https://www.francebleu.fr/rss/a-la-une/bourgogne'}
    ],
    'Bretagne': [
        {'name': 'Ouest-France Bretagne', 'url': 'https://www.ouest-france.fr/rss-en-continu.xml'},
        {'name': 'Le Télégramme', 'url': 'https://www.letelegramme.fr/rss.xml'},
        {'name': 'France Bleu Breizh Izel', 'url': 'https://www.francebleu.fr/rss/a-la-une/breizh-izel'}
    ],
    'Centre-Val de Loire': [
        {'name': 'La République du Centre', 'url': 'https://www.larep.fr/rss'},
        {'name': 'Le Berry républicain', 'url': 'https://www.leberry.fr/rss'},
        {'name': 'L\'Écho républicain', 'url': 'https://www.lechorepublicain.fr/rss'},
        {'name': 'France Bleu Berry', 'url': 'https://www.francebleu.fr/rss/a-la-une/berry'}
    ],
    'Corse': [
        {'name': 'Corse-Matin', 'url': 'https://www.corsematin.com/rss'},
        {'name': 'France Bleu RCFM', 'url': 'https://www.francebleu.fr/rss/a-la-une/rcfm'}
    ],
    'Grand Est': [
        {'name': 'Les Dernières Nouvelles d\'Alsace', 'url': 'https://www.dna.fr/rss'},
        {'name': 'L\'Alsace', 'url': 'https://www.lalsace.fr/rss'},
        {'name': 'Le Républicain lorrain', 'url': 'https://www.republicain-lorrain.fr/rss'},
        {'name': 'L\'Union', 'url': 'https://www.lunion.fr/rss'},
        {'name': 'Vosges Matin', 'url': 'https://www.vosgesmatin.fr/rss'},
        {'name': 'France Bleu Alsace', 'url': 'https://www.francebleu.fr/rss/a-la-une/alsace'},
        {'name': 'France Bleu Lorraine', 'url': 'https://www.francebleu.fr/rss/a-la-une/lorraine-nord'}
    ],
    'Hauts-de-France': [
        {'name': 'La Voix du Nord', 'url': 'https://www.lavoixdunord.fr/rss'},
        {'name': 'Le Courrier picard', 'url': 'https://www.courrier-picard.fr/rss'},
        {'name': 'Nord éclair', 'url': 'https://www.nordeclair.fr/rss'},
        {'name': 'Nord Littoral', 'url': 'https://www.nordlittoral.fr/rss'},
        {'name': 'France Bleu Nord', 'url': 'https://www.francebleu.fr/rss/a-la-une/nord'}
    ],
    'Île-de-France': [
        {'name': 'Le Parisien', 'url': 'https://www.leparisien.fr/rss.xml'},
        {'name': 'France Bleu Paris', 'url': 'https://www.francebleu.fr/rss/a-la-une/107-1'},
        {'name': 'Actu.fr Paris', 'url': 'https://actu.fr/ile-de-france/rss'}
    ],
    'Normandie': [
        {'name': 'La Presse de la Manche', 'url': 'https://www.lamanchelibre.fr/rss'},
        {'name': 'Paris Normandie', 'url': 'https://www.paris-normandie.fr/rss'},
        {'name': 'France Bleu Normandie', 'url': 'https://www.francebleu.fr/rss/a-la-une/normandie-caen'}
    ],
    'Nouvelle-Aquitaine': [
        {'name': 'Sud Ouest', 'url': 'https://www.sudouest.fr/rss.xml'},
        {'name': 'Charente libre', 'url': 'https://www.charentelibre.fr/rss'},
        {'name': 'Le Populaire du Centre', 'url': 'https://www.lepopulaire.fr/rss'},
        {'name': 'La Nouvelle République des Pyrénées', 'url': 'https://www.nrpyrenees.fr/rss'},
        {'name': 'France Bleu Gironde', 'url': 'https://www.francebleu.fr/rss/a-la-une/gironde'},
        {'name': 'France Bleu Périgord', 'url': 'https://www.francebleu.fr/rss/a-la-une/perigord'}
    ],
    'Occitanie': [
        {'name': 'La Dépêche du Midi', 'url': 'https://www.ladepeche.fr/rss.xml'},
        {'name': 'Midi libre', 'url': 'https://www.midilibre.fr/rss'},
        {'name': 'L\'Indépendant', 'url': 'https://www.lindependant.fr/rss'},
        {'name': 'Centre Presse', 'url': 'https://www.centrepresseaveyron.fr/rss'},
        {'name': 'France Bleu Toulouse', 'url': 'https://www.francebleu.fr/rss/a-la-une/toulouse'},
        {'name': 'France Bleu Hérault', 'url': 'https://www.francebleu.fr/rss/a-la-une/herault'}
    ],
    'Pays de la Loire': [
        {'name': 'Le Courrier de l\'Ouest', 'url': 'https://www.courrierdelouest.fr/rss'},
        {'name': 'Le Maine libre', 'url': 'https://www.ouest-france.fr/maine-libre/rss.xml'},
        {'name': 'Presse-Océan', 'url': 'https://www.presseocean.fr/rss'},
        {'name': 'France Bleu Loire Océan', 'url': 'https://www.francebleu.fr/rss/a-la-une/loire-ocean'}
    ],
    'Provence-Alpes-Côte d\'Azur': [
        {'name': 'La Provence', 'url': 'https://www.laprovence.com/rss/une.xml'},
        {'name': 'Nice-Matin', 'url': 'https://www.nicematin.com/rss'},
        {'name': 'Var-Matin', 'url': 'https://www.varmatin.com/rss'},
        {'name': 'France Bleu Azur', 'url': 'https://www.francebleu.fr/rss/a-la-une/azur'}
    ],
    'Guadeloupe': [
        {'name': 'France-Antilles Guadeloupe', 'url': 'https://www.franceantilles.fr/guadeloupe/rss.xml'},
        {'name': 'France Bleu Guadeloupe', 'url': 'https://www.francebleu.fr/rss/a-la-une/guadeloupe'}
    ],
    'Martinique': [
        {'name': 'France-Antilles Martinique', 'url': 'https://www.franceantilles.fr/martinique/rss.xml'},
        {'name': 'France Bleu Martinique', 'url': 'https://www.francebleu.fr/rss/a-la-une/martinique'}
    ],
    'Guyane': [
        {'name': 'La Presse de Guyane', 'url': 'https://www.franceguyane.fr/rss.xml'},
        {'name': 'France Bleu Guyane', 'url': 'https://www.francebleu.fr/rss/a-la-une/guyane'}
    ],
    'La Réunion': [
        {'name': 'Le Journal de l\'île de La Réunion', 'url': 'https://www.clicanoo.re/rss.xml'},
        {'name': 'Le Quotidien de la Réunion', 'url': 'https://www.lequotidien.re/rss.xml'},
        {'name': 'France Bleu La Réunion', 'url': 'https://www.francebleu.fr/rss/a-la-une/la-reunion'}
    ],
    'Mayotte': [
        {'name': 'Mayotte Hebdo', 'url': 'https://lejournaldemayotte.yt/feed/'}
    ]
}

def init_database():
    """Initialiser la base de données"""
    if USE_POSTGRES:
        # PostgreSQL
        conn = psycopg2.connect(DATABASE)
        cursor = conn.cursor()
        
        # Table des articles
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id SERIAL PRIMARY KEY,
                titre TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                description TEXT,
                source TEXT NOT NULL,
                region TEXT NOT NULL,
                date_publication TIMESTAMP,
                date_collecte TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table des collectes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collectes (
                id SERIAL PRIMARY KEY,
                date_collecte TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                nb_sources_total INTEGER,
                nb_sources_ok INTEGER,
                nb_articles_nouveaux INTEGER,
                details TEXT
            )
        ''')
        
        # Index pour les performances
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_region ON articles(region)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_date ON articles(date_publication DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url)')
        
    else:
        # SQLite
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Table des articles
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titre TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                description TEXT,
                source TEXT NOT NULL,
                region TEXT NOT NULL,
                date_publication DATETIME,
                date_collecte DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table des collectes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collectes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_collecte DATETIME DEFAULT CURRENT_TIMESTAMP,
                nb_sources_total INTEGER,
                nb_sources_ok INTEGER,
                nb_articles_nouveaux INTEGER,
                details TEXT
            )
        ''')
        
        # Index pour les performances
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_region ON articles(region)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_date ON articles(date_publication DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url)')
    
    conn.commit()
    conn.close()
    logger.info("Base de données initialisée")

def fetch_rss_feed(source_name, url, region):
    """Récupérer et parser un flux RSS"""
    try:
        logger.info(f"Collecte {source_name} ({region}): {url}")
        
        # Headers pour éviter les blocages
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/rss+xml, application/xml, text/xml, */*',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache'
        }
        
        # Récupérer le flux avec timeout
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parser avec feedparser
        feed = feedparser.parse(response.content)
        
        if feed.bozo and feed.bozo_exception:
            logger.warning(f"Avertissement parsing {source_name}: {feed.bozo_exception}")
        
        articles = []
        for entry in feed.entries[:20]:  # Limiter à 20 articles par source
            try:
                # Extraire les données
                titre = entry.get('title', '').strip()
                link = entry.get('link', '').strip()
                description = entry.get('summary', entry.get('description', '')).strip()
                
                # Date de publication
                date_pub = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    date_pub = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    date_pub = datetime(*entry.updated_parsed[:6])
                else:
                    date_pub = datetime.now()
                
                # Nettoyer la description
                if description:
                    # Supprimer les balises HTML basiques
                    import re
                    description = re.sub(r'<[^>]+>', '', description)
                    description = description.replace('&nbsp;', ' ').replace('&amp;', '&')
                    if len(description) > 300:
                        description = description[:300] + '...'
                
                if titre and link:
                    articles.append({
                        'titre': titre,
                        'url': link,
                        'description': description,
                        'source': source_name,
                        'region': region,
                        'date_publication': date_pub
                    })
                    
            except Exception as e:
                logger.error(f"Erreur parsing article {source_name}: {e}")
                continue
        
        logger.info(f"✅ {source_name}: {len(articles)} articles récupérés")
        return articles
        
    except requests.exceptions.Timeout:
        logger.error(f"❌ {source_name}: Timeout")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ {source_name}: Erreur réseau - {e}")
        return []
    except Exception as e:
        logger.error(f"❌ {source_name}: Erreur - {e}")
        return []

def save_articles(articles):
    """Sauvegarder les articles en base"""
    if not articles:
        return 0
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    nouveaux = 0
    for article in articles:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO articles 
                (titre, url, description, source, region, date_publication)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                article['titre'],
                article['url'],
                article['description'],
                article['source'],
                article['region'],
                article['date_publication']
            ))
            
            if cursor.rowcount > 0:
                nouveaux += 1
                
        except Exception as e:
            logger.error(f"Erreur sauvegarde article: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    return nouveaux

def collect_all_feeds():
    """Collecter tous les flux RSS"""
    logger.info("🚀 Début de la collecte RSS complète")
    start_time = datetime.now()
    
    total_sources = sum(len(sources) for sources in RSS_SOURCES.values())
    sources_ok = 0
    total_nouveaux = 0
    details = {}
    
    for region, sources in RSS_SOURCES.items():
        region_articles = []
        region_ok = 0
        
        for source in sources:
            articles = fetch_rss_feed(source['name'], source['url'], region)
            if articles:
                sources_ok += 1
                region_ok += 1
                region_articles.extend(articles)
        
        # Sauvegarder les articles de la région
        if region_articles:
            nouveaux = save_articles(region_articles)
            total_nouveaux += nouveaux
            details[region] = {
                'sources_ok': region_ok,
                'sources_total': len(sources),
                'articles_nouveaux': nouveaux,
                'articles_total': len(region_articles)
            }
            logger.info(f"📍 {region}: {region_ok}/{len(sources)} sources OK, {nouveaux} nouveaux articles")
        else:
            details[region] = {
                'sources_ok': 0,
                'sources_total': len(sources),
                'articles_nouveaux': 0,
                'articles_total': 0
            }
    
    # Enregistrer la collecte
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO collectes (nb_sources_total, nb_sources_ok, nb_articles_nouveaux, details)
        VALUES (?, ?, ?, ?)
    ''', (total_sources, sources_ok, total_nouveaux, json.dumps(details)))
    conn.commit()
    conn.close()
    
    duration = datetime.now() - start_time
    logger.info(f"✅ Collecte terminée en {duration.total_seconds():.1f}s: {sources_ok}/{total_sources} sources OK, {total_nouveaux} nouveaux articles")
    
    return {
        'sources_total': total_sources,
        'sources_ok': sources_ok,
        'articles_nouveaux': total_nouveaux,
        'duration': duration.total_seconds(),
        'details': details
    }

# Routes API
@app.route('/')
def index():
    """Page d'accueil"""
    return send_from_directory('static', 'index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    """Servir les fichiers statiques"""
    return send_from_directory('static', filename)

@app.route('/api/regions')
def get_regions():
    """Obtenir la liste des régions avec statistiques"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    regions = []
    for region_name in RSS_SOURCES.keys():
        # Compter les articles de la région
        cursor.execute('SELECT COUNT(*) FROM articles WHERE region = ?', (region_name,))
        nb_articles = cursor.fetchone()[0]
        
        # Compter les sources
        nb_sources = len(RSS_SOURCES[region_name])
        
        regions.append({
            'id': region_name.lower().replace(' ', '-').replace('\'', ''),
            'nom': region_name,
            'nb_articles': nb_articles,
            'nb_sources': nb_sources
        })
    
    conn.close()
    return jsonify(regions)

@app.route('/api/regions/<region_name>/articles')
def get_region_articles(region_name):
    """Obtenir les articles d'une région"""
    # Décoder le nom de région
    region_name = region_name.replace('-', ' ').replace('_', '\'')
    
    # Trouver la région exacte
    actual_region = None
    for region in RSS_SOURCES.keys():
        if region.lower().replace(' ', '-').replace('\'', '') == region_name.lower():
            actual_region = region
            break
    
    if not actual_region:
        return jsonify({'error': 'Région non trouvée'}), 404
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT titre, url, description, source, region, date_publication, date_collecte
        FROM articles 
        WHERE region = ?
        ORDER BY date_publication DESC
        LIMIT 100
    ''', (actual_region,))
    
    articles = []
    for row in cursor.fetchall():
        articles.append({
            'titre': row[0],
            'url': row[1],
            'description': row[2],
            'source': row[3],
            'region': row[4],
            'date_publication': row[5],
            'date_collecte': row[6]
        })
    
    conn.close()
    return jsonify({'articles': articles})

@app.route('/api/articles/top')
def get_top_articles():
    """Obtenir les top articles"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT titre, url, description, source, region, date_publication, date_collecte
        FROM articles 
        ORDER BY date_publication DESC
        LIMIT 100
    ''')
    
    articles = []
    for row in cursor.fetchall():
        articles.append({
            'titre': row[0],
            'url': row[1],
            'description': row[2],
            'source': row[3],
            'region': row[4],
            'date_publication': row[5],
            'date_collecte': row[6]
        })
    
    conn.close()
    return jsonify({'articles': articles})

@app.route('/api/stats')
def get_stats():
    """Obtenir les statistiques"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Statistiques générales
    cursor.execute('SELECT COUNT(*) FROM articles')
    total_articles = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT source) FROM articles')
    sources_actives = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT region) FROM articles')
    total_regions = cursor.fetchone()[0]
    
    # Dernière collecte
    cursor.execute('SELECT * FROM collectes ORDER BY date_collecte DESC LIMIT 1')
    derniere_collecte = cursor.fetchone()
    
    total_sources = sum(len(sources) for sources in RSS_SOURCES.values())
    
    stats = {
        'total_articles': total_articles,
        'total_sources': total_sources,
        'sources_actives': sources_actives,
        'total_regions': total_regions,
        'derniere_collecte': derniere_collecte[1] if derniere_collecte else None
    }
    
    conn.close()
    return jsonify(stats)

@app.route('/api/collect', methods=['POST'])
def trigger_collect():
    """Déclencher une collecte manuelle"""
    try:
        # Lancer la collecte dans un thread séparé
        def run_collect():
            collect_all_feeds()
        
        thread = threading.Thread(target=run_collect)
        thread.start()
        
        return jsonify({'status': 'success', 'message': 'Collecte démarrée'})
    except Exception as e:
        logger.error(f"Erreur déclenchement collecte: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/search')
def search_articles():
    """Rechercher des articles"""
    query = request.args.get('q', '').strip()
    region = request.args.get('region', '')
    
    if not query:
        return jsonify({'articles': []})
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    sql = '''
        SELECT titre, url, description, source, region, date_publication, date_collecte
        FROM articles 
        WHERE (titre LIKE ? OR description LIKE ? OR source LIKE ?)
    '''
    params = [f'%{query}%', f'%{query}%', f'%{query}%']
    
    if region:
        sql += ' AND region = ?'
        params.append(region)
    
    sql += ' ORDER BY date_publication DESC LIMIT 50'
    
    cursor.execute(sql, params)
    
    articles = []
    for row in cursor.fetchall():
        articles.append({
            'titre': row[0],
            'url': row[1],
            'description': row[2],
            'source': row[3],
            'region': row[4],
            'date_publication': row[5],
            'date_collecte': row[6]
        })
    
    conn.close()
    return jsonify({'articles': articles, 'total': len(articles)})

# Initialisation
if __name__ == '__main__':
    # Initialiser la base de données
    init_database()
    
    # Collecte initiale
    logger.info("Collecte initiale au démarrage...")
    collect_all_feeds()
    
    # Programmer les collectes automatiques (toutes les 15 minutes)
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=collect_all_feeds,
        trigger="interval",
        minutes=15,
        id='collect_rss'
    )
    scheduler.start()
    
    # Arrêter le scheduler à la fermeture
    atexit.register(lambda: scheduler.shutdown())
    
    # Démarrer l'application
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

