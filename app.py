import streamlit as st
import requests

st.set_page_config(page_title="Reddit Search", layout="wide")
st.title("🔍 Reddit Search")

def get_token(client_id, client_secret):
    auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
    data = {"grant_type": "client_credentials"}
    headers = {"User-Agent": "reddit-search-app/1.0"}
    r = requests.post("https://www.reddit.com/api/v1/access_token",
                      auth=auth, data=data, headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()["access_token"]

@st.cache_data(ttl=300, show_spinner=False)
def search_reddit(query, client_id, client_secret):
    token = get_token(client_id, client_secret)
    headers = {
        "Authorization": f"bearer {token}",
        "User-Agent": "reddit-search-app/1.0"
    }
    params = {"q": query, "sort": "relevance", "limit": 20}
    r = requests.get("https://oauth.reddit.com/search", headers=headers, params=params, timeout=10)
    r.raise_for_status()
    posts = []
    for child in r.json()["data"]["children"]:
        d = child["data"]
        posts.append({
            "title": d.get("title", ""),
            "subreddit": d.get("subreddit_name_prefixed", ""),
            "upvotes": d.get("score", 0),
            "comments": d.get("num_comments", 0),
            "url": "https://reddit.com" + d.get("permalink", ""),
        })
    return posts

# Check for credentials
if "reddit" not in st.secrets:
    st.error("Reddit API credentials not configured.")
    st.markdown("""
**Setup steps:**

1. Go to [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
2. Click **"create another app"** at the bottom
3. Fill in:
   - **name:** any name
   - **type:** select **script**
   - **redirect uri:** `http://localhost`
4. Click **Create app** — copy the **client ID** (under the app name) and **secret**
5. In Streamlit Cloud → your app → **Settings → Secrets**, paste:
```toml
[reddit]
client_id = "your_client_id"
client_secret = "your_client_secret"
```
6. Save and reboot the app
""")
    st.stop()

client_id = st.secrets["reddit"]["client_id"]
client_secret = st.secrets["reddit"]["client_secret"]

col1, col2 = st.columns([4, 1])
with col1:
    topic = st.text_input("Search topic:", placeholder="e.g., Python, AI, Marketing...")
with col2:
    search_btn = st.button("Search", use_container_width=True)

if search_btn and topic:
    try:
        with st.spinner("Searching Reddit..."):
            posts = search_reddit(topic, client_id, client_secret)
        if posts:
            st.success(f"Found {len(posts)} posts")
            for post in posts:
                st.markdown(f"### [{post['title']}]({post['url']})")
                c1, c2, c3 = st.columns(3)
                c1.metric("Upvotes", f"{post['upvotes']:,}")
                c2.metric("Comments", f"{post['comments']:,}")
                c3.metric("Subreddit", post['subreddit'])
                st.divider()
        else:
            st.warning("No results found. Try a different topic.")
    except Exception as e:
        st.error(f"Error: {e}")
