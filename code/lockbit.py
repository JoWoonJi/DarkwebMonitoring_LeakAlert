from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains

from bs4 import BeautifulSoup
import os
import time

sent_post_titles = set()

def open_driver():
    options = Options()
    service = Service(executable_path="C:\\Users\\faton\\Downloads\\chromedriver-win64\\chromedriver.exe")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-errors")
    options.add_argument("--proxy-server=socks5://127.0.0.1:9150")

    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(10)
    driver.set_script_timeout(10)
    driver.maximize_window()

    return driver

def main():
    driver = open_driver()
    action = ActionChains(driver)

    try:
        driver.get("http://lockbit7ouvrsdgtojeoj5hvu6bljqtghitekwpdy3b6y62ixtsu5jqd.onion")

        time.sleep(15)

        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        # lambda,  post-block bad, good ,post-block 클래스를 가지고 있는 부분을 찾습니다.
        block = soup.find_all("a", attrs = {"class": lambda L: L and L.startswith("post-block")})

        post_number = 1

        for post in block:
            post_title = post.find("div", {"class": "post-title"}).text.strip()#게시물 요소에서 제목을 추출

            print(post_title)

            target = driver.find_element(By.XPATH, f"/html/body/div[3]/div[1]/div/a[{post_number}]")
            action.move_to_element(target).perform()# 마우스를 해당 요소로 이동시킵니다.
            target.screenshot(f'C:\\Users\\faton\\Downloads\\capture\\{post_title}.png')# 스크린샷을 찍어서 해당 경로에 저장합니다.
            
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")#페이지를 스크롤하여 다음 게시물을 로드합니다.

            post_number += 1

        """
        block = soup.find_all("div", attrs = {"class": "post-block bad", "onclick": True})

        for post in block:
            post_timer = post.find("div", {"class": "post-timer"}).text.strip
        """ 
    finally:
        driver.quit()

if __name__ == '__main__':
    directory = 'C:\\Users\\faton\\Downloads\\capture'

    # 디렉토리가 존재하지 않으면 생성
    if not os.path.exists(directory):
        os.makedirs(directory)
    main()
    print("basecode complete")