import requests
import csv
import folium
import streamlit as st
from streamlit_folium import st_folium
from streamlit_image_select import image_select
from folium import plugins
from datetime import datetime, timedelta
import pandas as pd
import streamlit.components.v1 as components
import os
from bs4 import BeautifulSoup
from PIL import Image

###### 번역 테스트
from googletrans import Translator  # Google Translate API 라이브러리 사용

# Streamlit 페이지 설정 (파일 맨 위에서 선언)
st.set_page_config(page_title="자전거", page_icon='🚴', layout="wide")


# 번역기 초기화
translator = Translator()

# 번역 버튼 상태 관리
if "translate" not in st.session_state:
    st.session_state.translate = False  # False: 한글, True: 영어

# 번역 버튼
if st.button("번역하기/Translating"):
    st.session_state.translate = not st.session_state.translate  # 상태 토글

# 번역 함수
def translate_text(text, target_language="en"):
    if st.session_state.translate:
        try:
            translated = translator.translate(text, dest=target_language)
            return translated.text
        except Exception as e:
            st.error("번역에 실패했습니다.")
            return text
    return text

####### 번역 테스트



# 세션 상태 초기화
if 'current_page' not in st.session_state:
    st.session_state.current_page = '프로젝트 소개'


# 위치 경도위도 초기화
if 'latitude' not in st.session_state:
    st.session_state.latitude = None
if 'longitude' not in st.session_state:
    st.session_state.longitude = None


# 페이지 전환 함수
def switch_page(page_name):
    st.session_state.current_page = page_name

# 사이드바 버튼
st.sidebar.title(translate_text("페달이 프로젝트", target_language="en" if st.session_state.translate else "ko"))
st.sidebar.button(
    translate_text("프로젝트 소개", target_language="en" if st.session_state.translate else "ko"),
    on_click=lambda: switch_page("프로젝트 소개")
)
st.sidebar.button(
    translate_text("자전거 위치 정보", target_language="en" if st.session_state.translate else "ko"),
    on_click=lambda: switch_page("자전거 위치 정보")
)
st.sidebar.button(
    translate_text("관광지 추천", target_language="en" if st.session_state.translate else "ko"),
    on_click=lambda: switch_page("관광지 추천")
)


# GPS 위치 가져오기 (JavaScript 삽입)
gps_html = """
<script>
    navigator.geolocation.getCurrentPosition(
        (position) => {
            const latitude = position.coords.latitude;
            const longitude = position.coords.longitude;
            window.parent.postMessage({ latitude: latitude, longitude: longitude }, "*");
        },
        (error) => {
            console.error("Error getting location:", error);
            window.parent.postMessage({ error: "Unable to fetch location." }, "*");
        }
    );
</script>
"""
components.html(gps_html, height=0, width=0)

    # 현재 위치 추가
if st.session_state.latitude and st.session_state.longitude:
    folium.Marker(
        [float(st.session_state.latitude), float(st.session_state.longitude)],
        popup="📍 내 위치",
        icon=folium.Icon(color="red", icon="info-sign")
    ).add_to(map)


# JavaScript에서 위치 정보를 가져오는 콜백
msg = st.query_params
if "latitude" in msg and "longitude" in msg:
    st.session_state.latitude = msg["latitude"][0]
    st.session_state.longitude = msg["longitude"][0]



# CSV 데이터 로드
bike_rental_data = []
with open('부산광역시_자전거대여소_20230822.csv', newline='', encoding='UTF-8') as csvfile:
    reader = csv.reader(csvfile)
    next(reader)  # 헤더 행 건너뛰기
    for row in reader:
        entry = {
            'name': row[0],
            'address': row[3],
            'latitude': float(row[4]),
            'longitude': float(row[5])
        }
        bike_rental_data.append(entry)

park_data = []
with open('부산 도시 공원.csv', newline='', encoding='UTF-8') as csvfile:
    reader = csv.reader(csvfile)
    next(reader)  # 헤더 행 건너뛰기
    for row in reader:
        entry = {
            'name': row[1],
            'address': row[4],
            'latitude': float(row[5]),
            'longitude': float(row[6])
        }
        park_data.append(entry)

bike_storage_data = []
with open('자전거 보관소 데이터_filltered.csv', newline='', encoding='UTF-8') as csvfile:
    reader = csv.reader(csvfile)
    next(reader)  # 헤더 행 건너뛰기
    for row in reader:
        entry = {
            'address': row[0],
            'latitude': float(row[1]),
            'longitude': float(row[2])
        }
        bike_storage_data.append(entry)

hospital_data = []

# CSV 파일 열기
with open('부산광역시_종합병원 현황_20230927.csv', newline='', encoding='euc-kr') as csvfile:
    reader = csv.reader(csvfile)
    next(reader)  # 첫 번째 행(헤더) 건너뛰기
    
    # 각 행을 반복하면서 데이터 파싱
    for row in reader:
        # 데이터 딕셔너리 생성
        entry = {
            'name': row[1],  # 의료기관명
            'address': row[3],  # 도로명주소
            'latitude': float(row[4]),  # 위도
            'longitude': float(row[5]),  # 경도
            'phone': row[6]  # 전화번호
        }
        # 리스트에 추가
        hospital_data.append(entry)


# 현재 부산의 날씨 정보를 가져오는 함수
def get_current_weather():
    url = f"http://api.openweathermap.org/data/2.5/weather?lat=35.1796&lon=129.0756&appid=7abbc2847b7691c9ab5da95f24166c8e&units=metric"
    response = requests.get(url)
    weather_data = response.json()
    return weather_data


# 부산의 일기예보 정보를 가져오는 함수
def get_forecast():
    url = f"http://api.openweathermap.org/data/2.5/forecast?lat=35.1796&lon=129.0756&appid=7abbc2847b7691c9ab5da95f24166c8e&units=metric"
    response = requests.get(url)
    forecast_data = response.json()
    return forecast_data

weather_images = {
    "Clear": "images/clear_sky.png",
    "Clouds": "images/cloudy.png",
    "Rain": "images/rain.png",
    "Drizzle": "images/drizzle.png",
    "Thunderstorm": "images/thunderstorm.png",
    "Snow": "images/snow.png",
    "Mist": "images/mist.png",
    "Smoke": "images/smoke.png",
    "Fog": "images/fog.png",
    "Tornado": "images/tornado.png"
}

def get_weather_image(weather_main):
    return weather_images.get(weather_main, "images/default.png")
    

# 현재 날씨 정보 가져오기
weather_data = get_current_weather()
temp = weather_data['main']['temp']
weather_main = weather_data['weather'][0]['main']  # 주요 분류값
weather_description = weather_data['weather'][0]['description']

# 날씨에 맞는 이미지 파일 경로 가져오기
weather_image_path = get_weather_image(weather_main)
weather_image = Image.open(weather_image_path)

# 일기예보 정보 가져오기
forecast_data = get_forecast()

# Streamlit 사이드바에 현재 날씨 정보 표시
st.sidebar.header(translate_text('현재 부산 날씨', target_language='en'))
st.sidebar.write(f"{translate_text('기온', target_language='en')}: {temp}°C")
st.sidebar.write(f"{translate_text('날씨', target_language='en')}: {translate_text(weather_description, target_language='en')}")
st.sidebar.image(weather_image, width=100)  # 원하는 너비로 조정


# 자전거 타기 좋은 날 판단
if weather_description in ['clear sky', 'few clouds', 'scattered clouds', 'broken clouds']:
    st.sidebar.success(translate_text("자전거 타기 좋은 날이네요!", target_language='en'))
else:
    st.sidebar.warning(translate_text("자전거 타러 나가는 걸 다시 생각해 보세요!", target_language='en'))


# 예측된 일기예보에서 자전거 타기 좋은 시간 찾기
def find_good_biking_time(forecast_data, days=3):
    good_times = []
    now = datetime.utcnow()
    end_time = now + timedelta(days=days)  # 3일 후까지의 데이터를 사용

    for forecast in forecast_data['list']:
        forecast_time = datetime.utcfromtimestamp(forecast['dt'])
        if forecast_time > end_time:
            continue
        temp = forecast['main']['temp']
        weather_description = forecast['weather'][0]['description']
        if  weather_description in ['clear sky', 'few clouds', 'scattered clouds', 'broken clouds']:
            good_times.append({
                translate_text("날짜", target_language='en'): forecast_time.strftime('%Y-%m-%d'),
                translate_text("요일", target_language='en'): forecast_time.strftime('%A'),
                translate_text("시간", target_language='en'): forecast_time.strftime('%H:%M'),
                translate_text("기온 (°C)", target_language='en'): temp,
                translate_text("날씨 설명", target_language='en'): weather_description
            })
    return good_times


# 자전거 타기 좋은 시간대 찾기
good_times = find_good_biking_time(forecast_data, days=3)

# Streamlit에 자전거 타기 좋은 시간대를 표로 표시
st.sidebar.header(translate_text("자전거 타기 추천 시간 (다음 3일)", target_language='en'))
if good_times:
    df_good_times = pd.DataFrame(good_times)
    st.sidebar.dataframe(df_good_times)
else:
    st.sidebar.write(translate_text("앞으로 3일 동안 자전거 타기 좋은 시간이 없습니다.", target_language='en'))


# 메인 화면
if st.session_state.current_page == '프로젝트 소개':
    st.markdown(
        f"<h1 style='font-size:24px; '>{translate_text('페달이 소개', target_language='en')}</h1>",
        unsafe_allow_html=True
    )
        # 언어에 따른 이미지 분기
    if not st.session_state.translate:  # 한글 상태일 때
        st.image("images/home1.png", use_container_width=True)
        st.image("images/home2.png", use_container_width=True)
    else:  # 영어일 때
        st.image("images/main_image_1.jpg", use_container_width=True)
        st.image("images/main_image_2.jpg", use_container_width=True)




# 자전거 위치 정보 화면
elif st.session_state.current_page == '자전거 위치 정보':
    st.markdown(
        f"<h1 style='font-size:24px; '>{translate_text('부산광역시 자전거 위치 정보', target_language='en')}</h1>",
        unsafe_allow_html=True
    )


    # 이미지 선택 옵션과 관련된 데이터
    option_images = {
        "자전거 대여소": "images/2.png",
        "도시공원": "images/3.png",
        "자전거 보관소": "images/4.png",
        "종합 병원": "images/5.png"
    }

        # 언어에 따른 캡션 설정
    if not st.session_state.translate:  # 한글 상태일 때
        captions = list(option_images.keys())
    else:  # 영어 상태일 때
        captions = ["Bike Rentals", "City Park", "Bike Storage", "General Hospital"]
    
    # 이미지 선택 위젯
    selected_option_index = image_select(
        " ",
        images=list(option_images.values()),  # 이미지 리스트
        captions=captions,  # 각 이미지에 대한 캡션
        index=0,  # 기본 선택 (0번째 옵션)
        return_value="index"  # 선택된 이미지의 인덱스를 반환
    )
    


        # 선택된 옵션 이름
    selected_option = list(option_images.keys())[selected_option_index]
    
    # 번역된 옵션 이름 가져오기
    translated_option_name = translate_text(selected_option, target_language='en')
    translated_information = translate_text('위치 정보', target_language='en')
    # 선택된 옵션에 대한 정보 출력
    st.write(f"**{translated_option_name + ' ' + translated_information}**")

    
    # 데이터 로드 (각각의 데이터는 이미 파일에서 로드되어 있음)
    if selected_option == '자전거 대여소':
        selected_data = bike_rental_data
        icon_type = {'icon': 'bicycle', 'color': 'blue'}
        show_name = translated_option_name
    elif selected_option == '도시공원':
        selected_data = park_data
        icon_type = {'icon': 'tree', 'color': 'green'}
        show_name =  translated_option_name
    elif selected_option == '종합 병원':
        selected_data = hospital_data
        icon_type = {'icon': 'hospital', 'color': 'purple'}
        show_name =  translated_option_name
    else:  # 자전거 보관소
        selected_data = bike_storage_data
        icon_type = {'icon': 'lock', 'color': 'red'}
        show_name =  translated_option_name

    # 지도 생성
    map = folium.Map(location=[35.23164602460444, 129.0838577311402], zoom_start=12)
    plugins.LocateControl().add_to(map)

    # 선택된 데이터를 지도에 추가
    for place in selected_data:
        location = [place['latitude'], place['longitude']]

        kakao_directions_url = (f"https://map.kakao.com/link/to/{place['address']},"
                                f"{place['latitude']},{place['longitude']}")


                # HTML 텍스트 번역 함수 정의
        def translate_html_content(html_content, target_language="en"):
            try:
                # BeautifulSoup으로 HTML 파싱
                soup = BeautifulSoup(html_content, "html.parser")
                
                # 텍스트만 추출해서 번역
                for element in soup.find_all(text=True):
                    if element.parent.name not in ["a", "href"]:  # 링크 및 태그는 제외
                        translated_text = translator.translate(element, dest=target_language).text
                        element.replace_with(translated_text)
                
                # 번역된 HTML 반환
                return str(soup)
            except Exception as e:
                print(f"Translation error: {e}")
                return html_content
                
                # Streamlit에서 번역 상태를 관리하기 위한 변수 초기화
        if "translate" not in st.session_state:
            st.session_state.translate = False
       
        # 팝업 텍스트 설정 (번역 포함)
        if show_name and 'name' in place and place['name'] is not None:
            popup_text_korean = (f"<div style='font-family:sans-serif; font-size:14px;'>"
                                 f"이름: {place['name']}<br>"
                                 f"주소: <a href='{kakao_directions_url}' target='_blank'>{place['address']}</a><br>"
                                 f"<a href='{kakao_directions_url}' target='_blank'>길찾기 (카카오맵)</a></div>")
            # HTML 텍스트 번역
            popup_text = translate_html_content(popup_text_korean, target_language="en")
        else:
            popup_text_korean = (f"<div style='font-family:sans-serif; font-size:14px;'>"
                                 f"주소: <a href='{kakao_directions_url}' target='_blank'>{place['address']}</a><br>"
                                 f"<a href='{kakao_directions_url}' target='_blank'>길찾기 (카카오맵)</a></div>")
            # HTML 텍스트 번역
            popup_text = translate_html_content(popup_text_korean, target_language="en")

              

        
        # 마커 추가
        folium.Marker(location,
                      popup=folium.Popup(popup_text, max_width=300),
                      icon=folium.Icon(icon=icon_type['icon'], color=icon_type['color'],
                                       prefix='fa')).add_to(map)
        

    # 지도 표시
    st_folium(map, height=700, width=1000)


# 화면 3
elif st.session_state.current_page == '관광지 추천':


    # 먼저 번역된 텍스트를 변수에 할당합니다.
    translated_text = translate_text("관광지 추천 및 경로", target_language='en')
    
    # 번역된 텍스트를 HTML에 포함시킵니다.
    st.markdown(
        f"<h1 style='font-size:24px;'>{translated_text}</h1>",
        unsafe_allow_html=True
    )
    
    # URL 정의
    url1 = 'https://kko.kakao.com/1_de9FgI47'
    url2 = 'https://kko.kakao.com/qq3xXZX0XT'
    url3 = 'https://kko.kakao.com/7alrtOKbX3'


    # 이미지와 URL 설정
    image_paths = ["images/title1.jpg", "images/title2.png", "images/title3.png"]
    # 번역된 캡션
    captions_kr = ["동래", "광안리", "기장"]  # 한글 캡션
    captions_en = ["Dongnae", "Gwangalli", "Gijang"]  # 영어 캡션
    urls = ["https://kko.kakao.com/1_de9FgI47", "https://kko.kakao.com/qq3xXZX0XT", "https://kko.kakao.com/7alrtOKbX3"]
    # 디테일 이미지 리스트
    details_kr = ["images/detail1.png", "images/detail2.png", "images/detail3.png"]
    details_en = ["images/detail_en1.png", "images/detail_en2.png", "images/detail_en3.png"]
    
    # 상태 초기화
    if "selected_image" not in st.session_state:
        st.session_state.selected_image = None
        st.session_state.selected_url = None
        st.session_state.selected_detail = None


    # 번역 상태에 따른 디테일 이미지 선택
    current_details = details_en if st.session_state.translate else details_kr

    
    # 각 줄에 3개씩 이미지와 버튼 배치
    col1, col2, col3 = st.columns([1, 1, 1])
    # 버튼 텍스트 설정 (번역 상태에 따라 변경)
    button_text_kr = ["동래 코스 보기", "광안리 코스 보기", "기장 코스 보기"]
    button_text_en = ["Dongnae Course", "Gwangalli Course", "Gijang Course"]
    
    # 컬럼별 이미지와 버튼 추가
    with col1:
        st.image(image_paths[0], caption=captions_en[0] if st.session_state.translate else captions_kr[0], use_container_width=True)
        if st.button(button_text_en[0] if st.session_state.translate else button_text_kr[0]):
            st.session_state.selected_image = image_paths[0]
            st.session_state.selected_url = urls[0]
            st.session_state.selected_detail = current_details[0]
    
    with col2:
        st.image(image_paths[1], caption=captions_en[1] if st.session_state.translate else captions_kr[1], use_container_width=True)
        if st.button(button_text_en[1] if st.session_state.translate else button_text_kr[1]):
            st.session_state.selected_image = image_paths[1]
            st.session_state.selected_url = urls[1]
            st.session_state.selected_detail = current_details[1]
    
    with col3:
        st.image(image_paths[2], caption=captions_en[2] if st.session_state.translate else captions_kr[2], use_container_width=True)
        if st.button(button_text_en[2] if st.session_state.translate else button_text_kr[2]):
            st.session_state.selected_image = image_paths[2]
            st.session_state.selected_url = urls[2]
            st.session_state.selected_detail = current_details[2]
    
    # HTML + CSS 애니메이션 추가
    if st.session_state.selected_image:
        st.image(st.session_state.selected_detail, use_container_width=True)
        st.markdown(f"""
            <a href="{st.session_state.selected_url}" target="_blank">
                <button style="
                    padding: 10px 20px; 
                    font-size: 16px; 
                    background-color: #FFFFFF; 
                    border: 0.5px solid #D6D6D6;
                    border-radius: 10px; 
                    cursor: pointer;">
                    { 'Route Guide' if st.session_state.translate else '경로 안내' }
                </button>
            </a>
        """, unsafe_allow_html=True)
