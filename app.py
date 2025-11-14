import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from datetime import datetime
import os
from dotenv import load_dotenv

# 環境変数を読み込む
if load_dotenv():
    load_dotenv()
    print(".env を読み込みました")
else:
    print(".env が見つかりませんでした")
    os.environ["OPENWEATHER_API_KEY"] = st.secrets["OPENWEATHER_API_KEY"]


# ページ設定
st.set_page_config(
    page_title="横浜市現在気象マップ",
    page_icon="🌤️",
    layout="wide"
)

# タイトル
st.title("🌤️ 横浜市の現在の気象情報マップ")
st.markdown("みなとみらい・センター北・日吉の現在の気象情報を地図で確認")

# OpenWeatherMapのAPIキー設定（.envファイルからのみ読み込み）
API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

# 地点情報（横浜市の3地点）
locations = {
    'みなとみらい': {
        'lat': 35.4550,
        'lon': 139.6320,
        'icon': 'cloud-sun',
        'color': '#FF4444'  # 鮮やかな赤色
    },
    'センター北': {
        'lat': 35.5530,
        'lon': 139.5730,
        'icon': 'cloud',
        'color': '#4466FF'  # 鮮やかな青色
    },
    '日吉': {
        'lat': 35.5531,
        'lon': 139.6460,
        'icon': 'sun',
        'color': '#44AA44'  # 鮮やかな緑色
    }
}

# 天気情報を取得する関数
def get_weather(lat, lon, api_key):
    """OpenWeatherMap APIから天気情報を取得"""
    if not api_key:
        return None
    
    url = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=ja'
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            # 認証エラー（APIキーが無効）
            error_msg = response.json().get('message', '認証エラー')
            st.error(f"🔐 **認証エラー (401)**: {error_msg}")
            st.info("""
            **解決方法:**
            1. APIキーが正しく入力されているか確認してください
            2. OpenWeatherMapのアカウントでAPIキーが有効になっているか確認してください
            3. APIキーをコピー&ペーストする際、余分なスペースが入っていないか確認してください
            4. 新しいAPIキーを取得して、再度入力してください
            """)
            return None
        elif response.status_code == 429:
            # レート制限エラー
            st.warning("⚠️ **リクエスト制限**: リクエストが多すぎます。しばらく待ってから再度お試しください。")
            return None
        else:
            error_data = response.json() if response.content else {}
            error_msg = error_data.get('message', f'HTTP {response.status_code} エラー')
            st.error(f"❌ **APIエラー ({response.status_code})**: {error_msg}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"🌐 **接続エラー**: {str(e)}")
        return None
    except Exception as e:
        st.error(f"❌ **エラーが発生しました**: {str(e)}")
        return None

# 天気アイコンを取得する関数
def get_weather_icon(weather_code):
    """天気コードからアイコン名を取得"""
    icon_map = {
        '01d': '☀️',  # clear sky day
        '01n': '🌙',  # clear sky night
        '02d': '⛅',  # few clouds day
        '02n': '☁️',  # few clouds night
        '03d': '☁️',  # scattered clouds
        '03n': '☁️',
        '04d': '☁️',  # broken clouds
        '04n': '☁️',
        '09d': '🌧️', # shower rain
        '09n': '🌧️',
        '10d': '🌦️', # rain day
        '10n': '🌧️', # rain night
        '11d': '⛈️', # thunderstorm
        '11n': '⛈️',
        '13d': '🌨️', # snow
        '13n': '🌨️',
        '50d': '🌫️', # mist
        '50n': '🌫️'
    }
    return icon_map.get(weather_code, '☁️')

# APIキーの確認
if not API_KEY:
    st.error("⚠️ APIキーが設定されていません")
    st.info("""
    **APIキーの設定方法:**
    1. [OpenWeatherMap](https://openweathermap.org/)にアクセス
    2. アカウントを作成（無料）
    3. API Keysからキーを取得
    4. プロジェクトフォルダに `.env` ファイルを作成し、以下を記述してください：
    
    ```
    OPENWEATHER_API_KEY=あなたのAPIキー
    ```
    
    セキュリティ上の理由で、APIキーは.envファイルでのみ設定可能です。
    """)
else:
    # 地図の作成（横浜市を中心に）
    m = folium.Map(
        location=[35.5, 139.6],
        zoom_start=11,
        tiles='OpenStreetMap'
    )
    
    # 各地点の天気情報を取得
    with st.spinner('天気情報を取得中...'):
        for name, coords in locations.items():
            weather = get_weather(coords['lat'], coords['lon'], API_KEY)
            
            if weather:
                temp = weather['main']['temp']
                feels_like = weather['main']['feels_like']
                humidity = weather['main']['humidity']
                description = weather['weather'][0]['description']
                icon_code = weather['weather'][0]['icon']
                weather_icon = get_weather_icon(icon_code)
                
                # ポップアップテキストの作成
                popup_html = f"""
                <div style="text-align: center; min-width: 150px;">
                    <h3>{name}</h3>
                    <p style="font-size: 24px;">{weather_icon}</p>
                    <p><b>{description}</b></p>
                    <p>気温: <b>{temp:.1f}℃</b></p>
                    <p>体感: {feels_like:.1f}℃</p>
                    <p>湿度: {humidity}%</p>
                </div>
                """
                
                ## 地名を表示するカスタムアイコンを作成
                location_color = coords.get('color', 'red')
                icon_html = f"""
                <div style="
                    width: 50px;
                    height: 50px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: bold;
                    color: {location_color};
                    font-size: 20px;
                ">
                    📍
                </div>
                """
                
                # 地名ラベル用のHTML（地名、天気、温度を縦に表示）
                name_length = len(name)
                # 地名、天気、温度を考慮して幅を調整
                label_width = max(120, name_length * 10)  # 地名に合わせて幅を調整
                label_html = f"""
                <div style="
                    color: blue;
                    padding: 6px 12px;
                    font-weight: bold;
                    font-size: 14px;
                    text-align: center;
                    line-height: 1.4;
                ">
                    {name}<br/>
                    {description}<br/>
                    {temp:.1f}℃<br/>
                    &nbsp;
                </div>
                """
                
                # マーカーを地図に追加（アイコン付き）
                icon = folium.DivIcon(
                    html=icon_html,
                    icon_size=(50, 50),
                    icon_anchor=(25, 50)
                )
                folium.Marker(
                    location=[coords['lat'], coords['lon']],
                    popup=folium.Popup(popup_html, max_width=200),
                    tooltip=f"{name}: {weather_icon} {temp:.1f}℃",
                    icon=icon
                ).add_to(m)
                
                # 地名ラベルを追加（マーカーの上に表示）
                label_icon = folium.DivIcon(
                    html=label_html,
                    icon_size=(label_width, 80),  # 3行分の高さに調整
                    icon_anchor=(label_width/2, 90)  # アンカーを下に調整してラベルを上に
                )
                folium.Marker(
                    location=[coords['lat'] + 0.0045, coords['lon']],  # さらに上に移動（温度がピンと重ならないように）
                    icon=label_icon,
                    tooltip=name
                ).add_to(m)
                
    # 地図を表示
    st.subheader("🗺️ 地図表示")
    st_folium(m, width=None, height=600)
    update_time = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    st.caption(f"Last updated: {update_time}")
    


