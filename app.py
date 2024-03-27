from flask import Flask, jsonify, request
from flask_cors import CORS
from crawler import get_data

app = Flask(__name__)
CORS(app)

@app.route('/api/update')  
def update_data():
    update_type = request.args.get('type', '')  
    if update_type == 'lockbit':
        return update_lockbit()
    elif update_type == 'blacksuit':
        return update_blacksuit()
    elif update_type == 'alphv':
        return update_alphv()
    elif update_type == 'leakbase':
        return update_leakbase()
    else:
        return jsonify(message="잘못된 업데이트 타입 요청", error="Invalid update type"), 400

def update_lockbit():
    response = get_data('lockbit')  
    if response["status"] == "success":
        return jsonify(message="LockBit 업데이트 요청 성공", data=response["data"])
    else:
        return jsonify(message="LockBit 업데이트 요청 실패", error=response.get("message")), 400

def update_blacksuit():
    response = get_data('blacksuit')  
    if response["status"] == "success":
        return jsonify(message="blackSuit 업데이트 요청 성공", data=response["data"])
    else:
        return jsonify(message="blackSuit 업데이트 요청 실패", error=response.get("message")), 400

def update_alphv():
    response = get_data('alphv')  
    if response["status"] == "success":
        return jsonify(message="ALPHV 업데이트 요청 성공", data=response["data"])
    else:
        return jsonify(message="ALPHV 업데이트 요청 실패", error=response.get("message")), 400

def update_leakbase():
    response = get_data('leakbase')  
    if response["status"] == "success":
        return jsonify(message="LeakBase 업데이트 요청 성공", data=response["data"])
    else:
        return jsonify(message="LeakBase 업데이트 요청 실패", error=response.get("message")), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8282, debug=True)