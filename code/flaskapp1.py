from flask import Flask, render_template
from flask_apscheduler import APScheduler
from f_crawler import fetch_leakbase_data, fetch_lockbit_data
import logging
app = Flask(__name__)

app.logger.setLevel(logging.INFO)

app = Flask(__name__)
scheduler = APScheduler()

# 전역 변수로 데이터를 저장
leakbase_posts = []
lockbit_posts = []

def fetch_data():
    global leakbase_posts, lockbit_posts
    # 함수를 호출하여 데이터를 가져옵니다. 반환된 데이터를 전역 변수에 저장합니다.
    leakbase_posts = fetch_leakbase_data()
    lockbit_posts = fetch_lockbit_data()
    # 로그를 출력합니다.
    app.logger.info("Leakbase posts fetched: {}".format(len(leakbase_posts)))
    app.logger.info("Lockbit posts fetched: {}".format(len(lockbit_posts)))
    app.logger.info("Data updated.")

# 스케줄러에 작업 추가
scheduler.add_job(id='Scheduled Task', func=fetch_data, trigger='interval', minutes=60)  # 매 60분마다 실행
scheduler.init_app(app)
scheduler.start()

@app.route('/')
def home():
    # 전역 변수에서 직접 데이터를 가져와 템플릿에 전달합니다.
    app.logger.info(f"Rendering template with Leakbase data: {leakbase_posts}")
    app.logger.info(f"Rendering template with Lockbit data: {lockbit_posts}")
    return render_template('index1.html', leakbase_posts=leakbase_posts, lockbit_posts=lockbit_posts)

if __name__ == "__main__":
    fetch_data()  # 데이터를 직접 로드
    app.run(debug=True)
