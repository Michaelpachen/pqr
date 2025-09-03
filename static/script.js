// Configuration de l'API
const API_BASE = window.location.origin;

// État de l'application
let currentView = 'top';
let collectInProgress = false;

// Utilitaires
function formatDate(dateString) {
    if (!dateString) return 'Date inconnue';
    const date = new Date(dateString);
    return date.toLocaleString('fr-FR', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatRelativeTime(dateString) {
    if (!dateString) return 'Date inconnue';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffHours < 1) return 'Il y a moins d\'1h';
    if (diffHours < 24) return `Il y a ${diffHours}h`;
    if (diffDays < 7) return `Il y a ${diffDays} jour${diffDays > 1 ? 's' : ''}`;
    return formatDate(dateString);
}

function showLoading(show = true) {
    const loading = document.getElementById('loading');
    if (loading) {
        loading.style.display = show ? 'block' : 'none';
    }
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// API calls
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}/api${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error(`Erreur API ${endpoint}:`, error);
        throw error;
    }
}

// Chargement des statistiques
async function loadStats() {
    try {
        const stats = await apiCall('/stats');
        const statsText = document.getElementById('stats-text');
        if (statsText) {
            statsText.textContent = `${stats.total_articles} articles • ${stats.sources_actives}/${stats.total_sources} sources actives`;
        }
        
        const lastUpdate = document.getElementById('last-update');
        if (lastUpdate && stats.derniere_collecte) {
            lastUpdate.textContent = formatDate(stats.derniere_collecte);
        }
    } catch (error) {
        console.error('Erreur chargement stats:', error);
    }
}

// Affichage des top articles
async function showTopArticles() {
    currentView = 'top';
    updateNavigation();
    showLoading(true);
    
    try {
        const data = await apiCall('/articles/top');
        const content = document.getElementById('content');
        
        if (data.articles.length === 0) {
            content.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-newspaper"></i>
                    <h3>Aucun article disponible</h3>
                    <p>Cliquez sur "Actualiser" pour collecter les dernières actualités</p>
                </div>
            `;
        } else {
            content.innerHTML = `
                <div class="page-header">
                    <h1><i class="fas fa-star"></i> Top Articles</h1>
                    <p>Les articles les plus récents de toutes les régions</p>
                </div>
                
                <div class="articles-count">
                    <p><span class="highlight">${data.articles.length}</span> article${data.articles.length > 1 ? 's' : ''} trouvé${data.articles.length > 1 ? 's' : ''}</p>
                </div>
                
                <div class="articles-grid">
                    ${data.articles.map(article => createArticleCard(article)).join('')}
                </div>
            `;
        }
    } catch (error) {
        document.getElementById('content').innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>Erreur de chargement</h3>
                <p>Impossible de charger les articles</p>
            </div>
        `;
        showNotification('Erreur lors du chargement des articles', 'error');
    } finally {
        showLoading(false);
    }
}

// Affichage des régions
async function showRegions() {
    currentView = 'regions';
    updateNavigation();
    showLoading(true);
    
    try {
        const regions = await apiCall('/regions');
        const content = document.getElementById('content');
        
        content.innerHTML = `
            <div class="page-header">
                <h1><i class="fas fa-map-marked-alt"></i> Régions</h1>
                <p>Sélectionnez une région pour voir ses actualités</p>
            </div>
            
            <div class="regions-grid">
                ${regions.map(region => createRegionCard(region)).join('')}
            </div>
        `;
    } catch (error) {
        document.getElementById('content').innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>Erreur de chargement</h3>
                <p>Impossible de charger les régions</p>
            </div>
        `;
        showNotification('Erreur lors du chargement des régions', 'error');
    } finally {
        showLoading(false);
    }
}

// Affichage d'une région spécifique
async function showRegion(regionId, regionName) {
    currentView = 'region';
    updateNavigation();
    showLoading(true);
    
    try {
        const data = await apiCall(`/regions/${regionId}/articles`);
        const content = document.getElementById('content');
        
        if (data.articles.length === 0) {
            content.innerHTML = `
                <div class="page-header">
                    <h1><i class="fas fa-map-marker-alt"></i> ${regionName}</h1>
                    <p>Actualités de la région</p>
                    <button onclick="showRegions()" class="btn btn-outline">
                        <i class="fas fa-arrow-left"></i> Retour aux régions
                    </button>
                </div>
                
                <div class="empty-state">
                    <i class="fas fa-newspaper"></i>
                    <h3>Aucun article disponible</h3>
                    <p>Aucun article trouvé pour cette région</p>
                </div>
            `;
        } else {
            content.innerHTML = `
                <div class="page-header">
                    <h1><i class="fas fa-map-marker-alt"></i> ${regionName}</h1>
                    <p>Actualités de la région</p>
                    <button onclick="showRegions()" class="btn btn-outline">
                        <i class="fas fa-arrow-left"></i> Retour aux régions
                    </button>
                </div>
                
                <div class="articles-count">
                    <p><span class="highlight">${data.articles.length}</span> article${data.articles.length > 1 ? 's' : ''} trouvé${data.articles.length > 1 ? 's' : ''}</p>
                </div>
                
                <div class="articles-grid">
                    ${data.articles.map(article => createArticleCard(article)).join('')}
                </div>
            `;
        }
    } catch (error) {
        document.getElementById('content').innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>Erreur de chargement</h3>
                <p>Impossible de charger les articles de cette région</p>
            </div>
        `;
        showNotification('Erreur lors du chargement de la région', 'error');
    } finally {
        showLoading(false);
    }
}

// Recherche
async function performSearch() {
    const searchInput = document.getElementById('search-input');
    const query = searchInput.value.trim();
    
    if (!query) {
        showNotification('Veuillez saisir un terme de recherche', 'info');
        return;
    }
    
    currentView = 'search';
    updateNavigation();
    showLoading(true);
    
    try {
        const data = await apiCall(`/search?q=${encodeURIComponent(query)}`);
        const content = document.getElementById('content');
        
        if (data.articles.length === 0) {
            content.innerHTML = `
                <div class="page-header">
                    <h1><i class="fas fa-search"></i> Recherche</h1>
                    <p>Résultats pour "${query}"</p>
                </div>
                
                <div class="empty-state">
                    <i class="fas fa-search"></i>
                    <h3>Aucun résultat</h3>
                    <p>Aucun article trouvé pour "${query}"</p>
                </div>
            `;
        } else {
            content.innerHTML = `
                <div class="page-header">
                    <h1><i class="fas fa-search"></i> Recherche</h1>
                    <p>Résultats pour "${query}"</p>
                </div>
                
                <div class="articles-count">
                    <p><span class="highlight">${data.articles.length}</span> résultat${data.articles.length > 1 ? 's' : ''} trouvé${data.articles.length > 1 ? 's' : ''}</p>
                </div>
                
                <div class="articles-grid">
                    ${data.articles.map(article => createArticleCard(article)).join('')}
                </div>
            `;
        }
    } catch (error) {
        document.getElementById('content').innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>Erreur de recherche</h3>
                <p>Impossible d'effectuer la recherche</p>
            </div>
        `;
        showNotification('Erreur lors de la recherche', 'error');
    } finally {
        showLoading(false);
    }
}

// Collecte RSS
async function triggerCollect() {
    if (collectInProgress) {
        showNotification('Une collecte est déjà en cours', 'info');
        return;
    }
    
    collectInProgress = true;
    const refreshBtn = document.getElementById('refresh-btn');
    const originalText = refreshBtn.innerHTML;
    
    // Afficher le modal de collecte
    const modal = document.getElementById('collect-modal');
    modal.style.display = 'flex';
    
    // Mettre à jour le bouton
    refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Collecte...';
    refreshBtn.disabled = true;
    
    try {
        // Déclencher la collecte
        await apiCall('/collect', { method: 'POST' });
        
        // Simuler le progrès (la vraie collecte se fait côté serveur)
        let progress = 0;
        const progressFill = document.getElementById('progress-fill');
        const collectStatus = document.getElementById('collect-status');
        const collectDetails = document.getElementById('collect-details');
        
        const interval = setInterval(() => {
            progress += Math.random() * 10;
            if (progress > 100) progress = 100;
            
            progressFill.style.width = `${progress}%`;
            collectStatus.textContent = `Collecte en cours... ${Math.round(progress)}%`;
            
            if (progress >= 100) {
                clearInterval(interval);
                collectStatus.textContent = 'Collecte terminée !';
                collectDetails.innerHTML = '<p>✅ Collecte RSS terminée avec succès</p>';
                
                setTimeout(() => {
                    modal.style.display = 'none';
                    showNotification('Collecte terminée avec succès !', 'success');
                    
                    // Recharger les données
                    loadStats();
                    if (currentView === 'top') {
                        showTopArticles();
                    }
                }, 2000);
            }
        }, 500);
        
    } catch (error) {
        modal.style.display = 'none';
        showNotification('Erreur lors de la collecte', 'error');
        console.error('Erreur collecte:', error);
    } finally {
        collectInProgress = false;
        refreshBtn.innerHTML = originalText;
        refreshBtn.disabled = false;
    }
}

// Création des composants
function createArticleCard(article) {
    const description = article.description ? 
        (article.description.length > 200 ? 
            article.description.substring(0, 200) + '...' : 
            article.description) : '';
    
    return `
        <div class="article-card fade-in">
            <h3><a href="${article.url}" target="_blank" rel="noopener">${article.titre}</a></h3>
            ${description ? `<div class="description">${description}</div>` : ''}
            <div class="meta">
                <span class="source"><i class="fas fa-newspaper"></i> ${article.source}</span>
                <span class="region"><i class="fas fa-map-marker-alt"></i> ${article.region}</span>
                <span class="date"><i class="fas fa-clock"></i> ${formatRelativeTime(article.date_publication)}</span>
            </div>
        </div>
    `;
}

function createRegionCard(region) {
    return `
        <div class="region-card fade-in" onclick="showRegion('${region.id}', '${region.nom}')">
            <h3><i class="fas fa-map-marker-alt"></i> ${region.nom}</h3>
            <div class="stats">
                <i class="fas fa-newspaper"></i> ${region.nb_articles} article${region.nb_articles > 1 ? 's' : ''}
                <br>
                <i class="fas fa-rss"></i> ${region.nb_sources} source${region.nb_sources > 1 ? 's' : ''}
            </div>
        </div>
    `;
}

// Navigation
function updateNavigation() {
    const navBtns = document.querySelectorAll('.nav-btn');
    navBtns.forEach(btn => btn.classList.remove('active'));
    
    if (currentView === 'top' || currentView === 'search') {
        navBtns[0].classList.add('active');
    } else if (currentView === 'regions' || currentView === 'region') {
        navBtns[1].classList.add('active');
    }
}

// Événements
document.addEventListener('DOMContentLoaded', function() {
    // Charger les statistiques
    loadStats();
    
    // Afficher les top articles par défaut
    showTopArticles();
    
    // Événement du bouton actualiser
    document.getElementById('refresh-btn').addEventListener('click', triggerCollect);
    
    // Événement de recherche
    document.getElementById('search-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
    
    // Actualiser les stats toutes les minutes
    setInterval(loadStats, 60000);
});

// Fermer le modal en cliquant à l'extérieur
document.addEventListener('click', function(e) {
    const modal = document.getElementById('collect-modal');
    if (e.target === modal) {
        modal.style.display = 'none';
    }
});

