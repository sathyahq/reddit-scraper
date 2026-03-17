import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import re

def scrape_reddit(query):
    """
    Scrape Reddit search results without using the official API.
    Uses the old.reddit.com interface which is easier to parse.
    """
    url = f'https://old.reddit.com/search/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    params = {
        'q': query,
        'sort': 'relevance',
        'restrict_sr': 'off'
    }

    posts = []

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all post containers
        post_containers = soup.find_all('div', class_='thing')

        for container in post_containers[:15]:  # Limit to 15 results
            try:
                # Extract title and link
                title_elem = container.find('a', class_='title')
                if not title_elem:
                    continue

                title = title_elem.text.strip()
                post_url = title_elem.get('href', '')

                # Extract subreddit
                subreddit_elem = container.find('a', class_='subreddit')
                subreddit = subreddit_elem.text.strip() if subreddit_elem else 'Unknown'

                # Extract score/upvotes
                score_elem = container.find('div', class_='score')
                upvotes = extract_number(score_elem.text) if score_elem else 0

                # Extract comment count
                comment_elem = container.find('a', string=re.compile(r'comment'))
                comments = extract_number(comment_elem.text) if comment_elem else 0

                # Extract time posted
                time_elem = container.find('time')
                time_posted = time_elem.get('title', 'Unknown') if time_elem else 'Unknown'

                posts.append({
                    'title': title,
                    'url': post_url,
                    'subreddit': subreddit,
                    'upvotes': upvotes,
                    'comments': comments,
                    'time_posted': time_posted,
                    'scraped_at': datetime.now().isoformat(),
                    'query': query
                })

            except Exception as e:
                continue

        time.sleep(1)  # Be respectful to Reddit's servers

    except Exception as e:
        print(f"Error scraping Reddit: {e}")
        return []

    return posts

def extract_number(text):
    """Extract number from text like '1.2k' or '123'"""
    if not text:
        return 0

    text = text.lower().strip()
    multipliers = {'k': 1000, 'm': 1000000}

    for suffix, mult in multipliers.items():
        if suffix in text:
            try:
                num = float(text.replace(suffix, '').strip()) * mult
                return int(num)
            except:
                return 0

    try:
        return int(''.join(filter(str.isdigit, text)))
    except:
        return 0

def get_trending_keywords(db_path):
    """Get trending keywords from database"""
    # This is a placeholder - actual implementation in database.py
    return []

def get_top_posts(db_path):
    """Get top posts from database"""
    # This is a placeholder - actual implementation in database.py
    return []
