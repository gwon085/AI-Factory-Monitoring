#include <DHT.h>

#define DHTPIN 4
#define DHTTYPE DHT11

// RGB LED 핀
#define RED_PIN   23
#define GREEN_PIN 22
#define BLUE_PIN  21

DHT dht(DHTPIN, DHTTYPE);

// blink 제어용
unsigned long prevMillis = 0;
bool ledState = false;
bool blinkEnable = false;
bool isResetMode = false;  // RESET 모드 플래그

void setup() {
  Serial.begin(115200);
  dht.begin();

  pinMode(RED_PIN, OUTPUT);
  pinMode(GREEN_PIN, OUTPUT);
  pinMode(BLUE_PIN, OUTPUT);

  ledOff();
}

void loop() {
  // ===== 센서값 전송 =====
  float humi = dht.readHumidity();
  float temp = dht.readTemperature();

  if (!isnan(temp) && !isnan(humi)) {
    Serial.print(temp, 1);
    Serial.print(",");
    Serial.println(humi, 1);
  }

  // ===== PC 명령 수신 =====
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd == "OK") {
      blinkEnable = false;
      isResetMode = false;  // RESET 모드 해제
      setGreen();
    }
    else if (cmd == "NOK") {
      // RESET 모드일 때는 NOK 명령 무시
      if (!isResetMode) {
        blinkEnable = true;   // 빨강 blink
      }
    }
    else if (cmd == "RESET") {
      blinkEnable = false;
      isResetMode = true;   // RESET 모드 활성화
      setRed();             // 빨간색 고정
    }
  }

  // ===== NOK일 때 빨강 blink (RESET 모드가 아닐 때만) =====
  if (blinkEnable && !isResetMode) {
    unsigned long now = millis();
    if (now - prevMillis >= 500) {
      prevMillis = now;
      ledState = !ledState;
      digitalWrite(RED_PIN, ledState);
      digitalWrite(GREEN_PIN, LOW);
      digitalWrite(BLUE_PIN, LOW);
    }
  }

  delay(1000);
}

// ===== LED 제어 함수 =====
void ledOff() {
  digitalWrite(RED_PIN, LOW);
  digitalWrite(GREEN_PIN, LOW);
  digitalWrite(BLUE_PIN, LOW);
}

void setGreen() {
  digitalWrite(RED_PIN, LOW);
  digitalWrite(GREEN_PIN, HIGH);
  digitalWrite(BLUE_PIN, LOW);
}

void setRed() {
  digitalWrite(RED_PIN, HIGH);
  digitalWrite(GREEN_PIN, LOW);
  digitalWrite(BLUE_PIN, LOW);
}
