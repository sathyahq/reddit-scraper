import streamlit as st
import requests
from bs4 import BeautifulSoup
import re

st.set_page_config(page_title="Reddit Search", layout="wide")
st.title("🔍 Reddit Search")
st.caption("Search Reddit posts instantly - no login required")

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

def scrape_reddit(query):
    """Scrape Reddit search results"""
    url = f'https://old.reddit.com/search/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    params = {'q': query, 'sort': 'relevance', 'restrict_sr': 'off'}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        post_containers = soup.find_all('div', class_='thing')
        posts = []

        for container in post_containers[:20]:
            try:
                title_elem = container.find('a', class_='title')
                if not title_elem:
                    continue

                title = title_elem.text.strip()
                post_url = title_elem.get('href', '')
                subreddit_elem = container.find('a', class_='subreddit')
                subreddit = subreddit_elem.text.strip() if subreddit_elem else 'Unknown'
                score_elem = container.find('div', class_='score')
                upvotes = extract_number(score_elem.text) if score_elem else 0
                comment_elem = container.find('a', string=re.compile(r'comment'))
                comments = extract_number(comment_elem.text) if comment_elem else 0

                posts.append({
                    'title': title,
                    'subreddit': subreddit,
                    'upvotes': upvotes,
                    'comments': comments,
                    'url': post_url
                })
            except:
                continue

        return posts
    except Exception as e:
        st.error(f"Error: {e}")
        return []

# Search interface
col1, col2 = st.columns([4, 1])
with col1:
    topic = st.text_input("Search topic:", placeholder="e.g., Python, AI, Marketing...")
with col2:
    search_btn = st.button("Search", use_container_width=True)

if search_btn and topic:
    with st.spinner("Searching Reddit..."):
        posts = scrape_reddit(topic)

    if posts:
        st.success(f"Found {len(posts)} posts")
        for post in posts:
            with st.container():
                st.markdown(f"### {post['title']}")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Upvotes", f"{post['upvotes']:,}")
                with col2:
                    st.metric("Comments", f"{post['comments']:,}")
                with col3:
                    st.metric("Subreddit", post['subreddit'])
                st.divider()
    else:
        st.warning("No results found. Try a different topic.")
