#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sqlite3
import psycopg2
import json
from datetime import datetime

# Configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
USE_POSTGRES = bool(DATABASE_URL)

def get_connection():
    """Obtenir une connexion à la base de données"""
    if USE_POSTGRES:
        return psycopg2.connect(DATABASE_URL)
    else:
        return sqlite3.connect('pqr_articles.db')

def execute_query(query, params=None, fetch=False):
    """Exécuter une requête SQL"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch:
            result = cursor.fetchall()
        else:
            result = cursor.rowcount
        
        conn.commit()
        return result
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def save_articles_batch(articles):
    """Sauvegarder plusieurs articles en une fois"""
    if not articles:
        return 0
    
    conn = get_connection()
    cursor = conn.cursor()
    
    nouveaux = 0
    for article in articles:
        try:
            if USE_POSTGRES:
                cursor.execute('''
                    INSERT INTO articles 
                    (titre, url, description, source, region, date_publication)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (url) DO NOTHING
                ''', (
                    article['titre'],
                    article['url'],
                    article['description'],
                    article['source'],
                    article['region'],
                    article['date_publication']
                ))
            else:
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
            print(f"Erreur sauvegarde article: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    return nouveaux

