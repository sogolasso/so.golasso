import os
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from scheduler import run_job_now, get_scheduler_jobs, stop_scheduler, start_scheduler
from config import get_config, update_source_settings, update_scraper_settings

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "so-golasso-scraper-secret")

# Routes
@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/logs')
def logs():
    """View scraper logs"""
    return render_template('logs.html')
    
@app.route('/config')
def config_page():
    """Configuration page"""
    return render_template('config.html')
    
@app.route('/api/run_job/<job_id>', methods=['POST'])
def run_job(job_id):
    """API endpoint to run a scraper job immediately"""
    result = run_job_now(job_id)
    if result:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "message": "Failed to run job. Check logs for details."}), 500
        
@app.route('/api/logs')
def get_logs():
    """API endpoint to get scraper logs"""
    try:
        # Read the log file
        with open('data/scraper.log', 'r') as file:
            logs = file.read()
        return logs
    except FileNotFoundError:
        return "No logs available yet."
    except Exception as e:
        return f"Error reading logs: {str(e)}", 500

@app.route('/api/stats')
def get_stats():
    """API endpoint to get scraper statistics"""
    try:
        # Read the latest stats from the stats.json file
        with open('data/stats.json', 'r') as file:
            stats = json.load(file)
        return jsonify(stats)
    except FileNotFoundError:
        # Return empty stats if the file doesn't exist yet
        return jsonify({
            "news": {"total": 0, "last_updated": "Never"},
            "twitter": {"total": 0, "last_updated": "Never"},
            "instagram": {"total": 0, "last_updated": "Never"}
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/test/instagram', methods=['POST'])
def test_instagram():
    """Test endpoint to run Instagram scraper immediately"""
    from scrapers.instagram_scraper import fetch_instagram_posts
    try:
        posts = fetch_instagram_posts()
        return jsonify({"success": True, "posts": posts})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/latest_data/<source_type>')
def get_latest_data(source_type):
    """API endpoint to get the latest scraped data for a specific source"""
    valid_sources = ['news', 'twitter', 'instagram']
    
    if source_type not in valid_sources:
        return jsonify({"error": "Invalid source type"}), 400
    
    try:
        # Read the latest data from the relevant file
        filename = f'data/{source_type}_latest.json'
        with open(filename, 'r') as file:
            data = json.load(file)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
@app.route('/api/config')
def get_config_api():
    """API endpoint to get the current configuration"""
    config = get_config()
    return jsonify(config)

@app.route('/api/config/sources/<source_type>', methods=['POST'])
def update_sources_api(source_type):
    """API endpoint to update source settings"""
    try:
        valid_source_types = ["news_sources", "twitter_accounts", "instagram_accounts"]
        if source_type not in valid_source_types:
            return jsonify({"error": "Invalid source type"}), 400
            
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        result = update_source_settings(source_type, data)
        
        if result:
            # Restart the scheduler to apply the new settings
            stop_scheduler()
            scheduler = start_scheduler()
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "message": "Failed to update settings"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
@app.route('/api/config/scraper', methods=['POST'])
def update_scraper_settings_api():
    """API endpoint to update scraper settings"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        result = update_scraper_settings(data)
        
        if result:
            # Restart the scheduler to apply the new settings
            stop_scheduler()
            scheduler = start_scheduler()
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "message": "Failed to update settings"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Make sure the data directory exists
os.makedirs('data', exist_ok=True)

# Initialize or update the stats file
def init_stats_file():
    """Initialize the stats file if it doesn't exist"""
    stats_file = 'data/stats.json'
    if not os.path.exists(stats_file):
        initial_stats = {
            "news": {"total": 0, "last_updated": "Never"},
            "twitter": {"total": 0, "last_updated": "Never"},
            "instagram": {"total": 0, "last_updated": "Never"}
        }
        with open(stats_file, 'w') as file:
            json.dump(initial_stats, file)

init_stats_file()
