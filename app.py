import json
from flask import Flask, request, jsonify
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import google.generativeai as genai
import requests

app = Flask(__name__)

# Google Gemini API Key 설정
GEMINI_API_KEY = 'AIzaSyDAqUu3rya4Fg7JMKcsoEgKTpyXDjPOeMA'  # 여기에 실제 Google Gemini API Key를 입력하세요

# Google Gemini API 설정
genai.configure(api_key=GEMINI_API_KEY)

# Spotify API Key 설정
SPOTIFY_CLIENT_ID = '746e94ef4d33426b958a92ea44fc549b'  # 여기에 실제 Spotify Client ID를 입력하세요
SPOTIFY_CLIENT_SECRET = 'd51c96b3b17c4f82a926535f77d8f7b1'  # 여기에 실제 Spotify Client Secret을 입력하세요

spotify_auth_manager = SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)
spotify = spotipy.Spotify(auth_manager=spotify_auth_manager)

# 네이버 API 설정
client_id = 'qHQ2siKEc06lLOHc0Zq9'  # 여기에 실제 네이버 클라이언트 ID를 입력하세요
client_secret = 'WaDwGJB2GL'  # 여기에 실제 네이버 클라이언트 Secret을 입력하세요

queries = {
    '정치': '정치',
    '경제': '경제',
    '사회': '사회',
    '생활/문화': '생활문화',
    '세계': '세계',
    'IT/과학': 'IT과학'
}

headers = {
    'X-Naver-Client-Id': client_id,
    'X-Naver-Client-Secret': client_secret
}

def get_news(query):
    url = f"https://openapi.naver.com/v1/search/news.json?query={query}&display=5&start=1&sort=sim"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error Code: {response.status_code}")
        print(f"Error Message: {response.text}")
        return None

@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        data = request.json
        if not data:
            raise ValueError("No data provided")

        diary_entry = data.get('diary_entry')
        genre = data.get('genre')

        if not diary_entry or not genre:
            raise ValueError("Diary entry and genre are required")

        print(f'Received diary entry: {diary_entry}')
        print(f'Received genre: {genre}')

        prompt = f"""
        Based on the following diary entry and the preferred genre "{genre}", recommend three suitable songs with their artists using Spotify music data. 
        Provide each recommendation in the following format:
        Music Recommendation 1: [Song Title] by [Artist]
        Reason 1: [Reason for Recommendation]
        Music Recommendation 2: [Song Title] by [Artist]
        Reason 2: [Reason for Recommendation]
        Music Recommendation 3: [Song Title] by [Artist]
        Reason 3: [Reason for Recommendation]
        Diary Entry: "{diary_entry}"
        """

        model = genai.GenerativeModel('gemini-pro')
        gemini_response = model.generate_content(prompt)

        if gemini_response and gemini_response.text:
            recommendations = parse_recommendations(gemini_response.text)
            for rec in recommendations:
                track, artist = rec['track'], rec['artist']
                rec['spotify_link'] = search_spotify(track, artist)
            return jsonify(recommendations)
        else:
            raise ValueError("Failed to generate recommendations")
    except Exception as e:
        print(f'Error: {e}')
        return jsonify({'error': str(e)}), 500

def parse_recommendations(response_text):
    recommendations = []
    lines = response_text.split('\n')
    for i in range(0, len(lines), 2):
        if lines[i].startswith('Music Recommendation'):
            track_artist = lines[i].split('by')
            if len(track_artist) == 2:
                track = track_artist[0].split(':', 1)[1].strip()
                artist = track_artist[1].strip()
                reason = lines[i+1].split(':', 1)[1].strip()
                recommendations.append({'track': track, 'artist': artist, 'reason': reason})
    return recommendations

def search_spotify(track, artist):
    queries = [
        f"{track} {artist}",
        f"track:{track} artist:{artist}",
        f"{track}",
    ]
    for query in queries:
        results = spotify.search(q=query, type='track', limit=1)
        tracks = results['tracks']['items']
        if tracks:
            print(tracks)
            return tracks[0]['external_urls']['spotify']
    return "No Spotify link found."

@app.route('/news', methods=['GET'])
def news():
    try:
        news_data = {}
        for category, query in queries.items():
            category_news = get_news(query)
            if category_news:
                news_data[category] = [
                    {
                        'title': item['title'],
                        'link': item['link'],
                        'description': item['description']
                    }
                    for item in category_news['items']
                ]
        return jsonify(news_data)
    except Exception as e:
        print(f'Error: {e}')
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
