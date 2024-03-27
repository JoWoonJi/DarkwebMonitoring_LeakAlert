import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

from bs4 import BeautifulSoup

def open_driver():
    options = Options()
    service = Service(executable_path="C:\\Users\\faton\\Downloads\\chromedriver-win64\\chromedriver.exe")  # chromedriver 실행 파일의 경로를 지정하세요.

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

    try:
        # 원하는 웹 페이지로 이동합니다.
        driver.get("http://omegalock5zxwbhswbisc42o2q2i54vdulyvtqqbudqousisjgc7j7yd.onion")

        # 무한루프로 브라우저를 열어둡니다.
        while True:
            time.sleep(60)  # 60초마다 브라우저가 열려있도록 유지합니다.
            
            # 현재 페이지의 HTML을 가져옵니다.
            html = driver.page_source

            # BeautifulSoup을 사용하여 HTML 파싱
            soup = BeautifulSoup(html, 'html.parser')

            # 원하는 테이블을 찾습니다.
            table = soup.find("table", {"class": "datatable center"})  # 해당 테이블의 클래스 이름을 지정하세요.

            if table:
                # 테이블 데이터를 추출합니다.
                headers, data = extract_data_from_html(table)

                # CSV 파일로 저장
                output_file = 'Omega.csv'
                save_data_to_csv(headers, data, output_file)

    except KeyboardInterrupt:
        # 사용자가 Ctrl+C 키를 누르면 스크립트를 종료합니다.
        pass
    finally:
        driver.quit()

def extract_data_from_html(table):
    # 테이블 헤더를 추출
    headers = [header.get_text(strip=True) for header in table.find_all('th')]

    # 테이블 데이터를 추출
    data = []
    for row in table.find_all('tr', class_='trow'):
        row_data = [data.get_text(strip=True) for data in row.find_all('td')]
        data.append(row_data)

    return headers, data

def save_data_to_csv(headers, data, output_file):
    with open(output_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(data)

if __name__ == '__main__':
    main()