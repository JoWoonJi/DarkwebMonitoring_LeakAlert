import requests
import pytz
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException
from requests.exceptions import RequestException
import time
import os
from dotenv import load_dotenv
import logging
load_dotenv()

# 로깅 설정
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


token = os.getenv('SLACK_TOKEN')
channel = os.getenv('SLACK_CHANNEL')
leakbase_file_path = os.getenv('LEAKBASE_FILE_PATH')
lockbit_file_path = os.getenv('LOCKBIT_FILE_PATH')

# Selenium을 사용하여 Chrome 웹 드라이버를 설정하고 반환
def open_driver():
    options = Options()
    service = Service(executable_path="C:\\Users\\HP\\Desktop\\HackerJobJo_Project\\darkweb\\chromedriver_win32\\chromedriver.exe")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-errors")
    options.add_argument("--proxy-server=socks5://127.0.0.1:9150")
    options.add_argument("--headless")  # Headless 모드 활성화

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(300)

    return driver


# URL 페이지를 가져와 파싱, 타임아웃 발생시 브라우저 종료하고 예외 발생
def fetch_and_parse_html(driver, url):
    try:
        driver.get(url)
        time.sleep(20)  
        return BeautifulSoup(driver.page_source, 'html.parser')
    except TimeoutException:
            print(f"타임아웃 에러 발생 URL: {url}. 다시 시도해주시길 바랍니다.")
            driver.quit()  
            raise TimeoutException(f"Failed to load {url}, browser closed.")


# slack alarm
def slack_alarm(post, site):
    if site == 'lockbit':
        text = f"🚨 Data Breach Alert from Lockbit 🚨\nTitle: {post['title']}\nDetails: {post['post_text']}\nUpload time: {post['upload time']}\n⏳ days: {post['days']}"
    elif site == 'leakbase':
        text = f"🚨 Data Breach Alert from Leakbase🚨\nTitle: {post['title']}\nUpload time: {post['upload time']}\nAuthor: {post['author']}\nURL: {post['url']}"
    else:
        print("Error")
    
    requests.post('https://slack.com/api/chat.postMessage', 
    headers = {"Authorization": "Bearer "+token},
    data={"channel":channel,"text":text})

# 파일 업데이트
def update_file(posts, site):
    crawled_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if site == 'leakbase':
        file_path = leakbase_file_path
    elif site == 'lockbit':
        file_path = lockbit_file_path
    with open(file_path,'w',encoding='utf-8') as file:
        json.dump(posts, file, ensure_ascii=False, indent=4)
        
        print(f'{file_path} updated.')


# 이전 게시글 데이터 불러오기
def load_previous_posts(site):
    # 파일 경로 설정
    if site == 'leakbase':
        file_path = os.getenv('LEAKBASE_FILE_PATH')
    elif site == 'lockbit':
        file_path = os.getenv('LOCKBIT_FILE_PATH')
    else:
        raise ValueError("Unknown site")

    # 파일 경로가 제대로 설정되지 않았을 경우 예외 처리
    if file_path is None:
        raise ValueError(f"Environment variable for {site} file path is not set")

    print(f'site: {site}')
    print(f'file path: {file_path}')

    # 파일이 존재하지 않을 경우 빈 JSON 배열로 초기화된 파일 생성
    if not os.path.isfile(file_path):
        with open(file_path, 'w') as file:
            json.dump([], file)
            print(f"{file_path} was created because it didn't exist.")
    
    # 파일이 존재하는 경우, 파일을 열어 이전 게시글 데이터 로드
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            previous_posts = json.load(file)
    except json.JSONDecodeError:
        # 파일이 비어있거나 JSON 형식이 아닐 경우 빈 리스트 반환
        previous_posts = []

    return previous_posts


# 새로운 게시글 확인 및 처리
def check_posts(new_posts, site):
    previous_posts = load_previous_posts(site)
    if not previous_posts:
        for post in new_posts:
            slack_alarm(post, site)
        update_file(new_posts, site)
        return
    
    if site == 'leakbase':
        previous_urls = set(post['url'] for post in previous_posts)
        new_posts_found = [post for post in new_posts if post['url'] not in previous_urls]
    elif site == 'lockbit':
        previous_urls = set(post['title'] for post in previous_posts)
        new_posts_found = [post for post in new_posts if post['title'] not in previous_urls]
    else:
        print('Error')
        

    if new_posts_found:
        for post in reversed(new_posts_found): # 슬랙 알림 과거-최신순으로 보내도록
            slack_alarm(post, site)
        updated_posts = new_posts_found + previous_posts
        update_file(updated_posts, site)
    else:
        update_file(previous_posts, site)

leakbase_posts=[]
# leakbase
def fetch_leakbase_data():
    global leakbase_posts  # 전역 변수 사용 선언
    site = 'leakbase'
    leakbase_url = 'https://leakbase.io/'
    posts = []  # 이번에 가져온 게시글을 저장할 로컬 변수

    try:
        response = requests.get(leakbase_url)
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')

        # 게시글 정보 추출
        post_elements = soup.select('div._xgtIstatistik-satir--konu')
        time_elements = soup.select('time.structItem-latestDate')
        forum_elements = [a['title'] for a in soup.select('._xgtIstatistik-satir--hucre._xgtIstatistik-satir--forum a[title]')]

        for post_element, time_element, forum in zip(post_elements, time_elements, forum_elements):
            author = post_element.get('data-author', 'no author')
            title_tag = post_element.find('a', attrs={'data-preview-url': True})
            datetime_str = time_element.get('datetime', 'no time info')
            utc_datetime = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S%z')
            korea_datetime_str = utc_datetime.astimezone(pytz.timezone('Asia/Seoul')).strftime("%Y-%m-%d %H:%M:%S")

            if title_tag:
                full_url = urljoin(leakbase_url, title_tag['href'])
                title = title_tag.get_text().strip()
                post_data = {
                    'title': title,
                    'upload_time': korea_datetime_str,
                    'author': author,
                    'url': full_url
                }
                posts.append(post_data)

        leakbase_posts = posts  # 전역 변수 업데이트
        logger.info(f"Leakbase data fetched: {leakbase_posts}")  # 로그 출력
        return leakbase_posts

    except RequestException as e:
        print(f'Request to {leakbase_url} failed: {e}')

lockbit_posts=[]
# lockbit
def fetch_lockbit_data():
    global lockbit_posts  # 전역 변수 사용 선언
    site = 'lockbit'
    driver = open_driver()
    URL = "http://lockbit7ouvrsdgtojeoj5hvu6bljqtghitekwpdy3b6y62ixtsu5jqd.onion"
    posts = []  # 이번에 가져온 게시글을 저장할 로컬 변수

    try:
        soup = fetch_and_parse_html(driver, URL)

        post_container = soup.find('div', class_='post-big-list')
        if post_container:
            post_blocks = post_container.find_all('a', class_='post-block')

            for post in post_blocks:
                title = post.find('div', class_='post-title').text.strip()
                post_text = post.find('div', class_='post-block-text').text.strip()
                updated_date = post.find('div', class_='updated-post-date').text.strip()
                days_element = post.find('span', class_='days')
                days = days_element.text.strip() if days_element else 'published'

                post_data = {
                    'title': title,
                    'post_text': post_text,
                    'upload_time': updated_date,
                    'days': days,
                }
                posts.append(post_data)

        lockbit_posts = posts  # 전역 변수 업데이트
        logger.info(f"Lockbit data fetched: {lockbit_posts}")  # 로그 출력
        return lockbit_posts

    finally:
        driver.quit()

if __name__ == '__main__':
    fetch_leakbase_data()
    fetch_lockbit_data()
    print('Process Finished')
    
