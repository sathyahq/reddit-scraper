from flask import Flask, render_template, request, jsonify
from scraper import scrape_reddit, get_trending_keywords, get_top_posts
from database import init_db, save_post, search_posts, get_stats
import os

app = Flask(__name__)
app.config['DATABASE'] = 'reddit_data.db'

# Initialize database on startup
init_db(app.config['DATABASE'])

@app.route('/')
def index():
    stats = get_stats(app.config['DATABASE'])
    return render_template('index.html', stats=stats)

@app.route('/search', methods=['POST'])
def search():
    query = request.json.get('query', '').strip()
    if not query or len(query) < 2:
        return jsonify({'error': 'Query too short'}), 400

    # Scrape from Reddit
    posts = scrape_reddit(query)

    # Save to database
    for post in posts:
        save_post(app.config['DATABASE'], post)

    return jsonify({
        'query': query,
        'results': posts,
        'count': len(posts)
    })

@app.route('/api/posts', methods=['GET'])
def get_posts():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'No query provided'}), 400

    posts = search_posts(app.config['DATABASE'], query)
    return jsonify({'posts': posts})

@app.route('/api/trending', methods=['GET'])
def trending():
    keywords = get_trending_keywords(app.config['DATABASE'])
    return jsonify({'trending': keywords})

@app.route('/api/stats', methods=['GET'])
def stats():
    stats = get_stats(app.config['DATABASE'])
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
