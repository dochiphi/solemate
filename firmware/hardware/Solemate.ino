/* Solemate — sensors + BLE two-way + 4 FSRs + step count (single foot) */
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

#define ONE_WIRE_BUS 4
#define MOTOR_PIN    18
#define SERVICE_UUID "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
#define CHAR_TX_UUID "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"
#define CHAR_RX_UUID "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"

const int FSR_PINS[4] = {34, 33, 32, 35};   // heel, ball-in, ball-out, toe
int fsrBase[4] = {0, 0, 0, 0};

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature tempSensor(&oneWire);
Adafruit_MPU6050 mpu;

BLECharacteristic *txChar;
bool bleConnected = false;

const float IMPACT_G = 2.5, STILL_LOW = 0.8, STILL_HIGH = 1.2;
const unsigned long STILL_TIME = 2000, GIVE_UP_TIME = 15000;
bool watching = false, counting = false;
unsigned long impactTime = 0, stillStart = 0;

const unsigned long COUNTDOWN_MS = 10000;
const unsigned long SOS_HOLD_MS = 8000;
bool alertActive = false;
unsigned long alertStart = 0, sosHoldStart = 0;
int countdownSec = 0;

// step counting (simple pedometer)
const float STEP_HI = 1.25, STEP_LO = 1.05;
bool stepArmed = false;
unsigned long lastStepMs = 0;
long stepCount = 0;

unsigned long lastSend = 0;
float gForce = 0, tempC = 0;
String status = "OK";

class RxCallbacks : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic *c) {
    String cmd = c->getValue();
    if (cmd == "CANCEL") {
      alertActive = false;
      digitalWrite(MOTOR_PIN, LOW);
      status = "OK";
      countdownSec = 0;
      Serial.println(">> Alert cancelled from app");
    }
  }
};

class ServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer *s) { bleConnected = true; }
  void onDisconnect(BLEServer *s) { bleConnected = false; BLEDevice::startAdvertising(); }
};

void setup() {
  Serial.begin(115200);
  pinMode(MOTOR_PIN, OUTPUT);
  digitalWrite(MOTOR_PIN, LOW);
  tempSensor.begin();
  if (!mpu.begin()) { Serial.println("MPU6050 not found"); while (1) delay(10); }
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  for (int i = 0; i < 4; i++) fsrBase[i] = analogRead(FSR_PINS[i]);   // auto-zero at startup

  BLEDevice::init("Solemate");
  BLEServer *server = BLEDevice::createServer();
  server->setCallbacks(new ServerCallbacks());
  BLEService *service = server->createService(SERVICE_UUID);
  txChar = service->createCharacteristic(CHAR_TX_UUID, BLECharacteristic::PROPERTY_NOTIFY);
  txChar->addDescriptor(new BLE2902());
  BLECharacteristic *rxChar = service->createCharacteristic(
      CHAR_RX_UUID, BLECharacteristic::PROPERTY_WRITE);
  rxChar->setCallbacks(new RxCallbacks());
  service->start();
  BLEAdvertising *adv = BLEDevice::getAdvertising();
  adv->addServiceUUID(SERVICE_UUID);
  adv->setScanResponse(true);
  BLEDevice::startAdvertising();
  Serial.println("Ready, BLE advertising as 'Solemate'");
}

void loop() {
  sensors_event_t a, g, t;
  mpu.getEvent(&a, &g, &t);
  gForce = sqrt(a.acceleration.x*a.acceleration.x +
                a.acceleration.y*a.acceleration.y +
                a.acceleration.z*a.acceleration.z) / 9.81;

  // count a step on each acceleration peak, skip during an alert
  if (!alertActive && status != "SOS") {
    if (gForce < STEP_LO) stepArmed = true;
    if (gForce > STEP_HI && stepArmed && millis() - lastStepMs > 300) {
      stepCount++; lastStepMs = millis(); stepArmed = false;
    }
  }

  if (alertActive) {
    status = "FALL";
    long rem = ((long)COUNTDOWN_MS - (long)(millis() - alertStart)) / 1000;
    if (rem < 0) rem = 0;
    countdownSec = rem;
    if (millis() - alertStart >= COUNTDOWN_MS) {
      Serial.println("*** SENDING SOS ***");
      digitalWrite(MOTOR_PIN, LOW);
      alertActive = false;
      status = "SOS";
      countdownSec = 0;
      sosHoldStart = millis();
    }
  } else if (status == "SOS") {
    if (millis() - sosHoldStart >= SOS_HOLD_MS) status = "OK";
  } else {
    if (!watching) {
      if (gForce > IMPACT_G) { watching = true; counting = false; impactTime = millis();
        Serial.println(">> Impact detected"); }
    } else {
      bool isStill = (gForce >= STILL_LOW && gForce <= STILL_HIGH);
      if (isStill) {
        if (!counting) { counting = true; stillStart = millis(); }
        if (millis() - stillStart > STILL_TIME) {
          Serial.println("!!! FALL DETECTED !!!");
          alertActive = true; alertStart = millis();
          digitalWrite(MOTOR_PIN, HIGH); watching = false;
        }
      } else counting = false;
      if (watching && millis() - impactTime > GIVE_UP_TIME) {
        Serial.println(">> No fall"); watching = false;
      }
    }
  }

  if (millis() - lastSend > 500) {
    lastSend = millis();
    tempSensor.requestTemperatures();
    tempC = tempSensor.getTempCByIndex(0);

    String msg = "F:" + String(gForce, 2) + ",T:" + String(tempC, 1);
    for (int i = 0; i < 4; i++) {
      int v = analogRead(FSR_PINS[i]) - fsrBase[i];
      if (v < 0) v = 0;
      msg += ",P" + String(i + 1) + ":" + String(v);
    }
    msg += ",C:" + String(countdownSec) + ",S:" + status + ",ST:" + String(stepCount);

    if (bleConnected) { txChar->setValue(msg.c_str()); txChar->notify(); }
    Serial.println(msg);
  }

  delay(100);
}