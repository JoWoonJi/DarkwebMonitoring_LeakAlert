import requests
import pytz
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.common.exceptions import TimeoutException
from requests.exceptions import RequestException
import time
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv('SLACK_TOKEN')
channel = os.getenv('SLACK_CHANNEL')
leakbase_file_path = os.getenv('LEAKBASE_FILE_PATH')
lockbit_file_path = os.getenv('LOCKBIT_FILE_PATH')

def open_driver():
    # Tor 실행 파일과 프로필 경로 설정
    tor_binary_path = 'C:\\Users\\HP\\Desktop\\Tor Browser\\Browser\\firefox.exe'
    tor_profile_path = 'C:\\Users\\HP\\Desktop\\Tor Browser\\Browser\\TorBrowser\\Data\\Browser\\profile.default'

    # FirefoxOptions 객체 생성 및 바이너리 위치 설정
    firefox_options = FirefoxOptions()
    firefox_options.binary_location = tor_binary_path
    # 프로필 경로 설정
    firefox_options.add_argument(f"-profile {tor_profile_path}")
    
    # Firefox 드라이버 생성 및 옵션 전달
    driver = webdriver.Firefox(options=firefox_options)
    driver.set_page_load_timeout(300)
    return driver

def fetch_and_parse_html(driver, url):
    try:
        driver.get(url)
        time.sleep(20)
        return BeautifulSoup(driver.page_source, 'html.parser')
    except TimeoutException:
        print(f"타임아웃 에러 발생 URL: {url}. 다시 시도해주시길 바랍니다.")
        driver.quit()
        raise

def slack_alarm(post, site):
    if site == 'lockbit':
        text = f"🚨 Data Breach Alert from Lockbit 🚨\nTitle: {post['title']}\nDetails: {post['post_text']}\nUpload time: {post['upload time']}\n⏳ days: {post['days']}"
    elif site == 'leakbase':
        text = f"🚨 Data Breach Alert from Leakbase🚨\nTitle: {post['title']}\nUpload time: {post['upload time']}\nAuthor: {post['author']}\nURL: {post['url']}"
    else:
        print("Error")

    requests.post('https://slack.com/api/chat.postMessage', 
    headers={"Authorization": "Bearer " + token},
    data={"channel": channel, "text": text})

def update_file(posts, site):
    if site == 'leakbase':
        file_path = leakbase_file_path
    elif site == 'lockbit':
        file_path = lockbit_file_path

    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(posts, file, ensure_ascii=False, indent=4)
        print(f'{file_path} updated.')

def load_previous_posts(site):
    if site == 'leakbase':
        file_path = leakbase_file_path
    elif site == 'lockbit':
        file_path = lockbit_file_path
    else:
        raise ValueError("Unknown site")

    if file_path is None:
        raise ValueError(f"Environment variable for {site} file path is not set")

    if not os.path.isfile(file_path):
        with open(file_path, 'w') as file:
            json.dump([], file)
            print(f"{file_path} was created because it didn't exist.")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            previous_posts = json.load(file)
    except json.JSONDecodeError:
        previous_posts = []

    return previous_posts

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
        previous_titles = set(post['title'] for post in previous_posts)
        new_posts_found = [post for post in new_posts if post['title'] not in previous_titles]

    if new_posts_found:
        # 슬랙 알림을 과거-최신순으로 보냅니다.
        for post in reversed(new_posts_found):
            slack_alarm(post, site)
        # 업데이트된 포스트 리스트로 파일을 업데이트합니다.
        updated_posts = new_posts_found + previous_posts
        update_file(updated_posts, site)
    else:
        # 새로운 포스트가 없는 경우, 기존의 포스트를 유지합니다.
        update_file(previous_posts, site)

# leakbase
def fetch_leakbase_data():
    site = 'leakbase'
    leakbase_url = 'https://leakbase.io/'

    try:
        response = requests.get(leakbase_url)
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
    
        # 게시글 정보 추출
        post_elements = soup.select('div._xgtIstatistik-satir--konu')
        time_elements = soup.select('time.structItem-latestDate')
        forum_elements = [a['title'] for a in soup.select('._xgtIstatistik-satir--hucre._xgtIstatistik-satir--forum a[title]')]

        posts = []

        for post_element, time_element, forum in zip(post_elements, time_elements, forum_elements):
            # 작성자 정보
            author = post_element.get('data-author', 'no author')
            # url
            title_tag = post_element.find('a', attrs={'data-preview-url': True})            
            # 게시글 시간정보
            datetime_str = time_element.get('datetime', 'no time info')
            utc_datetime = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S%z')
            korea_datetime_str = utc_datetime.astimezone(pytz.timezone('Asia/Seoul')).strftime("%Y-%m-%d %H:%M:%S")
            time_text = time_element.get_text().strip()
        
            # 게시글 주소
            if title_tag:
                full_url = urljoin(leakbase_url, title_tag['href'])
                title = title_tag.get_text().strip()
                
                post_data = {
                    'title': title,
                    'upload time': korea_datetime_str,
                    'time_text': time_text,
                    'author': author,
                    'url': full_url
                }
                posts.append(post_data)
        
        # 새로운 게시글 확인 및 처리
        check_posts(posts, site)
    except RequestException as e:
        print(f'Request to {leakbase_url} failed: {e}')

# lockbit
def fetch_lockbit_data():
    site = 'lockbit'
    driver = open_driver()
    URL = "http://lockbit7ouvrsdgtojeoj5hvu6bljqtghitekwpdy3b6y62ixtsu5jqd.onion"
    soup = fetch_and_parse_html(driver, URL)

    posts = []

    post_container = soup.find('div', class_='post-big-list')
    if post_container:
        post_blocks = post_container.find_all('a', class_='post-block')

        for post in post_blocks:
            title = post.find('div', class_='post-title').text.strip()
            post_text = post.find('div', class_='post-block-text').text.strip()
            updated_date = post.find('div', class_='updated-post-date').text.strip()
            days_element = post.find('span', class_='days')
            if days_element:
                days = days_element.text.strip()
            else:
                days = 'published'
            
            post_data = {
                'title': title,
                'post_text': post_text,
                'upload time': updated_date,
                'days': days,
            }
            posts.append(post_data)

    check_posts(posts, site)
    driver.quit()

if __name__ == '__main__':
    fetch_leakbase_data()
    fetch_lockbit_data()
    print('Process Finished')
