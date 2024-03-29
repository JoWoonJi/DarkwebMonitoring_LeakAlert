from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import requests
import time

# 슬랙 웹훅 함수
def send_slack_message(webhook_url, message):
    payload = {'text': message}
    response = requests.post(webhook_url, json=payload)
    return response.ok

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
    webhook_url = 'YOUR_SLACK_WEBHOOK_URL'
    url = 'https://gall.dcinside.com/mini/board/lists/?id=dataprocessing'
    driver = webdriver.Chrome()  # Chrome WebDriver 인스턴스 생성

    try:
        while True:
            new_posts = crawl_website(driver, url)
            if new_posts:
                for title, link in new_posts[:5]:  # 최근 5개의 새 게시글만 슬랙으로 전송
                    message = f'새 글: {title}\n링크: {link}'
                    send_slack_message(webhook_url, message)
                    time.sleep(1)  # 슬랙 메시지 전송 간격을 1초로 설정
            else:
                print('새 글이 없습니다.')

            time.sleep(60 * 10)  # 10분마다 사이트를 다시 체크
    finally:
        driver.quit()
