import requests
import csv
import folium
import streamlit as st
from streamlit_folium import st_folium
from folium import plugins
from datetime import datetime, timedelta
import pandas as pd

st.set_page_config(page_title="자전거123", page_icon='burgundy-bicycle.png')

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


st.header("부산광역시 자전거 위치정보")

# 버튼 추가
option = st.radio("보기 옵션을 선택하세요", ('자전거 대여소', '도시공원', '자전거 보관소','종합 병원'))

# 선택에 따라 아이콘 타입 및 팝업 설정
if option == '자전거 대여소':
    selected_data = bike_rental_data
    icon_type = {'icon': 'bicycle', 'color': 'blue'}
    show_name = True
elif option == '도시공원':
    selected_data = park_data
    icon_type = {'icon': 'tree', 'color': 'green'}
    show_name = True
# 병원 추가
elif option == '종합 병원':  
    selected_data = hospital_data  # 병원 데이터를 사용
    icon_type = {'icon': 'hospital', 'color': 'purple'}  # 병원 아이콘 설정
    show_name = True
else:  # 자전거 보관소
    selected_data = bike_storage_data
    icon_type = {'icon': 'lock', 'color': 'red'}
    show_name = False


# 부산대 위치로 지도의 중심
map = folium.Map(location=[35.23164602460444, 129.0838577311402], zoom_start=12)
plugins.LocateControl().add_to(map)

for place in selected_data:
    location = [place['latitude'], place['longitude']]

    # Kakao Map directions URL with destination coordinates
    kakao_directions_url = (f"https://map.kakao.com/link/to/{place['address']},"
                            f"{place['latitude']},{place['longitude']}")

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

# 지도 생성 및 표시
st_folium(map, height=700, width=1000)


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
