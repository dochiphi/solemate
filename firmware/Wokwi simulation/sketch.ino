/* =============================================================
   Solemate Smart Insole — Prototype Firmware
   -------------------------------------------------------------
   Author:  Ethan Do
   Platform: ESP32 (Wokwi simulation build)

   WHAT IT DOES
   Reads foot sensors and runs two functions:
     1. Fall detection  — impact above 2.5 g followed by 2 s of
        stillness triggers an alert. A stumble that keeps moving
        does not (false-alarm reject).
     2. Temperature asymmetry — a sustained gap above 2.0 C
        between the two feet flags possible foot inflammation.
     On a detected fall: buzz the motor, start a 30 s countdown,
     cancel on button press, else send a mock SOS.

   PIN MAP
     GPIO34  FSR pressure   (ADC1, 10k divider; pot in sim)
     GPIO4   DS18B20 data   (both temp sensors, 4.7k pull-up)
     GPIO21  MPU6050 SDA    (I2C)
     GPIO22  MPU6050 SCL    (I2C)
     GPIO5   Motor          (via transistor; LED in sim)
     GPIO18  Cancel button  (INPUT_PULLUP; app cancel on real device)

   SIM STAND-INS (hardware-only on the real build)
     Pressure  = potentiometer    -> real FSR
     Motor     = LED              -> coin motor + transistor + diode
     SOS send  = serial printout  -> Bluetooth to phone
     Timers compressed for testing (stillness 2 s, temp gap 10 s)

   LIBRARIES: OneWire, DallasTemperature, Adafruit_MPU6050,
              Adafruit_Sensor, Wire
   ============================================================= */

#include <OneWire.h>
#include <DallasTemperature.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>

#define ONE_WIRE_BUS 4
#define MOTOR_PIN   5      // LED stands in for the vibration motor
#define CANCEL_BTN  18

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature tempSensor(&oneWire);
Adafruit_MPU6050 mpu;

// --- fall detection ---
const float IMPACT_G    = 2.5;
const float STILL_LOW   = 0.8;
const float STILL_HIGH  = 1.2;
const unsigned long STILL_TIME   = 2000;
const unsigned long GIVE_UP_TIME = 15000;
bool watching = false;
bool counting = false;
unsigned long impactTime = 0;
unsigned long stillStart = 0;

// --- alert stage ---
const unsigned long COUNTDOWN_MS = 30000;   // 30s cancel window; lower to test faster
bool alertActive = false;
unsigned long alertStart = 0;
int lastSecondShown = -1;

// --- temperature asymmetry ---
const float TEMP_DIFF_LIMIT = 2.0;
const unsigned long DIFF_SUSTAIN = 10000;
bool diffCounting = false;
unsigned long diffStart = 0;
unsigned long lastTempRead = 0;
float tempLeft = 0, tempRight = 0;

void setup() {
  Serial.begin(115200);
  pinMode(MOTOR_PIN, OUTPUT);
  digitalWrite(MOTOR_PIN, LOW);
  pinMode(CANCEL_BTN, INPUT_PULLUP);
  tempSensor.begin();
  if (!mpu.begin()) {
    Serial.println("MPU6050 not found");
    while (1) delay(10);
  }
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
}

void loop() {
  // motion, every loop
  sensors_event_t a, g, t;
  mpu.getEvent(&a, &g, &t);
  float gForce = sqrt(a.acceleration.x*a.acceleration.x +
                      a.acceleration.y*a.acceleration.y +
                      a.acceleration.z*a.acceleration.z) / 9.81;

  if (alertActive) {
    // countdown + cancel
    unsigned long elapsed = millis() - alertStart;
    if (digitalRead(CANCEL_BTN) == LOW) {
      Serial.println(">> Alert cancelled by user. False alarm.");
      digitalWrite(MOTOR_PIN, LOW);
      alertActive = false;
    } else if (elapsed >= COUNTDOWN_MS) {
      Serial.println("*** SENDING SOS: GPS location + timestamp to family and medical ***");
      digitalWrite(MOTOR_PIN, LOW);
      alertActive = false;
    } else {
      int remaining = (COUNTDOWN_MS - elapsed) / 1000;
      if (remaining != lastSecondShown) {
        Serial.print("Countdown to SOS: "); Serial.print(remaining);
        Serial.println("s  (press button to cancel)");
        lastSecondShown = remaining;
      }
    }
  } else {
    // fall detection
    if (!watching) {
      if (gForce > IMPACT_G) {
        watching = true; counting = false;
        impactTime = millis();
        Serial.println(">> Impact detected, waiting to see if they stay still...");
      }
    } else {
      bool isStill = (gForce >= STILL_LOW && gForce <= STILL_HIGH);
      if (isStill) {
        if (!counting) { counting = true; stillStart = millis(); }
        if (millis() - stillStart > STILL_TIME) {
          Serial.println("!!! FALL DETECTED !!!");
          alertActive = true;
          alertStart = millis();
          lastSecondShown = -1;
          digitalWrite(MOTOR_PIN, HIGH);   // buzz the motor
          watching = false;
        }
      } else {
        counting = false;
      }
      if (watching && millis() - impactTime > GIVE_UP_TIME) {
        Serial.println(">> No stillness after impact, no fall.");
        watching = false;
      }
    }
  }

  // temperature asymmetry, every 1s
  if (millis() - lastTempRead > 1000) {
    tempSensor.requestTemperatures();
    tempLeft  = tempSensor.getTempCByIndex(0);
    tempRight = tempSensor.getTempCByIndex(1);
    lastTempRead = millis();

    float diff = fabs(tempLeft - tempRight);
    if (diff > TEMP_DIFF_LIMIT) {
      if (!diffCounting) { diffCounting = true; diffStart = millis(); }
      if (millis() - diffStart > DIFF_SUSTAIN) {
        Serial.print("### TEMP ASYMMETRY WARNING: ");
        Serial.print(diff); Serial.println(" C gap, possible foot inflammation ###");
        diffCounting = false;
      }
    } else {
      diffCounting = false;
    }

    if (!alertActive) {
      Serial.print("Force: "); Serial.print(gForce);
      Serial.print(" g   A: "); Serial.print(tempLeft);
      Serial.print(" C   B: "); Serial.print(tempRight);
      Serial.print(" C   gap: "); Serial.print(diff); Serial.println(" C");
    }
  }

  delay(100);
}