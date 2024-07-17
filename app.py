from flask import Flask, request, jsonify
import google.generativeai as genai
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from flask_cors import CORS
import json
import requests

app = Flask(__name__)
CORS(app)

# Google Gemini API Key 설정
GEMINI_API_KEY = ''  # 여기에 실제 Google Gemini API Key를 입력하세요
genai.configure(api_key=GEMINI_API_KEY)

# Spotify API Key 설정
SPOTIFY_CLIENT_ID = ''  # 여기에 실제 Spotify Client ID를 입력하세요
SPOTIFY_CLIENT_SECRET = ''  # 여기에 실제 Spotify Client Secret을 입력하세요
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

def clean_html_tags(text):
    return text.replace('<br>', '').replace('&quot;', '')

def get_news(query):
    url = f"https://openapi.naver.com/v1/search/news.json?query={query}&display=5&start=1&sort=sim"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        news_items = response.json().get('items', [])
        cleaned_news_items = []
        for item in news_items:
            cleaned_item = {
                'title': clean_html_tags(item['title']),
                'link': item['link'],
                'description': clean_html_tags(item['description'])
            }
            cleaned_news_items.append(cleaned_item)
        return cleaned_news_items
    else:
        print(f"Error Code: {response.status_code}")
        print(f"Error Message: {response.text}")
        return None

@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.json
    diary_entry = data.get('diary_entry')
    genre = data.get('genre')

    recommendations, reasons = ask_gemini_for_music_recommendation(diary_entry, genre)
    result = []
    for i in range(3):
        if "by" in recommendations[i]:
            track, artist = recommendations[i].split(" by ")
            spotify_link = search_spotify(track.strip(), artist.strip())
            result.append({
                'recommendation': recommendations[i],
                'reason': reasons[i],
                'spotify_link': spotify_link
            })
        else:
            result.append({
                'recommendation': recommendations[i],
                'reason': reasons[i],
                'spotify_link': ''
            })
    return jsonify(result)

def ask_gemini_for_music_recommendation(diary_entry, genre):
    print(genre)
    try:
        model = genai.GenerativeModel('gemini-pro')
        prompt = (f'Based on the following diary entry and the preferred genre "{genre}", recommend three suitable songs with their artists. '
                  f'Provide each recommendation in the following format:\n'
                  f'Music Recommendation 1: [Song Title] by [Artist]\n'
                  f'Reason 1: [Reason for Recommendation]\n'
                  f'Music Recommendation 2: [Song Title] by [Artist]\n'
                  f'Reason 2: [Reason for Recommendation]\n'
                  f'Music Recommendation 3: [Song Title] by [Artist]\n'
                  f'Reason 3: [Reason for Recommendation]\n'
                  f'Diary Entry: "{diary_entry}".')
        gemini_response = model.generate_content(prompt)
        
        response_text = gemini_response.text if gemini_response and gemini_response.text else "추천할 음악을 생성할 수 없습니다."
        
        recommendations = ["추천할 음악을 생성할 수 없습니다."] * 3
        reasons = [""] * 3
        
        if response_text:
            lines = response_text.split('\n')
            for line in lines:
                if line.startswith("Music Recommendation 1:"):
                    recommendations[0] = line.replace("Music Recommendation 1:", "").strip()
                elif line.startswith("Reason 1:"):
                    reasons[0] = line.replace("Reason 1:", "").strip()
                elif line.startswith("Music Recommendation 2:"):
                    recommendations[1] = line.replace("Music Recommendation 2:", "").strip()
                elif line.startswith("Reason 2:"):
                    reasons[1] = line.replace("Reason 2:", "").strip()
                elif line.startswith("Music Recommendation 3:"):
                    recommendations[2] = line.replace("Music Recommendation 3:", "").strip()
                elif line.startswith("Reason 3:"):
                    reasons[2] = line.replace("Reason 3:", "").strip()
        
        return recommendations, reasons
    except Exception as e:
        error_message = f"Failed to get recommendation from Gemini: {e}"
        print(error_message)
        return ["Error: Failed to get recommendation from Gemini."] * 3, [""] * 3

def search_spotify(track, artist):
    query = f"track:{track} artist:{artist}"
    results = spotify.search(q=query, type='track', limit=1)
    tracks = results['tracks']['items']
    
    if tracks:
        return tracks[0]['external_urls']['spotify']
    else:
        query = f"{artist} {track}"
        results = spotify.search(q=query, type='track', limit=1)
        tracks = results['tracks']['items']
        if tracks:
            return tracks[0]['external_urls']['spotify']
        else:
            return "No Spotify link found."

@app.route('/news', methods=['GET'])
def news():
    try:
        news_data = {}
        for category, query in queries.items():
            category_news = get_news(query)
            if category_news:
                news_data[category] = category_news
        return jsonify(news_data)
    except Exception as e:
        print(f'Error: {e}')
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
