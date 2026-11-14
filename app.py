"""Single-process classroom server. Start with python app.py, not flask debug reload."""
import json
import logging
import os
import secrets
import threading
import time
import uuid
from datetime import datetime, timezone

import pymysql
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Strict')
password_hash = generate_password_hash(os.getenv('STUDENT_PASSWORD', 'smartfarm1234'))
lock = threading.Lock()
nodes = {}
pending = {}
client = None


def db():
    return pymysql.connect(host=os.getenv('DB_HOST', '127.0.0.1'),
        port=int(os.getenv('DB_PORT', '3306')), user=os.getenv('DB_USER', 'smartfarm'),
        password=os.environ['DB_PASSWORD'], database=os.getenv('DB_NAME', 'smartfarm'),
        charset='utf8mb4', autocommit=True, connect_timeout=2, read_timeout=2, write_timeout=2)


def on_connect(c, userdata, flags, reason_code, properties):
    if reason_code == 0:
        c.subscribe('smartfarm/v1/+/telemetry', qos=1)


def on_message(c, userdata, msg):
    try:
        node = int(msg.topic.split('/')[2])
        data = json.loads(msg.payload)
        if node not in (1, 2) or not isinstance(data, dict):
            return
        raw = int(data['raw'])
        pump = int(data['pump'])
        led = int(data['led'])
        if not 0 <= raw <= 1023 or pump not in (0, 1) or not 0 <= led <= 3:
            return
        now = time.time()
        with lock:
            nodes[node] = dict(raw=raw, pump=bool(pump), led=led, received=now)
            job = pending.get(node)
            if job and data.get('id') == job['id']:
                job['status'] = 'confirmed' if pump == job['pump'] and led == job['led'] else 'mismatch'
        try:
            with db() as conn, conn.cursor() as cur:
                cur.execute('INSERT INTO telemetry(node_id,raw,pump,led) VALUES(%s,%s,%s,%s)',
                            (node, raw, pump, led))
        except Exception:
            logging.exception('Telemetry database write failed; live state still available')
    except (ValueError, KeyError, TypeError, IndexError, UnicodeDecodeError):
        logging.warning('Ignored malformed telemetry')


@app.before_request
def protect():
    if request.path.startswith('/api/') and request.path != '/api/login':
        if not session.get('user'):
            return jsonify(error='로그인이 필요합니다'), 401
        if request.method != 'GET' and not secrets.compare_digest(request.headers.get('X-CSRF-Token', ''), session.get('csrf', '')):
            return jsonify(error='잘못된 요청 토큰'), 403


@app.get('/')
def index():
    return render_template('index.html')


@app.post('/api/login')
def login():
    data = request.get_json(silent=True) or {}
    if data.get('username') != os.getenv('STUDENT_USER', 'smartfarm2026') or not check_password_hash(password_hash, str(data.get('password', ''))):
        return jsonify(error='아이디 또는 비밀번호를 확인하세요'), 401
    session.clear()
    session.update(user=data['username'], csrf=secrets.token_hex(24))
    return jsonify(csrf=session['csrf'])


@app.post('/api/logout')
def logout():
    session.clear()
    return jsonify(ok=True)


@app.get('/api/state')
def state():
    with lock:
        result = {n: dict(v, online=time.time()-v['received'] < 8) for n,v in nodes.items()}
        jobs = {n: dict(v, status=('timeout' if v['status']=='pending' and time.time()-v['sent']>8 else v['status'])) for n,v in pending.items()}
    return jsonify(nodes=result, commands=jobs, mqtt=bool(client and client.is_connected()))


@app.post('/api/command')
def command():
    data = request.get_json(silent=True) or {}
    node, pump, led = data.get('node'), data.get('pump'), data.get('led')
    if type(node) is not int or node not in (1,2) or type(pump) is not int or pump not in (0,1) or type(led) is not int or led not in range(4):
        return jsonify(error='node=1/2, pump=0/1, led=0..3 정수가 필요합니다'), 400
    with lock:
        info = nodes.get(node)
        if pump and (not info or time.time()-info['received'] > 8):
            return jsonify(error='오프라인 노드의 펌프를 켤 수 없습니다'), 409
    if not client or not client.is_connected():
        return jsonify(error='MQTT 연결 없음'), 503
    job = dict(id=uuid.uuid4().hex[:12], pump=pump, led=led, sent=time.time(), status='pending')
    payload = dict(id=job['id'], pump=pump, led=led, expires=int(time.time())+5)
    with lock:
        pending[node] = job
    result = client.publish(f'smartfarm/v1/{node}/command', json.dumps(payload), qos=1, retain=False)
    if result.rc != mqtt.MQTT_ERR_SUCCESS:
        return jsonify(error='전송 실패'), 503
    return jsonify(id=job['id'], status='pending'), 202


@app.get('/api/history')
def history():
    try:
        with db() as conn, conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute('SELECT node_id,raw,pump,led,created_at FROM telemetry ORDER BY id DESC LIMIT 100')
            rows=cur.fetchall()
        return jsonify(rows=rows)
    except Exception:
        return jsonify(error='DB 연결 또는 테이블을 확인하세요'), 503


def start_mqtt():
    global client
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id='smartfarm-server-'+secrets.token_hex(4))
    client.username_pw_set(os.environ['MQTT_USER'], os.environ['MQTT_PASSWORD'])
    client.on_connect, client.on_message = on_connect, on_message
    client.reconnect_delay_set(1, 10)
    client.connect_async(os.getenv('MQTT_HOST','127.0.0.1'), int(os.getenv('MQTT_PORT','1883')), 20)
    client.loop_start()


if __name__ == '__main__':
    from waitress import serve
    logging.basicConfig(level=logging.INFO)
    start_mqtt()
    serve(app, host='0.0.0.0', port=8000, threads=4)
