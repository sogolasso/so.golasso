/**
 * Configuration page JavaScript
 */

// DOM elements
const newsSourcesContainer = document.getElementById('newsSources');
const twitterAccountsContainer = document.getElementById('twitterAccounts');
const instagramAccountsContainer = document.getElementById('instagramAccounts');
const scraperSettingsForm = document.getElementById('scraperSettingsForm');
const newsSourcesForm = document.getElementById('newsSourcesForm');
const twitterAccountsForm = document.getElementById('twitterAccountsForm');
const instagramAccountsForm = document.getElementById('instagramAccountsForm');

// Form fields
const newsIntervalInput = document.getElementById('newsInterval');
const twitterIntervalInput = document.getElementById('twitterInterval');
const instagramIntervalInput = document.getElementById('instagramInterval');
const maxPostsPerSourceInput = document.getElementById('maxPostsPerSource');

// Load configuration on page load
document.addEventListener('DOMContentLoaded', function() {
    loadConfig();
    
    // Set up form submission handlers
    scraperSettingsForm.addEventListener('submit', saveScraperSettings);
    newsSourcesForm.addEventListener('submit', saveNewsSources);
    twitterAccountsForm.addEventListener('submit', saveTwitterAccounts);
    instagramAccountsForm.addEventListener('submit', saveInstagramAccounts);
});

/**
 * Load configuration from the server
 */
function loadConfig() {
    fetch('/api/config')
        .then(response => response.json())
        .then(config => {
            displayScraperSettings(config.scraper_settings);
            displayNewsSources(config.news_sources);
            displayTwitterAccounts(config.twitter_accounts);
            displayInstagramAccounts(config.instagram_accounts);
        })
        .catch(error => {
            console.error('Error loading configuration:', error);
            showAlert('Error loading configuration. Please try refreshing the page.', 'danger');
        });
}

/**
 * Display scraper settings in the form
 */
function displayScraperSettings(settings) {
    newsIntervalInput.value = settings.news_interval_hours;
    twitterIntervalInput.value = settings.twitter_interval_hours;
    instagramIntervalInput.value = settings.instagram_interval_hours;
    maxPostsPerSourceInput.value = settings.max_posts_per_source;
}

/**
 * Display news sources as checkboxes
 */
function displayNewsSources(sources) {
    newsSourcesContainer.innerHTML = '';
    
    for (const [source, enabled] of Object.entries(sources)) {
        const sourceName = formatSourceName(source);
        
        const div = document.createElement('div');
        div.className = 'form-check';
        
        const input = document.createElement('input');
        input.className = 'form-check-input';
        input.type = 'checkbox';
        input.id = `news-${source}`;
        input.name = source;
        input.checked = enabled;
        
        const label = document.createElement('label');
        label.className = 'form-check-label';
        label.htmlFor = `news-${source}`;
        label.textContent = sourceName;
        
        div.appendChild(input);
        div.appendChild(label);
        newsSourcesContainer.appendChild(div);
    }
}

/**
 * Display Twitter accounts as checkboxes
 */
function displayTwitterAccounts(accounts) {
    twitterAccountsContainer.innerHTML = '';
    
    for (const [account, enabled] of Object.entries(accounts)) {
        const div = document.createElement('div');
        div.className = 'form-check';
        
        const input = document.createElement('input');
        input.className = 'form-check-input';
        input.type = 'checkbox';
        input.id = `twitter-${account}`;
        input.name = account;
        input.checked = enabled;
        
        const label = document.createElement('label');
        label.className = 'form-check-label';
        label.htmlFor = `twitter-${account}`;
        label.textContent = `@${account}`;
        
        div.appendChild(input);
        div.appendChild(label);
        twitterAccountsContainer.appendChild(div);
    }
}

/**
 * Display Instagram accounts as checkboxes
 */
function displayInstagramAccounts(accounts) {
    instagramAccountsContainer.innerHTML = '';
    
    for (const [account, enabled] of Object.entries(accounts)) {
        const div = document.createElement('div');
        div.className = 'form-check';
        
        const input = document.createElement('input');
        input.className = 'form-check-input';
        input.type = 'checkbox';
        input.id = `instagram-${account}`;
        input.name = account;
        input.checked = enabled;
        
        const label = document.createElement('label');
        label.className = 'form-check-label';
        label.htmlFor = `instagram-${account}`;
        label.textContent = `@${account}`;
        
        div.appendChild(input);
        div.appendChild(label);
        instagramAccountsContainer.appendChild(div);
    }
}

/**
 * Save scraper settings
 */
function saveScraperSettings(event) {
    event.preventDefault();
    
    const settings = {
        news_interval_hours: parseInt(newsIntervalInput.value),
        twitter_interval_hours: parseInt(twitterIntervalInput.value),
        instagram_interval_hours: parseInt(instagramIntervalInput.value),
        max_posts_per_source: parseInt(maxPostsPerSourceInput.value)
    };
    
    fetch('/api/config/scraper', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(settings)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Scraper settings saved successfully!', 'success');
        } else {
            showAlert('Error saving scraper settings: ' + (data.message || 'Unknown error'), 'danger');
        }
    })
    .catch(error => {
        console.error('Error saving scraper settings:', error);
        showAlert('Error saving scraper settings. Please try again.', 'danger');
    });
}

/**
 * Save news sources
 */
function saveNewsSources(event) {
    event.preventDefault();
    
    const sources = {};
    const checkboxes = newsSourcesContainer.querySelectorAll('input[type="checkbox"]');
    
    checkboxes.forEach(checkbox => {
        sources[checkbox.name] = checkbox.checked;
    });
    
    fetch('/api/config/sources/news_sources', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(sources)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('News sources saved successfully!', 'success');
        } else {
            showAlert('Error saving news sources: ' + (data.message || 'Unknown error'), 'danger');
        }
    })
    .catch(error => {
        console.error('Error saving news sources:', error);
        showAlert('Error saving news sources. Please try again.', 'danger');
    });
}

/**
 * Save Twitter accounts
 */
function saveTwitterAccounts(event) {
    event.preventDefault();
    
    const accounts = {};
    const checkboxes = twitterAccountsContainer.querySelectorAll('input[type="checkbox"]');
    
    checkboxes.forEach(checkbox => {
        accounts[checkbox.name] = checkbox.checked;
    });
    
    fetch('/api/config/sources/twitter_accounts', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(accounts)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Twitter accounts saved successfully!', 'success');
        } else {
            showAlert('Error saving Twitter accounts: ' + (data.message || 'Unknown error'), 'danger');
        }
    })
    .catch(error => {
        console.error('Error saving Twitter accounts:', error);
        showAlert('Error saving Twitter accounts. Please try again.', 'danger');
    });
}

/**
 * Save Instagram accounts
 */
function saveInstagramAccounts(event) {
    event.preventDefault();
    
    const accounts = {};
    const checkboxes = instagramAccountsContainer.querySelectorAll('input[type="checkbox"]');
    
    checkboxes.forEach(checkbox => {
        accounts[checkbox.name] = checkbox.checked;
    });
    
    fetch('/api/config/sources/instagram_accounts', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(accounts)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Instagram accounts saved successfully!', 'success');
        } else {
            showAlert('Error saving Instagram accounts: ' + (data.message || 'Unknown error'), 'danger');
        }
    })
    .catch(error => {
        console.error('Error saving Instagram accounts:', error);
        showAlert('Error saving Instagram accounts. Please try again.', 'danger');
    });
}

/**
 * Format source name for display (e.g., convert "globo_esporte" to "Globo Esporte")
 */
function formatSourceName(source) {
    return source
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

/**
 * Show an alert message
 */
function showAlert(message, type) {
    // Create alert element
    const alertElement = document.createElement('div');
    alertElement.className = `alert alert-${type} alert-dismissible fade show`;
    alertElement.role = 'alert';
    alertElement.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to page
    const container = document.querySelector('.container');
    container.insertBefore(alertElement, container.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alertElement);
        bsAlert.close();
    }, 5000);
}