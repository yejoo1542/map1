from setuptools import setup, find_packages

setup(
    name='your_project_name',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'streamlit==1.20.0',
        'folium==0.14.0',
        # 추가 의존성 명시
    ],
)
