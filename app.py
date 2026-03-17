import re
import streamlit as st
import requests
import xml.etree.ElementTree as ET

st.set_page_config(page_title="Reddit Search", layout="wide")
st.title("🔍 Reddit Search")
st.caption("Search Reddit posts instantly")

def extract_text(html):
    """Strip HTML tags and return clean plain text."""
    text = re.sub(r"<[^>]+>", " ", html or "")
    text = re.sub(r"\s+", " ", text).strip()
    # Remove Reddit submission boilerplate
    text = re.sub(r"submitted by.*", "", text, flags=re.IGNORECASE).strip()
    return text

@st.cache_data(ttl=300, show_spinner=False)
def search_reddit(query):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36"
    }

    # Try OAuth API first if credentials are available
    if "reddit" in st.secrets:
        try:
            auth = requests.auth.HTTPBasicAuth(
                st.secrets["reddit"]["client_id"],
                st.secrets["reddit"]["client_secret"]
            )
            token_r = requests.post(
                "https://www.reddit.com/api/v1/access_token",
                auth=auth,
                data={"grant_type": "client_credentials"},
                headers={"User-Agent": "reddit-search-app/1.0"},
                timeout=10
            )
            token_r.raise_for_status()
            token = token_r.json()["access_token"]
            r = requests.get(
                "https://oauth.reddit.com/search",
                headers={"Authorization": f"bearer {token}", "User-Agent": "reddit-search-app/1.0"},
                params={"q": query, "sort": "relevance", "limit": 25},
                timeout=10
            )
            r.raise_for_status()
            posts = []
            for child in r.json()["data"]["children"]:
                d = child["data"]
                if d.get("is_self") is False and not d.get("selftext"):
                    snippet = "Link post — click to view."
                else:
                    snippet = d.get("selftext", "").strip()[:300]
                    if len(d.get("selftext", "")) > 300:
                        snippet += "..."
                posts.append({
                    "title": d.get("title", ""),
                    "subreddit": d.get("subreddit_name_prefixed", ""),
                    "upvotes": d.get("score", 0),
                    "comments": d.get("num_comments", 0),
                    "url": "https://reddit.com" + d.get("permalink", ""),
                    "snippet": snippet,
                })
            return posts, None
        except Exception:
            pass  # Fall through to RSS

    # Fallback: RSS feed (no credentials needed)
    try:
        r = requests.get(
            "https://www.reddit.com/search.rss",
            headers=headers,
            params={"q": query, "sort": "relevance", "limit": 25},
            timeout=10
        )
        r.raise_for_status()
        root = ET.fromstring(r.content)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall("atom:entry", ns)
        posts = []
        for entry in entries:
            title = entry.findtext("atom:title", default="", namespaces=ns)
            link = entry.find("atom:link", ns)
            url = link.get("href", "") if link is not None else ""

            # Skip subreddit/community pages — only keep actual posts
            if "/comments/" not in url:
                continue

            # Extract subreddit from URL
            parts = url.split("/")
            subreddit = ""
            if "r" in parts:
                idx = parts.index("r")
                if idx + 1 < len(parts):
                    subreddit = "r/" + parts[idx + 1]

            # Extract post body snippet from RSS content
            content_el = entry.find("atom:content", ns)
            raw_html = content_el.text if content_el is not None else ""
            body = extract_text(raw_html)
            snippet = body[:300] + "..." if len(body) > 300 else body

            posts.append({
                "title": title,
                "subreddit": subreddit,
                "upvotes": "—",
                "comments": "—",
                "url": url,
                "snippet": snippet,
            })
        return posts, None
    except Exception as e:
        return [], str(e)

col1, col2 = st.columns([4, 1])
with col1:
    topic = st.text_input("Search topic:", placeholder="e.g., Python, AI, Marketing...")
with col2:
    search_btn = st.button("Search", use_container_width=True)

if search_btn and topic:
    with st.spinner("Searching Reddit..."):
        posts, error = search_reddit(topic)

    if error:
        st.error(f"Error: {error}")
    elif posts:
        st.success(f"Found {len(posts)} posts")
        for post in posts:
            st.markdown(f"### [{post['title']}]({post['url']})")
            if post["snippet"]:
                st.caption(post["snippet"])
            c1, c2, c3 = st.columns(3)
            c1.metric("Upvotes", post["upvotes"])
            c2.metric("Comments", post["comments"])
            c3.metric("Subreddit", post["subreddit"])
            st.divider()
    else:
        st.warning("No results found. Try a different topic.")
