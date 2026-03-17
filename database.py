import sqlite3
from datetime import datetime, timedelta
from collections import Counter
import re

def init_db(db_path):
    """Initialize SQLite database"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            url TEXT,
            subreddit TEXT,
            upvotes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            time_posted TEXT,
            scraped_at TIMESTAMP,
            query TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY,
            query TEXT NOT NULL,
            result_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

def save_post(db_path, post):
    """Save a post to the database"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Avoid duplicates
    c.execute('SELECT id FROM posts WHERE title = ? AND subreddit = ?',
              (post['title'], post['subreddit']))

    if not c.fetchone():
        c.execute('''
            INSERT INTO posts (title, url, subreddit, upvotes, comments, time_posted, scraped_at, query)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            post['title'],
            post['url'],
            post['subreddit'],
            post['upvotes'],
            post['comments'],
            post['time_posted'],
            post['scraped_at'],
            post['query']
        ))

    conn.commit()
    conn.close()

def search_posts(db_path, query):
    """Search posts by keyword"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    search_term = f'%{query}%'
    c.execute('''
        SELECT * FROM posts
        WHERE title LIKE ? OR subreddit LIKE ?
        ORDER BY upvotes DESC, comments DESC
        LIMIT 50
    ''', (search_term, search_term))

    posts = [dict(row) for row in c.fetchall()]
    conn.close()

    return posts

def get_trending_keywords(db_path):
    """Get trending keywords from posts"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute('SELECT title FROM posts WHERE created_at > datetime("now", "-7 days")')
    titles = c.fetchall()
    conn.close()

    if not titles:
        return []

    # Extract keywords (words longer than 3 chars)
    all_words = []
    for (title,) in titles:
        words = re.findall(r'\b\w{4,}\b', title.lower())
        all_words.extend(words)

    # Get most common keywords
    counter = Counter(all_words)
    return [{'keyword': word, 'count': count} for word, count in counter.most_common(10)]

def get_stats(db_path):
    """Get database statistics"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute('SELECT COUNT(*) FROM posts')
    total_posts = c.fetchone()[0]

    c.execute('SELECT COUNT(DISTINCT query) FROM posts')
    total_searches = c.fetchone()[0]

    c.execute('SELECT COUNT(DISTINCT subreddit) FROM posts')
    total_subreddits = c.fetchone()[0]

    c.execute('SELECT SUM(upvotes) FROM posts')
    total_engagement = c.fetchone()[0] or 0

    conn.close()

    return {
        'total_posts': total_posts,
        'total_searches': total_searches,
        'total_subreddits': total_subreddits,
        'total_engagement': total_engagement
    }
