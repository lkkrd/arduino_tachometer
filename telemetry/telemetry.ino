#include <Servo.h>

// ----------------- KONFIGURACJA -----------------
const int low_rpm_pin = 3;
const int high_rpm_pin = 5;
const int blue_pin = 6;

const int low_rpm = 10000;
const int mid_rpm = 16000;
const int high_rpm = 17550;

const float min_g_acc = -3.6;
const float max_g_acc = 2;
const float min_g_turn = -3.7;
const float max_g_turn = 3.7;

int blinker = 0;
int blinker_speed = 20;

// Struktura telemetryczna
struct Telemetry {
  float rpm;
  float acc_brake_g_force;
  float left_right_g_force;
};

Telemetry t;
Servo servo_l;

// ----------------- SETUP -----------------
void setup() {
  Serial.begin(9600);
  pinMode(low_rpm_pin, OUTPUT);
  pinMode(high_rpm_pin, OUTPUT);
  pinMode(blue_pin, OUTPUT);
  servo_l.attach(9);
  
}

// ----------------- LOOP -----------------
void loop() {
  // Resetujemy niebieską diodę
  analogWrite(blue_pin, 0);

  // Odczyt z Serial
  String msg = readSerial();
  if (msg.length() > 0) {
    t = parseTelemetry(msg);
  }

  float rpm = t.rpm;
  Serial.println(rpm);  // debug RPM

  // ----------------- LOGIKA LED -----------------
  if (rpm < low_rpm) {
    analogWrite(low_rpm_pin, 255);
    analogWrite(high_rpm_pin, 0);
  } 
  else if (rpm >= low_rpm && rpm < mid_rpm) {
    int val = map(rpm, low_rpm, mid_rpm, 0, 255);
    analogWrite(high_rpm_pin, val);
    analogWrite(low_rpm_pin, 255 - val);
  } 
  else if (rpm >= mid_rpm && rpm < high_rpm) {
    analogWrite(low_rpm_pin, 0);
    analogWrite(high_rpm_pin, 255);
  } 
  else {
    blink();
  }
 
  // LOGIKA SERVO
  float g_acc = t.acc_brake_g_force;
  float g_turn = t.left_right_g_force;
  float pos = map(g_turn, min_g_acc, max_g_acc, 0, 180);
  servo_l.write(pos);


  // ----------------- UPDATE BLINK -----------------
  blinker++;
  if (blinker > blinker_speed) {
    blinker = 0;
  }

  delay(10); // mała pauza dla stabilności Serial
}

// ----------------- FUNKCJE -----------------

// Funkcja migania LED (niebieska + wysokie RPM)
void blink() {
  if (blinker > blinker_speed / 2) {
    analogWrite(blue_pin, 150);
    analogWrite(high_rpm_pin, 150);
  } else {
    analogWrite(high_rpm_pin, 0);
    analogWrite(blue_pin, 0);
  }
}

// Funkcja odczytu całego stringa z Serial
String readSerial() {
  static String msg_local = "";
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n') {
      String result = msg_local;
      msg_local = "";
      result.trim();  // usuwa \r, \n, spacje
      return result;
    } else {
      msg_local += c;
    }
  }
  return ""; // jeśli brak pełnego stringa
}

// Funkcja parsująca string "2500;0.0;-0.1" do struktury Telemetry
Telemetry parseTelemetry(String msg) {
  Telemetry t;
  float values[3];    
  int startIndex = 0;
  int endIndex;
  int i = 0;

  while (i < 3) {
    endIndex = msg.indexOf(';', startIndex);
    if (endIndex == -1) {   // ostatni element
      endIndex = msg.length();
    }
    
    String part = msg.substring(startIndex, endIndex);
    values[i] = part.toFloat();  // konwersja na float
    startIndex = endIndex + 1;
    i++;
  }

  t.rpm = values[0];
  t.acc_brake_g_force = values[1];
  t.left_right_g_force = values[2];

  return t;
}
