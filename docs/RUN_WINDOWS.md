# Windows 10/11 설치와 실행

## 1. 소스 및 Python

Python 3.13, Git, MySQL Community Server 8.0.46, Workbench 8, Mosquitto를 설치합니다.
PowerShell:

```powershell
git clone https://github.com/itlects/202611_smartfarm_max485_mqtt.git
cd 202611_smartfarm_max485_mqtt
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

출력 키를 .env의 SECRET_KEY에 입력합니다. 학생 계정은 smartfarm2026 / smartfarm1234입니다.
.env는 커밋하지 않습니다.

## 2. MySQL

Workbench에서 관리자 계정으로 schema.sql을 실행합니다. SQL의 새 DB 사용자 암호와 .env DB_PASSWORD를 일치시킵니다.
기존 smartfarm 사용자가 있다면 CREATE USER IF NOT EXISTS는 암호를 바꾸지 않으므로 관리자가 ALTER USER로 수정하세요.
서비스는 root 대신 전용 DB 계정을 사용합니다. MySQL은 노트북 로컬에서만 접근합니다.

## 3. MQTT 브로커

프로젝트 루트에서:

```powershell
& 'C:\Program Files\mosquitto\mosquitto_passwd.exe' -c broker\passwords farmserver
& 'C:\Program Files\mosquitto\mosquitto_passwd.exe' broker\passwords farmgateway
& 'C:\Program Files\mosquitto\mosquitto.exe' -c broker\mosquitto.conf -v
```

비밀번호는 프롬프트에서 입력합니다. farmserver 암호는 .env MQTT_PASSWORD에, farmgateway 암호는 ESP32 secrets.h에 입력합니다.
Mosquitto 창을 실행 상태로 유지하세요. 기존 서비스가 1883을 사용하면 해당 서비스를 중지하거나 포트를 일치시켜 변경합니다.
학생 로그인 계정과 MQTT 계정은 서로 다릅니다.

## 4. 펌웨어

Arduino IDE 보드 매니저: Arduino AVR Boards, esp32 by Espressif Systems.
라이브러리 매니저: PubSubClient, ArduinoJson 7.x.

1. uno_node.ino의 NODE_ID=1로 UNO1에 업로드합니다.
2. NODE_ID=2로 바꿔 UNO2에 업로드합니다.
3. ESP32 폴더의 secrets.example.h를 secrets.h로 복사하고 Wi-Fi, 노트북 IPv4, MQTT 암호를 입력합니다.
4. 실제 ESP32에 맞는 보드를 선택하여 esp32_gateway.ino를 업로드합니다.
5. NTP 시간 동기화가 되어야 원격 명령이 허용됩니다. 인터넷 NTP 차단 시 학교 로컬 NTP로 configTime 서버를 바꿉니다.

## 5. 서버와 학생 접속

새 PowerShell 창에서 프로젝트 루트:

```powershell
.\.venv\Scripts\python.exe app.py
```

노트북 http://localhost:8000, 학생 `http://노트북IPv4:8000`.
ipconfig에서 Wi-Fi IPv4를 확인합니다. 학생 휴대전화도 같은 주소를 사용합니다(모바일 웹앱, APK 없음).
Windows 방화벽 개인 네트워크에 TCP 8000(웹), 1883(ESP32 MQTT)을 허용합니다. MySQL 3306은 학생에게 열지 않습니다.
Wi-Fi 클라이언트 격리가 켜져 있으면 접속되지 않습니다. 절전 해제, 노트북 DHCP 예약을 권장합니다.
공유 학생 계정이므로 조작자를 구분하지 못하며 수업 중 조작 순서를 정해야 합니다.
현재 로컬 수업용 HTTP/MQTT 구성입니다. 인터넷 공개 배포는 HTTPS/MQTT TLS 및 개별 인증 구성이 추가로 필요합니다.
저장소에 소스를 올리는 것만으로 서비스가 실행되거나 인터넷 접속 URL이 생성되지는 않습니다.

## 6. 실습 확인

1. 로그인 → MQTT 연결 → 두 노드 온라인을 확인합니다.
2. ADC 원시값 변화와 LED 전환을 확인합니다. confirmed는 실제 노드 출력 상태 응답입니다.
3. 펌프 대신 LED로 D6 출력을 시험합니다.
4. 실제 펌프는 5초 이내 정지, ESP32 전원 분리 시 3초 이내 정지를 시험합니다.
5. MySQL telemetry와 최근 저장 기록을 확인합니다.
6. 건조/젖음 ADC 교정 전에는 원시값을 수분 %로 표시하지 않습니다.
