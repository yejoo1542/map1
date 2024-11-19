import requests
import csv
import folium
import streamlit as st
from streamlit_folium import st_folium
from folium import plugins
from datetime import datetime, timedelta
import pandas as pd
import streamlit.components.v1 as components
import os

# Streamlit 페이지 설정 (파일 맨 위에서 선언)
st.set_page_config(page_title="자전거", page_icon='🚴', layout="wide")

# 세션 상태 초기화
if 'current_page' not in st.session_state:
    st.session_state.current_page = '메인화면'


# 위치 경도위도 초기화
if 'latitude' not in st.session_state:
    st.session_state.latitude = None
if 'longitude' not in st.session_state:
    st.session_state.longitude = None


# 페이지 전환 함수
def switch_page(page_name):
    st.session_state.current_page = page_name

# 페이지 선택 UI
st.sidebar.title("페이지 선택")
st.sidebar.button("메인화면", on_click=lambda: switch_page("메인화면"))
st.sidebar.button("자전거 위치 정보", on_click=lambda: switch_page("자전거 위치 정보"))
st.sidebar.button("추천관광지", on_click=lambda: switch_page("추천관광지"))


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
msg = st.experimental_get_query_params()
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


# 현재 날씨 정보 가져오기
weather_data = get_current_weather()
temp = weather_data['main']['temp']
weather_description = weather_data['weather'][0]['description']

# 일기예보 정보 가져오기
forecast_data = get_forecast()

# Streamlit 사이드바에 현재 날씨 정보 표시
st.sidebar.header('현재 부산 날씨')
st.sidebar.write(f"기온: {temp}°C")
st.sidebar.write(f"날씨: {weather_description}")

# 자전거 타기 좋은 날 판단
if 15 <= temp <= 25 and weather_description in ['clear sky', 'few clouds', 'scattered clouds', 'broken clouds']:
    st.sidebar.success("자전거 타기 좋은 날이네요!")
else:
    st.sidebar.warning("자전거 타러 나가는 걸 다시 생각해 보세요!")


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
        if 15 <= temp <= 25 and weather_description in ['clear sky', 'few clouds', 'scattered clouds', 'broken clouds']:
            good_times.append({
                "날짜": forecast_time.strftime('%Y-%m-%d'),
                "요일": forecast_time.strftime('%A'),
                "시간": forecast_time.strftime('%H:%M'),
                "기온 (°C)": temp,
                "날씨 설명": weather_description
            })
    return good_times


# 자전거 타기 좋은 시간대 찾기
good_times = find_good_biking_time(forecast_data, days=3)

# Streamlit에 자전거 타기 좋은 시간대를 표로 표시
st.sidebar.header('자전거 타기 추천 시간 (다음 3일)')
if good_times:
    df_good_times = pd.DataFrame(good_times)
    st.sidebar.dataframe(df_good_times)
else:
    st.sidebar.write("앞으로 3일 동안 자전거 타기 좋은 시간이 없습니다.")


# 메인 화면
if st.session_state.current_page == '메인화면':
    st.title("메인화면")
    st.write("페달이 소개랑 사진 등등이 들어갈 화면입니다~")
    # 이미지 경로와 설명
    st.image("test1.jpg", caption="이미지 시험 중", use_column_width=True)


# 자전거 위치 정보 화면
elif st.session_state.current_page == '자전거 위치 정보':
    st.title("부산광역시 자전거 위치 정보")
    st.write("여기에 자전거 관련 정보를 표시합니다.")

        # 이미지 경로를 절대 경로로 변환    
    option_images = {
        "자전거 대여소": "111.png",
        "도시공원":  "222.png",
        "자전거 보관소":  "333.png",
        "종합 병원":  "444.png",
    }
    
    # 선택된 옵션 저장 변수
    if "selected_option" not in st.session_state:
        st.session_state.selected_option = None
    
    st.write("**보기 옵션을 선택하세요:**")
    cols = st.columns(len(option_images))
    
    for idx, (option, image_path) in enumerate(option_images.items()):
        with cols[idx]:
            # CSS 스타일 적용 (선택된 옵션 강조)
            if st.session_state.selected_option == option:
                border_style = "5px solid red"  # 강조 테두리
            else:
                border_style = "2px solid transparent"  # 기본 테두리
    
            # HTML로 이미지 생성
            st.markdown(
                f"""
                <div style="text-align: center; border: {border_style}; border-radius: 10px; padding: 5px;">
                    <img src="{image_path}" style="width: 100%; height: auto;" alt="{option}">
                    <p>{option}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        
        # 버튼 클릭 이벤트 처리
        if st.button(option, key=f"{option}_btn"):
            st.session_state.selected_option = option

    
    # 결과 출력
    if st.session_state.selected_option:
        st.write(f"선택한 옵션: **{st.session_state.selected_option}**")


    # 선택에 따라 아이콘 타입 및 팝업 설정
    if option == '자전거 대여소':
        selected_data = bike_rental_data
        icon_type = {'icon': 'bicycle', 'color': 'blue'}
        show_name = True
    elif option == '도시공원':
        selected_data = park_data
        icon_type = {'icon': 'tree', 'color': 'green'}
        show_name = True
    elif option == '종합 병원':  
        selected_data = hospital_data
        icon_type = {'icon': 'hospital', 'color': 'purple'}
        show_name = True
    else:  # 자전거 보관소
        selected_data = bike_storage_data
        icon_type = {'icon': 'lock', 'color': 'red'}
        show_name = False

    # 지도 생성
    map = folium.Map(location=[35.23164602460444, 129.0838577311402], zoom_start=12)
    plugins.LocateControl().add_to(map)

    # 선택된 데이터를 지도에 추가
    for place in selected_data:
        location = [place['latitude'], place['longitude']]
        
        kakao_directions_url = (f"https://map.kakao.com/link/to/{place['address']},"
                                f"{place['latitude']},{place['longitude']}")

                
        # 팝업 텍스트 설정
        if show_name and 'name' in place and place['name'] is not None:
            popup_text = (f"<div style='font-family:sans-serif; font-size:14px;'>"
                          f"이름: {place['name']}<br>"
                          f"주소: <a href='{kakao_directions_url}' target='_blank'>{place['address']}</a><br>"
                          f"<a href='{kakao_directions_url}' target='_blank'>길찾기 (카카오맵)</a></div>")
        else:
            popup_text = (f"<div style='font-family:sans-serif; font-size:14px;'>"
                          f"주소: <a href='{kakao_directions_url}' target='_blank'>{place['address']}</a><br>"
                          f"<a href='{kakao_directions_url}' target='_blank'>길찾기 (카카오맵)</a></div>")

        folium.Marker(location,
                      popup=folium.Popup(popup_text, max_width=300),
                      icon=folium.Icon(icon=icon_type['icon'], color=icon_type['color'],
                                       prefix='fa')).add_to(map)

    # 지도 표시
    st_folium(map, height=700, width=1000)



# 화면 3
elif st.session_state.current_page == '추천관광지':
    st.title("관광지 추천 및 경로")
    # URL 정의
    url1 = 'https://kko.kakao.com/1_de9FgI47'
    url2 = 'https://kko.kakao.com/qq3xXZX0XT'
    url3 = 'https://kko.kakao.com/x8368YWDdQ'

    # 이미지와 버튼을 가로로 3개 배치
    col1, col2, col3 = st.columns([1, 1, 1])  # 컬럼의 비율을 균등하게 설정

    # 각 컬럼에 이미지와 버튼 배치
    with col1:
        st.image('guide1.png', caption="지도 1", use_column_width=True)  # 이미지 크기 고정
        st.markdown(f'<a href="{url1}" target="_blank"><button style="width: 200px; height: 50px; font-size: 16px;">지도 1로 이동</button></a>', unsafe_allow_html=True)

    with col2:
        st.image('guide2.png', caption="지도 2", use_column_width=True)  # 이미지 크기 고정
        st.markdown(f'<a href="{url2}" target="_blank"><button style="width: 200px; height: 50px; font-size: 16px;">지도 2로 이동</button></a>', unsafe_allow_html=True)

    with col3:
        st.image('guide3.png', caption="지도 3", use_column_width=True)  # 이미지 크기 고정
        st.markdown(f'<a href="{url3}" target="_blank"><button style="width: 200px; height: 50px; font-size: 16px;">지도 3으로 이동</button></a>', unsafe_allow_html=True)
