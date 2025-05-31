from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import requests
import os
import logging
from datetime import datetime
import markdown
import time
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

# Initialize models after app creation
ContentItem = None
PowerMapping = None
OrganizingAction = None
SystemicIssue = None
ResistanceStory = None
DataSource = None

def init_database():
    """Initialize database and models"""
    global ContentItem, PowerMapping, OrganizingAction, SystemicIssue, ResistanceStory, DataSource
    
    with app.app_context():
        from models import init_models
        models = init_models(db)
        
        # Create all tables
        db.create_all()
        
        # Make models available globally
        ContentItem = models['ContentItem']
        PowerMapping = models['PowerMapping']
        OrganizingAction = models['OrganizingAction']
        SystemicIssue = models['SystemicIssue']
        ResistanceStory = models['ResistanceStory']
        DataSource = models['DataSource']

# Initialize database when app starts
init_database()

# GitHub configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_RAW_BASE = os.getenv("GITHUB_RAW_BASE", "https://raw.githubusercontent.com/DignityAI/dignity-ai/main/drafts")
CACHE_DURATION = 300  # 5 minutes cache

# Simple in-memory cache
content_cache = {
    'data': None,
    'timestamp': 0
}

def cache_content(func):
    """Decorator to cache content fetching"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        current_time = time.time()
        if (content_cache['data'] is None or 
            current_time - content_cache['timestamp'] > CACHE_DURATION):
            logging.debug("Cache miss or expired, fetching new content")
            content_cache['data'] = func(*args, **kwargs)
            content_cache['timestamp'] = current_time
        else:
            logging.debug("Serving content from cache")
        return content_cache['data']
    return wrapper

def get_files_from_github_folder(folder_name):
    """Get actual files from GitHub folder using API"""
    try:
        api_url = f"https://api.github.com/repos/DignityAI/dignity-ai/contents/drafts/{folder_name}"
        headers = {}
        if GITHUB_TOKEN:
            headers['Authorization'] = f'token {GITHUB_TOKEN}'
        
        response = requests.get(api_url, headers=headers, timeout=10)
        if response.status_code == 200:
            files = response.json()
            return [f"{folder_name}/{file['name']}" for file in files if file['name'].endswith('.md')]
        else:
            logging.warning(f"Failed to get files from {folder_name}: {response.status_code}")
            return []
    except Exception as e:
        logging.error(f"Error getting files from {folder_name}: {e}")
        return []

def parse_markdown_content(content):
    """Parse markdown content to HTML and save to database"""
    try:
        md = markdown.Markdown(extensions=['meta', 'codehilite', 'fenced_code'])
        html_content = md.convert(content)
        
        # Extract metadata if available
        metadata = getattr(md, 'Meta', {})
        title = metadata.get('title', ['Untitled'])[0] if 'title' in metadata else 'Untitled'
        date = metadata.get('date', [datetime.now().strftime('%Y-%m-%d')])[0] if 'date' in metadata else datetime.now().strftime('%Y-%m-%d')
        
        return {
            'title': title,
            'content': html_content,
            'date': date,
            'metadata': metadata
        }
    except Exception as e:
        logging.error(f"Error parsing markdown: {e}")
        return {
            'title': 'Parse Error',
            'content': content,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'metadata': {}
        }

def save_content_to_db(content_data, content_type, category, file_path):
    """Save parsed content to database"""
    try:
        with app.app_context():
            # Check if content already exists
            existing = ContentItem.query.filter_by(file_path=file_path).first()
            
            if existing:
                # Update existing content
                existing.title = content_data['title']
                existing.content = content_data['content']
                existing.content_metadata = content_data['metadata']
                existing.updated_at = datetime.utcnow()
                existing.published_date = datetime.strptime(content_data['date'], '%Y-%m-%d').date()
            else:
                # Create new content item
                new_content = ContentItem(
                    title=content_data['title'],
                    content=content_data['content'],
                    content_type=content_type,
                    category=category,
                    file_path=file_path,
                    content_metadata=content_data['metadata'],
                    published_date=datetime.strptime(content_data['date'], '%Y-%m-%d').date()
                )
                db.session.add(new_content)
            
            db.session.commit()
            logging.info(f"Saved content to database: {content_data['title']}")
            
    except Exception as e:
        logging.error(f"Error saving content to database: {e}")
        db.session.rollback()

def fetch_github_file(file_path):
    """Fetch a single file from GitHub"""
    try:
        url = f"{GITHUB_RAW_BASE}/{file_path}"
        headers = {}
        if GITHUB_TOKEN:
            headers['Authorization'] = f'token {GITHUB_TOKEN}'
        
        logging.debug(f"Fetching: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.text
        else:
            logging.warning(f"Failed to fetch {file_path}: {response.status_code}")
            return None
    except requests.RequestException as e:
        logging.error(f"Network error fetching {file_path}: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error fetching {file_path}: {e}")
        return None

@cache_content
def fetch_latest_content():
    """Fetch latest content from GitHub repository"""
    try:
        content = {
            'case_studies': [],
            'news_articles': [],
            'blog_posts': [],
            'power_mapping': [],
            'sdoh_analysis': []
        }
        
        # Use your actual generated files
        content_files = {
            'case_studies': get_files_from_github_folder('case-studies'),
            'news_articles': get_files_from_github_folder('news-articles'), 
            'blog_posts': get_files_from_github_folder('blog-posts'),
            'power_mapping': get_files_from_github_folder('power-mapping'),
            'sdoh_analysis': get_files_from_github_folder('sdoh-analysis')
        }
        
        # Fetch content for each category
        for category, files in content_files.items():
            for file_path in files:
                raw_content = fetch_github_file(file_path)
                if raw_content:
                    parsed_content = parse_markdown_content(raw_content)
                    # Save to database
                    save_content_to_db(parsed_content, category, category, file_path)
                    content[category].append(parsed_content)
        
        # Sort content by date (newest first)
        for category in content:
            content[category].sort(key=lambda x: x['date'], reverse=True)
        
        # If no content fetched from GitHub, try loading from database
        if sum(len(v) for v in content.values()) == 0:
            content = load_content_from_db()
        
        logging.info(f"Successfully fetched content: {sum(len(v) for v in content.values())} items")
        return content
        
    except Exception as e:
        logging.error(f"Error fetching content: {e}")
        return {
            'case_studies': [],
            'news_articles': [],
            'blog_posts': [],
            'power_mapping': [],
            'sdoh_analysis': [],
            'error': str(e)
        }

def load_content_from_db():
    """Load content from database when GitHub fails"""
    try:
        with app.app_context():
            content = {
                'case_studies': [],
                'news_articles': [],
                'blog_posts': [],
                'power_mapping': [],
                'sdoh_analysis': []
            }
            
            # Map database content types to display categories
            type_mapping = {
                'case_studies': 'case_studies',
                'news_articles': 'news_articles',
                'blog_posts': 'blog_posts',
                'power_mapping': 'power_mapping',
                'sdoh_analysis': 'sdoh_analysis'
            }
            
            for db_type, display_category in type_mapping.items():
                items = ContentItem.query.filter_by(
                    content_type=db_type, 
                    is_active=True
                ).order_by(ContentItem.published_date.desc()).all()
                
                for item in items:
                    content[display_category].append({
                        'title': item.title,
                        'content': item.content,
                        'date': item.published_date.strftime('%Y-%m-%d') if item.published_date else '',
                        'metadata': item.content_metadata or {}
                    })
            
            return content
            
    except Exception as e:
        logging.error(f"Error loading content from database: {e}")
        return {
            'case_studies': [],
            'news_articles': [],
            'blog_posts': [],
            'power_mapping': [],
            'sdoh_analysis': []
        }

@app.route('/')
def home():
    """Main page showing daily content"""
    try:
        content = fetch_latest_content()
        if 'error' in content:
            return render_template('error.html', 
                                 error_message="Failed to fetch content from GitHub repository", 
                                 error_details=content['error'])
        return render_template('index.html', content=content)
    except Exception as e:
        logging.error(f"Error in home route: {e}")
        return render_template('error.html', 
                             error_message="An unexpected error occurred", 
                             error_details=str(e))

@app.route('/case-studies')
def case_studies():
    """Show all case studies"""
    try:
        content = fetch_latest_content()
        if 'error' in content:
            return render_template('error.html', 
                                 error_message="Failed to fetch case studies", 
                                 error_details=content['error'])
        return render_template('case_studies.html', case_studies=content['case_studies'])
    except Exception as e:
        logging.error(f"Error in case_studies route: {e}")
        return render_template('error.html', 
                             error_message="An unexpected error occurred", 
                             error_details=str(e))

@app.route('/news')
def news():
    """Show news articles"""
    try:
        content = fetch_latest_content()
        if 'error' in content:
            return render_template('error.html', 
                                 error_message="Failed to fetch news articles", 
                                 error_details=content['error'])
        return render_template('news.html', articles=content['news_articles'])
    except Exception as e:
        logging.error(f"Error in news route: {e}")
        return render_template('error.html', 
                             error_message="An unexpected error occurred", 
                             error_details=str(e))

@app.route('/blog')
def blog_posts():
    """Show blog posts"""
    try:
        content = fetch_latest_content()
        if 'error' in content:
            return render_template('error.html', 
                                 error_message="Failed to fetch blog posts", 
                                 error_details=content['error'])
        return render_template('blog_posts.html', blog_posts=content['blog_posts'])
    except Exception as e:
        logging.error(f"Error in blog_posts route: {e}")
        return render_template('error.html', 
                             error_message="An unexpected error occurred", 
                             error_details=str(e))

@app.route('/power-mapping')
def power_mapping():
    """Show power mapping content"""
    try:
        content = fetch_latest_content()
        if 'error' in content:
            return render_template('error.html', 
                                 error_message="Failed to fetch power mapping content", 
                                 error_details=content['error'])
        return render_template('power_mapping.html', power_mapping=content['power_mapping'])
    except Exception as e:
        logging.error(f"Error in power_mapping route: {e}")
        return render_template('error.html', 
                             error_message="An unexpected error occurred", 
                             error_details=str(e))

@app.route('/sdoh-analysis')
def sdoh_analysis():
    """Show SDOH analysis content"""
    try:
        content = fetch_latest_content()
        if 'error' in content:
            return render_template('error.html', 
                                 error_message="Failed to fetch SDOH analysis", 
                                 error_details=content['error'])
        return render_template('sdoh_analysis.html', sdoh_analysis=content['sdoh_analysis'])
    except Exception as e:
        logging.error(f"Error in sdoh_analysis route: {e}")
        return render_template('error.html', 
                             error_message="An unexpected error occurred", 
                             error_details=str(e))

@app.route('/api/content')
def api_content():
    """API endpoint for mobile app"""
    try:
        content = fetch_latest_content()
        return jsonify(content)
    except Exception as e:
        logging.error(f"Error in API endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/refresh-cache')
def refresh_cache():
    """Manual cache refresh endpoint"""
    global content_cache
    content_cache['data'] = None
    content_cache['timestamp'] = 0
    return jsonify({'message': 'Cache refreshed successfully'})

@app.route('/api/content/<content_type>')
def api_content_by_type(content_type):
    """API endpoint for specific content type"""
    try:
        with app.app_context():
            items = ContentItem.query.filter_by(
                content_type=content_type, 
                is_active=True
            ).order_by(ContentItem.published_date.desc()).all()
            
            return jsonify([item.to_dict() for item in items])
    except Exception as e:
        logging.error(f"Error in API endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/database-status')
def database_status():
    """Admin endpoint to check database status"""
    try:
        with app.app_context():
            total_content = ContentItem.query.count()
            power_mappings = PowerMapping.query.count()
            organizing_actions = OrganizingAction.query.count()
            systemic_issues = SystemicIssue.query.count()
            resistance_stories = ResistanceStory.query.count()
            
            return jsonify({
                'status': 'connected',
                'total_content_items': total_content,
                'power_mappings': power_mappings,
                'organizing_actions': organizing_actions,
                'systemic_issues': systemic_issues,
                'resistance_stories': resistance_stories
            })
    except Exception as e:
        logging.error(f"Database error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', 
                         error_message="Page not found", 
                         error_details="The requested page could not be found."), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', 
                         error_message="Internal server error", 
                         error_details="An unexpected error occurred on the server."), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
