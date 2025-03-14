document.addEventListener('DOMContentLoaded', function() {
    // Load initial data
    loadStats();
    loadLatestData('news');
    loadLatestData('twitter');
    loadLatestData('instagram');
    
    // Set up tab change event to load data when switching tabs
    const dataTabs = document.querySelectorAll('button[data-bs-toggle="tab"]');
    dataTabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function(event) {
            const targetId = event.target.getAttribute('data-bs-target').replace('#', '');
            loadLatestData(targetId);
        });
    });
    
    // Set up refresh interval (every 60 seconds)
    setInterval(function() {
        loadStats();
        
        // Get the currently active tab
        const activeTab = document.querySelector('.tab-pane.active');
        if (activeTab) {
            const tabId = activeTab.id;
            loadLatestData(tabId);
        }
    }, 60000);
});

/**
 * Load scraper statistics
 */
function loadStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            // Update news stats
            if (data.news) {
                document.getElementById('news-count').textContent = `${data.news.total} items scraped`;
                document.getElementById('news-updated').textContent = 
                    `Last updated: ${formatDate(data.news.last_updated)}`;
            }
            
            // Update twitter stats
            if (data.twitter) {
                document.getElementById('twitter-count').textContent = `${data.twitter.total} tweets scraped`;
                document.getElementById('twitter-updated').textContent = 
                    `Last updated: ${formatDate(data.twitter.last_updated)}`;
            }
            
            // Update instagram stats
            if (data.instagram) {
                document.getElementById('instagram-count').textContent = `${data.instagram.total} posts scraped`;
                document.getElementById('instagram-updated').textContent = 
                    `Last updated: ${formatDate(data.instagram.last_updated)}`;
            }
        })
        .catch(error => {
            console.error('Error loading stats:', error);
        });
}

/**
 * Load latest data for a specific source
 * @param {string} source - The data source (news, twitter, instagram)
 */
function loadLatestData(source) {
    const container = document.getElementById(`${source}-data`);
    
    if (!container) return;
    
    // Display loading indicator
    container.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Loading latest ${source} data...</p>
        </div>
    `;
    
    fetch(`/api/latest_data/${source}`)
        .then(response => response.json())
        .then(data => {
            if (Array.isArray(data) && data.length > 0) {
                // Display the data based on source type
                switch(source) {
                    case 'news':
                        displayNewsData(container, data);
                        break;
                    case 'twitter':
                        displayTwitterData(container, data);
                        break;
                    case 'instagram':
                        displayInstagramData(container, data);
                        break;
                }
            } else {
                container.innerHTML = `
                    <div class="text-center py-5">
                        <i class="fas fa-exclamation-circle text-warning fa-3x mb-3"></i>
                        <p>No ${source} data available yet. Run the scraper to collect data.</p>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error(`Error loading ${source} data:`, error);
            container.innerHTML = `
                <div class="text-center py-5">
                    <i class="fas fa-exclamation-triangle text-danger fa-3x mb-3"></i>
                    <p>Error loading ${source} data. Please try again later.</p>
                    <p class="small text-muted">${error.message}</p>
                </div>
            `;
        });
}

/**
 * Display news data in the container
 * @param {HTMLElement} container - The container element
 * @param {Array} data - The news data
 */
function displayNewsData(container, data) {
    let html = '';
    
    data.forEach(item => {
        html += `
            <div class="news-item">
                <div class="news-source">${item.source}</div>
                <h5 class="mt-1"><a href="${item.link}" target="_blank">${item.title}</a></h5>
                <p>${item.summary || ''}</p>
                <div class="news-date">${formatDate(item.published || item.scraped_at)}</div>
            </div>
        `;
    });
    
    container.innerHTML = html || '<div class="p-4 text-center">No news data available</div>';
}

/**
 * Display Twitter data in the container
 * @param {HTMLElement} container - The container element
 * @param {Array} data - The Twitter data
 */
function displayTwitterData(container, data) {
    let html = '';
    
    data.forEach(item => {
        html += `
            <div class="tweet-item">
                <div class="tweet-user">@${item.username}</div>
                <p>${item.text}</p>
                <div class="d-flex justify-content-between align-items-center">
                    <div class="tweet-date">${formatDate(item.created_at || item.scraped_at)}</div>
                    <a href="${item.link}" target="_blank" class="btn btn-sm btn-outline-info">
                        <i class="fab fa-twitter me-1"></i> View Tweet
                    </a>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html || '<div class="p-4 text-center">No Twitter data available</div>';
}

/**
 * Display Instagram data in the container
 * @param {HTMLElement} container - The container element
 * @param {Array} data - The Instagram data
 */
function displayInstagramData(container, data) {
    let html = '';
    
    data.forEach(item => {
        html += `
            <div class="instagram-item">
                <div class="instagram-user">@${item.username}</div>
                <p>${item.caption || 'No caption'}</p>
                <div class="instagram-metrics">
                    <span class="me-3"><i class="fas fa-heart"></i> ${item.likes || 0}</span>
                    <span><i class="fas fa-comment"></i> ${item.comments || 0}</span>
                </div>
                <div class="d-flex justify-content-between align-items-center mt-2">
                    <div class="instagram-date">${formatDate(item.posted_at || item.scraped_at)}</div>
                    <a href="${item.link}" target="_blank" class="btn btn-sm btn-outline-info">
                        <i class="fab fa-instagram me-1"></i> View Post
                    </a>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html || '<div class="p-4 text-center">No Instagram data available</div>';
}

/**
 * Run a scraper job immediately
 * @param {string} jobId - The ID of the job to run
 */
function runJob(jobId) {
    const button = document.querySelector(`button[onclick="runJob('${jobId}')"]`);
    button.disabled = true;
    button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Running...';
    
    fetch(`/api/run_job/${jobId}`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Show success toast
                alert('Job started successfully! Check logs for progress.');
            } else {
                // Show error toast
                alert(`Error: ${data.message}`);
            }
        })
        .catch(error => {
            console.error(`Error running job ${jobId}:`, error);
            alert(`Error: ${error.message}`);
        })
        .finally(() => {
            // Re-enable the button after 5 seconds
            setTimeout(() => {
                button.disabled = false;
                button.innerHTML = 'Run Now';
            }, 5000);
        });
}

/**
 * Format a date string to a human-readable format
 * @param {string} dateString - The date string to format
 * @returns {string} - The formatted date
 */
function formatDate(dateString) {
    if (!dateString || dateString === 'Never') return 'Never';
    
    try {
        const date = new Date(dateString);
        
        // Check if date is valid
        if (isNaN(date.getTime())) {
            return dateString;
        }
        
        // If date is today, show time only
        const today = new Date();
        if (date.toDateString() === today.toDateString()) {
            return `Today at ${date.toLocaleTimeString()}`;
        }
        
        // Otherwise show full date and time
        return date.toLocaleString();
    } catch (e) {
        return dateString;
    }
}
