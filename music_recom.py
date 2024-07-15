import google.generativeai as genai
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Google Gemini API Key 설정
GEMINI_API_KEY = 'AIzaSyDAqUu3rya4Fg7JMKcsoEgKTpyXDjPOeMA'  # 여기에 실제 Google Gemini API Key를 입력하세요

# Spotify API Key 설정
SPOTIFY_CLIENT_ID = '746e94ef4d33426b958a92ea44fc549b'  # 여기에 실제 Spotify Client ID를 입력하세요
SPOTIFY_CLIENT_SECRET = 'd51c96b3b17c4f82a926535f77d8f7b1'  # 여기에 실제 Spotify Client Secret을 입력하세요

# Google Gemini API 설정
genai.configure(api_key=GEMINI_API_KEY)

# Spotify API 설정
spotify_auth_manager = SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)
spotify = spotipy.Spotify(auth_manager=spotify_auth_manager)

def ask_gemini_for_music_recommendation(diary_entry, genre):
    try:
        # Google Gemini API를 사용하여 일기와 장르에 맞는 음악 추천
        model = genai.GenerativeModel('gemini-pro')
        prompt = (f'Based on the following diary entry and the preferred genre "{genre}", recommend three suitable songs with their artists using Spotify music data. '
                  f'Provide each recommendation in the following format:\n'
                  f'Music Recommendation 1: [Song Title] by [Artist]\n'
                  f'Reason 1: [Reason for Recommendation]\n'
                  f'Music Recommendation 2: [Song Title] by [Artist]\n'
                  f'Reason 2: [Reason for Recommendation]\n'
                  f'Music Recommendation 3: [Song Title] by [Artist]\n'
                  f'Reason 3: [Reason for Recommendation]\n'
                  f'Diary Entry: "{diary_entry}".')
        gemini_response = model.generate_content(prompt)
        
        # 응답을 텍스트로 추출
        response_text = gemini_response.text if gemini_response and gemini_response.text else "추천할 음악을 생성할 수 없습니다."
        print(response_text)
        # 추천 음악과 이유를 분리하여 추출
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
    queries = [
        f"track:{track} artist:{artist}",
        f"{track} {artist}",
        f"{track}",
    ]
    for query in queries:
        results = spotify.search(q=query, type='track', limit=1)
        tracks = results['tracks']['items']
        if tracks:
            return tracks[0]['external_urls']['spotify']
    return "No Spotify link found."

if __name__ == '__main__':
    while True:
        # 사용자로부터 일기와 음악 장르 입력 받기
        diary_entry = input("Enter your diary entry (or type 'exit' to quit): ")
        if diary_entry.lower() == 'exit':
            break
        genre = input("Enter your preferred music genre: ")
        
        # Gemini API를 사용하여 음악 추천 가져오기
        recommendations, reasons = ask_gemini_for_music_recommendation(diary_entry, genre)
        
        spotify_links = []
        for i in range(3):
            if "by" in recommendations[i]:
                track, artist = recommendations[i].split(" by ")
                spotify_link = search_spotify(track.strip(), artist.strip())
                spotify_links.append(spotify_link)
                print(f"Music Recommendation {i+1}: {recommendations[i]}")
                print(f"Reason {i+1}: {reasons[i]}")
                print(f"Spotify Link {i+1}: {spotify_link}")
            else:
                print(f"Music Recommendation {i+1}: {recommendations[i]}")
                print(f"Reason {i+1}: {reasons[i]}")
        
        print("Spotify Links:", spotify_links)
