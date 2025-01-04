from flask import Flask
from flask_cors import CORS
import requests
import json
from flask import request

app = Flask(__name__)
CORS(app)

@app.route("/scrape", methods=["POST"])
def scrapeProfileData():
    userId = request.args.get('userId')
    session = requests.Session()
    BLOCK_SIZE = 1024 * 1024
    path = "profiles/" + userId + "/"
    domain = 'www.instagram.com'
    base = f'https://{domain}'
    user_url = f'{base}/{userId}/'
    url = "https://i.instagram.com/api/v1/users/web_profile_info"
    
    params = {
        "username": userId,
    }
    headers = {
        "x-ig-app-id": "936619743392459",
    }
    response = session.get(url, params=params, headers=headers)
    response.raise_for_status()
    obj = response.json()
    userIdJson = obj["data"]["user"]["id"]
    
    urlQuery = f'{base}/graphql/query/'
    count = 50
    queryHash = 'bd0d6d184eefd4d0ce7036c11ae58ed9'  # posts
    hasNextPage = True
    endCursor = None
    profile_data = []

    while hasNextPage:
        variables = {
            'id': userIdJson,
            'first': count,
        }
        if endCursor:
            variables['after'] = endCursor
        params = {
            'query_hash': queryHash,
            'variables': json.dumps(variables)
        }
        response = session.get(urlQuery, params=params).json()
        dataUser = response['data']['user']['edge_owner_to_timeline_media']
        hasNextPage = dataUser['page_info']['has_next_page']
        endCursor = dataUser['page_info']['end_cursor']

        for outerNode in dataUser['edges']:
            innerNode = outerNode['node']
            post_info = {
                "post_id": innerNode["id"],
                "type": innerNode["__typename"],
                "likes_count": innerNode["edge_media_preview_like"]["count"],
                "comments_count": innerNode["edge_media_to_comment"]["count"],
                "top_comments": [comment["node"]["text"] for comment in innerNode["edge_media_to_comment"]["edges"][:3]],  # Top 3 comments
                "description": innerNode["edge_media_to_caption"]["edges"][0]["node"]["text"] if len(innerNode["edge_media_to_caption"]["edges"]) > 0 else "",
                "date_time": innerNode["taken_at_timestamp"],
                "views_count": innerNode.get("video_view_count", 0) if innerNode["__typename"] == "GraphVideo" else 0,  # Scrape views for videos
            }
            profile_data.append(post_info)

    # Convert profile_data to JSON format
    return json.dumps(profile_data)  # Return JSON data

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0")