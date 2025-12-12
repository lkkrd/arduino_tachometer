String msg = "";
int rpm = 0;
int blinker = 0;
int blinker_speed = 20;

const int low_rpm_pin = 3;
const int high_rpm_pin = 5;
const int blue_pin = 6;

void setup() {
  Serial.begin(9600);

  pinMode(low_rpm_pin, OUTPUT);
  pinMode(high_rpm_pin, OUTPUT);
}

void loop() {

  // Odczyt danych z bufora
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == ';') {
      rpm = msg.toInt();   // dopiero tutaj aktualizujemy RPM
      msg = "";            // reset bufora
    } else {
      msg += c;
    }
  }

  analogWrite(blue_pin, 0);

  // Logika LED
  if (rpm < 10000) {
    analogWrite(low_rpm_pin, 255);
    analogWrite(high_rpm_pin, 0);
  } else if (rpm > 10000 & rpm < 16000) {
    int val = map(rpm, 10000, 16000, 0, 255);
    analogWrite(high_rpm_pin, val);
    analogWrite(low_rpm_pin, 255 - val);
  } else if (rpm > 16000 & rpm < 17700) {
    analogWrite(low_rpm_pin, 0);
    analogWrite(high_rpm_pin, 255);
  } else {
    blink();
  }



  blinker++;
  if (blinker > blinker_speed) {
    blinker = 0;
  }
  delay(10);
}

void blink() {
  if (blinker > blinker_speed / 2) {
    analogWrite(blue_pin, 150);
    analogWrite(high_rpm_pin, 150);
  } else {
    analogWrite(high_rpm_pin, 0);
    analogWrite(blue_pin, 0);
  }

}
