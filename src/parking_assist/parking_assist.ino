/*
  Parking Assist v1.0

  ESP32-S3 garage parking assistant using:
  - HC-SR04 ultrasonic distance sensor
  - MAX7219 FC-16 8x8 LED matrix
  - Momentary calibration switch

  Behavior:
  - Press the calibration button when the vehicle is parked at the desired stop point.
  - The ESP32-S3 stores that distance in NVS using Preferences.
  - Guidance begins at 3x the calibrated distance.
  - The LED matrix fills from 1 to 8 rows as the vehicle approaches.
  - At the calibrated stop distance, the matrix is full.
  - If the vehicle is closer than the calibrated distance, the matrix flashes.
*/

#include <Preferences.h>
#include <SPI.h>
#include <math.h>

// ---------- Pin Configuration ----------
constexpr uint8_t TRIG_PIN = 5;
constexpr uint8_t ECHO_PIN = 6;       // HC-SR04 ECHO must be level-shifted to 3.3V.
constexpr uint8_t CAL_BUTTON_PIN = 7; // Active HIGH, uses ESP32-S3 internal pulldown.

constexpr uint8_t MAX7219_CS_PIN = 10;
constexpr uint8_t MAX7219_DIN_PIN = 11;
constexpr uint8_t MAX7219_CLK_PIN = 12;

// ---------- User Configuration ----------
constexpr uint8_t MATRIX_INTENSITY = 0x0A; // 0x00-0x0F. Prototype test worked well at 0x0A.
constexpr uint32_t SPI_CLOCK_HZ = 100000;  // Reliable 100 kHz direct SPI for this build.

constexpr float DEFAULT_STOP_DISTANCE_CM = 30.0;
constexpr float MIN_VALID_DISTANCE_CM = 2.0;
constexpr float MAX_VALID_DISTANCE_CM = 400.0;
constexpr float GUIDANCE_START_MULTIPLIER = 3.0;

constexpr uint8_t DISTANCE_SAMPLES = 5;
constexpr uint16_t MEASUREMENT_INTERVAL_MS = 120;
constexpr uint16_t STATUS_INTERVAL_MS = 1000;
constexpr uint16_t BUTTON_DEBOUNCE_MS = 60;
constexpr uint16_t FLASH_INTERVAL_MS = 250;
constexpr uint32_t ECHO_TIMEOUT_US = 30000; // About 5 meters round trip.

// ---------- Persistent Storage ----------
Preferences preferences;
constexpr const char *PREF_NAMESPACE = "parkassist";
constexpr const char *PREF_STOP_CM = "stop_cm";

// ---------- Runtime State ----------
float stopDistanceCm = DEFAULT_STOP_DISTANCE_CM;
uint8_t currentRows = 0;
bool flashState = false;
bool lastButtonReading = false;
bool stableButtonState = false;
uint32_t lastButtonChangeMs = 0;
uint32_t lastMeasurementMs = 0;
uint32_t lastStatusMs = 0;
uint32_t lastFlashMs = 0;

SPIClass matrixSPI(FSPI);

void writeMax7219(uint8_t address, uint8_t data) {
  matrixSPI.beginTransaction(SPISettings(SPI_CLOCK_HZ, MSBFIRST, SPI_MODE0));
  digitalWrite(MAX7219_CS_PIN, LOW);
  matrixSPI.transfer(address);
  matrixSPI.transfer(data);
  digitalWrite(MAX7219_CS_PIN, HIGH);
  matrixSPI.endTransaction();
}

void clearMatrix() {
  for (uint8_t row = 1; row <= 8; row++) {
    writeMax7219(row, 0x00);
  }
}

void setMatrixRows(uint8_t rows) {
  rows = constrain(rows, 0, 8);
  if (rows == currentRows) {
    return;
  }

  currentRows = rows;
  for (uint8_t row = 1; row <= 8; row++) {
    writeMax7219(row, row <= rows ? 0xFF : 0x00);
  }
}

void setMatrixFull(bool on) {
  currentRows = on ? 8 : 0;
  for (uint8_t row = 1; row <= 8; row++) {
    writeMax7219(row, on ? 0xFF : 0x00);
  }
}

void initializeMatrix() {
  pinMode(MAX7219_CS_PIN, OUTPUT);
  digitalWrite(MAX7219_CS_PIN, HIGH);

  matrixSPI.begin(MAX7219_CLK_PIN, -1, MAX7219_DIN_PIN, MAX7219_CS_PIN);

  writeMax7219(0x0F, 0x00);                 // Display test off.
  writeMax7219(0x0C, 0x01);                 // Normal operation.
  writeMax7219(0x09, 0x00);                 // No BCD decode.
  writeMax7219(0x0B, 0x07);                 // Scan all 8 rows.
  writeMax7219(0x0A, MATRIX_INTENSITY & 0x0F);
  clearMatrix();
}

float readDistanceOnceCm() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  uint32_t durationUs = pulseIn(ECHO_PIN, HIGH, ECHO_TIMEOUT_US);
  if (durationUs == 0) {
    return NAN;
  }

  // Speed of sound is about 0.0343 cm/us. Divide by 2 for out-and-back travel.
  float distanceCm = durationUs * 0.0343 / 2.0;
  if (distanceCm < MIN_VALID_DISTANCE_CM || distanceCm > MAX_VALID_DISTANCE_CM) {
    return NAN;
  }

  return distanceCm;
}

float readDistanceCm() {
  float total = 0.0;
  uint8_t validSamples = 0;

  for (uint8_t i = 0; i < DISTANCE_SAMPLES; i++) {
    float distance = readDistanceOnceCm();
    if (!isnan(distance)) {
      total += distance;
      validSamples++;
    }
    delay(10);
  }

  if (validSamples == 0) {
    return NAN;
  }

  return total / validSamples;
}

void saveCalibration(float distanceCm) {
  stopDistanceCm = distanceCm;
  preferences.putFloat(PREF_STOP_CM, stopDistanceCm);

  Serial.print("Calibration saved: ");
  Serial.print(stopDistanceCm, 1);
  Serial.println(" cm");
}

void handleCalibrationButton() {
  bool reading = digitalRead(CAL_BUTTON_PIN) == HIGH;
  uint32_t now = millis();

  if (reading != lastButtonReading) {
    lastButtonReading = reading;
    lastButtonChangeMs = now;
  }

  if ((now - lastButtonChangeMs) > BUTTON_DEBOUNCE_MS && reading != stableButtonState) {
    stableButtonState = reading;

    if (stableButtonState) {
      float distance = readDistanceCm();
      if (!isnan(distance)) {
        saveCalibration(distance);
        setMatrixRows(8);
      } else {
        Serial.println("Calibration failed: no valid distance reading.");
      }
    }
  }
}

uint8_t rowsForDistance(float distanceCm) {
  float guidanceStartCm = stopDistanceCm * GUIDANCE_START_MULTIPLIER;

  if (distanceCm >= guidanceStartCm) {
    return 0;
  }

  if (distanceCm <= stopDistanceCm) {
    return 8;
  }

  float progress = (guidanceStartCm - distanceCm) / (guidanceStartCm - stopDistanceCm);
  uint8_t rows = ceil(progress * 8.0);
  return constrain(rows, 1, 8);
}

void updateGuidance(float distanceCm) {
  uint32_t now = millis();

  if (distanceCm < stopDistanceCm) {
    if (now - lastFlashMs >= FLASH_INTERVAL_MS) {
      lastFlashMs = now;
      flashState = !flashState;
      setMatrixFull(flashState);
    }
    return;
  }

  flashState = false;
  setMatrixRows(rowsForDistance(distanceCm));
}

void printStatus(float distanceCm) {
  uint32_t now = millis();
  if (now - lastStatusMs < STATUS_INTERVAL_MS) {
    return;
  }

  lastStatusMs = now;
  Serial.print("Distance: ");
  if (isnan(distanceCm)) {
    Serial.print("no echo");
  } else {
    Serial.print(distanceCm, 1);
    Serial.print(" cm");
  }
  Serial.print(" | Stop: ");
  Serial.print(stopDistanceCm, 1);
  Serial.println(" cm");
}

void setup() {
  Serial.begin(115200);
  delay(500);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(CAL_BUTTON_PIN, INPUT_PULLDOWN);
  digitalWrite(TRIG_PIN, LOW);

  preferences.begin(PREF_NAMESPACE, false);
  stopDistanceCm = preferences.getFloat(PREF_STOP_CM, DEFAULT_STOP_DISTANCE_CM);

  initializeMatrix();

  Serial.println();
  Serial.println("Parking Assist v1.0");
  Serial.print("Loaded stop distance: ");
  Serial.print(stopDistanceCm, 1);
  Serial.println(" cm");
  Serial.println("Press the calibration button at the desired parking stop point.");
}

void loop() {
  handleCalibrationButton();

  uint32_t now = millis();
  if (now - lastMeasurementMs >= MEASUREMENT_INTERVAL_MS) {
    lastMeasurementMs = now;

    float distance = readDistanceCm();
    if (!isnan(distance)) {
      updateGuidance(distance);
    } else {
      setMatrixRows(0);
    }

    printStatus(distance);
  }
}
