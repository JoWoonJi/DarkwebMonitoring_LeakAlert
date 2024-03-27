from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import requests
import time

# 슬랙 API를 사용하여 사용자에게 DM 보내는 함수
def send_slack_dm(token, user_id, message):
    # 사용자에게 DM 채널 열기
    open_dm_response = requests.post('https://slack.com/api/conversations.open', headers={
        'Authorization': f'Bearer {token}'
    }, json={
        'users': user_id
    }).json()

    # DM 채널 ID 획득
    dm_channel_id = open_dm_response['channel']['id']

    # DM 채널에 메시지 보내기
    post_message_response = requests.post('https://slack.com/api/chat.postMessage', headers={
        'Authorization': f'Bearer {token}'
    }, json={
        'channel': dm_channel_id,
        'text': message
    }).json()

    return post_message_response.get('ok', False)

# Selenium을 사용한 크롤링 함수
def crawl_website(driver, url):
    driver.get(url)
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.gall_list tbody tr'))
        )
    except TimeoutException:
        print("페이지 로딩 시간 초과")
        return []

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    posts = soup.select('.gall_list tbody tr')

    new_posts = []
    for post in posts:
        if post.find('td', class_='gall_num') and post.find('td', class_='gall_num').text.isdigit():
            title = post.find('td', class_='gall_tit').text.strip()
            link = 'https://gall.dcinside.com' + post.find('a')['href']
            new_posts.append((title, link))

    return new_posts

if __name__ == '__main__':
    slack_token = 'xoxb-6828434958416-6803446648853-d0etf16rdCmbdgvT9KV3aRKf'
    slack_user_id = 'U06Q28XK6HF'
    url = 'https://gall.dcinside.com/mini/board/lists/?id=dataprocessing'
    
    # WebDriver 옵션 설정 (필요한 경우)
    options = webdriver.ChromeOptions()
    # 예: options.add_argument('--headless')

    # Chrome WebDriver 경로 지정 및 인스턴스 생성
    driver_path = 'C:\\Users\\HP\\Desktop\\HackerJobJo_Project\\darkweb\\chromedriver_win32\\chromedriver.exe'
    driver = webdriver.Chrome(executable_path=driver_path, options=options)

    try:
        while True:
            new_posts = crawl_website(driver, url)
            if new_posts:
                for title, link in new_posts[:5]:  # 최근 5개의 새 게시글만 슬랙으로 전송
                    message = f'새 글: {title}\n링크: {link}'
                    send_slack_dm(slack_token, slack_user_id, message)
                    time.sleep(1)  # 슬랙 메시지 전송 간격을 1초로 설정
            else:
                print('새 글이 없습니다.')

            time.sleep(60 * 10)  # 10분마다 사이트를 다시 체크
    finally:
        driver.quit()
