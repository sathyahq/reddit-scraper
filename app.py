import streamlit as st
import requests

st.set_page_config(page_title="Reddit Search", layout="wide")
st.title("🔍 Reddit Search")
st.caption("Search Reddit posts instantly - no login required")

@st.cache_data(ttl=300, show_spinner=False)
def search_reddit(query):
    url = "https://www.reddit.com/search.json"
    headers = {"User-Agent": "reddit-search-app/1.0"}
    params = {"q": query, "sort": "relevance", "limit": 20}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        posts = []
        for child in response.json()["data"]["children"]:
            d = child["data"]
            posts.append({
                "title": d.get("title", ""),
                "subreddit": d.get("subreddit_name_prefixed", ""),
                "upvotes": d.get("score", 0),
                "comments": d.get("num_comments", 0),
                "url": "https://reddit.com" + d.get("permalink", ""),
            })
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
        posts = search_reddit(topic)

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
