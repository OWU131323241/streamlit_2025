import streamlit as st
import requests
from datetime import datetime
import google.generativeai as genai

st.title("🌤️ AIお出かけスポット提案アプリ")


owm_api_key = st.sidebar.text_input("🔑 OpenWeatherMap APIキー", type="password")
gemini_api_key = st.sidebar.text_input("🔑 Gemini APIキー", type="password")


if gemini_api_key:
    genai.configure(api_key=gemini_api_key)


place_name = st.text_input("📍 行きたい場所（市区町村もOK・日本語）", placeholder="例: 渋谷区, 京都市, 札幌")
date = st.date_input("📅 日付を選択")
time = st.time_input("🕒 時間を選択")
companion = st.selectbox("👥 同行者", ["一人", "恋人", "家族", "友人"])


def get_coordinates_from_place(place_name):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": place_name,
        "format": "json",
        "limit": 1
    }
    res = requests.get(url, params=params, headers={"User-Agent": "my-app"})
    if res.status_code == 200 and res.json():
        data = res.json()[0]
        return float(data["lat"]), float(data["lon"]), data.get("display_name", "")
    return None, None, None

def get_weather_by_coordinates(lat, lon, api_key, target_datetime):
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric",
        "lang": "ja"
    }
    res = requests.get(url, params=params)
    if res.status_code != 200:
        return None
    data = res.json()
    closest = min(data["list"], key=lambda x: abs(datetime.fromtimestamp(x["dt"]) - target_datetime))
    return {
        "description": closest["weather"][0]["description"],
        "temp": closest["main"]["temp"],
        "humidity": closest["main"]["humidity"],
        "pop": closest.get("pop", 0) * 100,  
        "datetime": datetime.fromtimestamp(closest["dt"])
    }

def generate_spot_suggestions(location, weather, temp, humidity, pop, companion, dt):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
あなたは旅行アドバイザーです。
以下の条件に基づいて、日本国内のお出かけスポットを3つ提案してください。

- 日時: {dt.strftime('%Y-%m-%d %H:%M')}
- 場所: {location}
- 天気: {weather}
- 気温: {temp}℃
- 湿度: {humidity}%
- 降水確率: {pop:.0f}%
- 同行者: {companion}

以下の形式で出力してください:
1. スポット名 - 一言説明
2. スポット名 - 一言説明
3. スポット名 - 一言説明

屋内か屋外かなど、天気・降水確率との相性にも配慮してください。
親しみやすく、短く、分かりやすくお願いします。
"""
    response = model.generate_content(prompt)
    return response.text.strip()


if st.button("🎉 お出かけプランを提案"):
    if not place_name or not owm_api_key or not gemini_api_key:
        st.warning("場所・APIキーを入力してください。")
    else:
        lat, lon, full_name = get_coordinates_from_place(place_name)
        if lat is None:
            st.error("場所の検索に失敗しました。正しい地名を日本語で入力してください。")
        else:
            target_dt = datetime.combine(date, time)
            weather_info = get_weather_by_coordinates(lat, lon, owm_api_key, target_dt)

            if not weather_info:
                st.error("天気情報の取得に失敗しました。APIキーまたは場所・日時を確認してください。")
            else:
                st.markdown("### ☁️ 天気情報")
                st.markdown(f"""
                - **場所**: {full_name}  
                - **日時**: {weather_info['datetime'].strftime('%Y-%m-%d %H:%M')}  
                - **天気**: {weather_info['description']}  
                - **気温**: {weather_info['temp']} ℃  
                - **湿度**: {weather_info['humidity']} %  
                - **降水確率**: {weather_info['pop']:.0f} %
                """)


                st.markdown("### 🗺️ AIによるお出かけスポット提案")
                with st.spinner("AIが提案を考えています..."):
                    suggestions = generate_spot_suggestions(
                        full_name,
                        weather_info["description"],
                        weather_info["temp"],
                        weather_info["humidity"],
                        weather_info["pop"],         
                        companion,
                        target_dt                    
                    )
                st.markdown(suggestions)

