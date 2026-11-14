# 검증 및 프로토콜

Python 3.13.5에서 requirements 설치 및 unittest 4개 통과: 미인증 차단, 로그인, CSRF/입력 검증, 오프라인 급수 거부, 비retain 명령 및 모의 확인응답 처리.
DB 쓰기 실패를 의도적으로 모의한 테스트에서도 실시간 상태가 유지되는지 확인했습니다.
실제 MySQL 8.0.46, Mosquitto, Windows, Arduino 컴파일과 실물 전기 회로는 이 환경에서 검증하지 않았습니다.
GitHub Actions에 Python 3.13 검사를 추가했습니다. 실행 결과는 Actions에서 확인하세요.

## RS-485

Modbus가 아닌 자체 ASCII 프로토콜 + CRC16/Modbus 체크섬입니다.
9600 baud 8N1, 단일 마스터, 노드1/2 교대 500ms 요청, 노드별 약 1초 갱신, 응답 대기 180ms.

| 본문 예 | 의미 |
|---|---|
| Q,1 | 노드1 상태 요청 |
| C,1,012345abcdef,1,3 | ID, 펌프0/1, LED 비트마스크0~3 |
| S,1,012345abcdef,650,1,3 | 마지막 ID, ADC, 펌프, LED 응답 |

프레임은 `본문*CRC4자리16진수\n`. CRC는 초기 0xFFFF, 다항식 0xA001, 본문만 계산.
UNO는 요청 시에만 응답합니다. 동일 ID 재전송으로 타이머가 다시 시작되지 않습니다.
펌프는 리셋 OFF, 최대 5초, RS-485 요청 단절 3초에 OFF입니다.
MQTT 연결만 끊겼을 때 즉시 정지하지는 않으며 최대 5초 제한이 적용됩니다.

## MQTT

- `smartfarm/v1/{1 또는 2}/telemetry`: ESP32→서버, JSON id/raw/pump/led, QoS0, retain=false.
- `smartfarm/v1/{1 또는 2}/command`: 서버→ESP32, JSON id/pump/led/expires, QoS1, retain=false.
- expires는 서버 기준 현재+5초, ESP32가 시간 동기화 후 만료 검증.
- 웹 상태: pending → 노드 응답값과 ID 일치 시 confirmed, 다르면 mismatch, 8초 후 timeout.
- 8초 이상 상태 수신이 없으면 offline. confirmed는 물 흐름 확인이 아니라 UNO 출력 확인입니다.

현재 수동 급수·LED 제어, 버튼·부저, ADC 저장을 제공합니다. 자동 임계값 급수, 네이티브 APK, 푸시 알림, 사용자별 이력은 포함하지 않습니다.
