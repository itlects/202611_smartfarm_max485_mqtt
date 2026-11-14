# 스마트팜 RS-485 + MQTT

ESP32 DevKit V3 1개 → RS-485 → Arduino UNO 2개. 노트북 Mosquitto / Python 3.13 / MySQL Community 8.0.46.

- [부품과 배선](docs/WIRING.md)
- [Windows 설치와 실행](docs/RUN_WINDOWS.md)
- [프로토콜 및 검증](docs/VALIDATION.md)

학생 계정: smartfarm2026 / smartfarm1234 (.env에서 설정)
웹: http://localhost:8000 또는 http://노트북IPv4:8000
앱: 별도 APK가 아닌 모바일 반응형 웹앱. 같은 Wi-Fi에서 휴대전화로 위 주소 접속.

센서 사진을 이번 요청에서 확인할 수 없어 아날로그 AO형으로 임시 설계했습니다. RS-485 센서면 별도 전원/주소/명령 구현이 필요합니다.
실물 시험 전 참조 구현입니다. 무인 운영 전에 배선과 정지 기능을 직접 검증하세요.

## 공식 참고

- MAX3485 3.3V: https://www.analog.com/en/products/max3485.html
- MAX485 5V: https://www.analog.com/en/products/max485.html
- ESP32 UART: https://docs.espressif.com/projects/arduino-esp32/en/latest/api/serial.html
- MQTT 브로커: https://mosquitto.org/man/mosquitto-conf-5.html
- Paho Python: https://eclipse.dev/paho/files/paho.mqtt.python/html/
- MySQL: https://dev.mysql.com/doc/refman/8.0/en/
