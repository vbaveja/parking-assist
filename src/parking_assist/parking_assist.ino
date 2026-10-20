#include <SPI.h>
#include <Preferences.h>

// ============================================================
// ESP32-S3 GARAGE PARKING SENSOR WITH CALIBRATION
// ============================================================
//
// HC-SR04 Distance Sensor
//   VCC  -> 5V
//   GND  -> GND
//   TRIG -> GPIO 5
//   ECHO -> GPIO 6 through voltage divider
//
// Calibration Toggle Switch
//   One side -> 3.3V
//   Other side -> GPIO 7
//   GPIO 7 uses INPUT_PULLDOWN
//
// MAX7219 FC-16 LED Matrix
//   CS / LOAD -> GPIO 10
//   DIN       -> GPIO 11
//   CLK       -> GPIO 12
//   VCC       -> 5V
//   GND       -> GND
//
// IMPORTANT:
//   ESP32-S3 GPIO pins are 3.3V only.
//   Never connect HC-SR04 ECHO directly to GPIO 6.
//   Use a voltage divider on ECHO.
//
// NEW BEHAVIOR:
//   - LED meter fills from the opposite side.
//   - Display turns OFF after 5 seconds without movement.
//   - Display automatically wakes when movement resumes.
//
// ============================================================


// ============================================================
// PINS
// ============================================================

#define TRIG_PIN 5
#define ECHO_PIN 6

#define CAL_SWITCH 7

#define CS_PIN 10
#define DIN_PIN 11
#define CLK_PIN 12


// ============================================================
// OBJECTS
// ============================================================

SPIClass spi(FSPI);
Preferences preferences;


// ============================================================
// SETTINGS
// ============================================================

// Saved stopping distance.
float calibratedDistance = 0.0;


// Meter starts lighting at this multiple of stop distance.
//
// Example:
// stop distance = 50 cm
// display begins at 150 cm.
//
const float START_MULTIPLIER = 3.0;


// Number of samples used during calibration.
const int CALIBRATION_SAMPLES = 15;


// HC-SR04 timeout.
const unsigned long ECHO_TIMEOUT = 30000;


// Valid HC-SR04 range.
const float MIN_DISTANCE_CM = 2.0;
const float MAX_DISTANCE_CM = 400.0;


// ============================================================
// DISPLAY ORIENTATION
// ============================================================
//
// Your original code used:
//
// const bool FILL_FROM_BOTTOM = true;
//
// Since your physical matrix was filling from the wrong side,
// this has been reversed.
//
// If for some reason it still fills from the wrong physical
// side, change false back to true.
//
// ============================================================

const bool FILL_FROM_BOTTOM = false;


// ============================================================
// MOVEMENT / DISPLAY TIMEOUT SETTINGS
// ============================================================
//
// If distance doesn't change meaningfully for 5 seconds,
// turn the LED matrix completely OFF.
//
// HC-SR04 readings fluctuate slightly, so changes smaller
// than 2 cm are treated as sensor noise.
//
// ============================================================

const unsigned long NO_MOVEMENT_TIMEOUT = 5000;

const float MOVEMENT_THRESHOLD_CM = 2.0;


// ============================================================
// STATE VARIABLES
// ============================================================

// Tracks last displayed row count.
// -1 forces refresh.

int currentDisplayedRows = -1;


// Calibration switch state.

bool calibrationSwitchWasOn = false;


// ============================================================
// MOVEMENT STATE
// ============================================================

// Reference distance used for movement detection.

float lastMovementDistance = -1.0;


// Time when meaningful movement was last detected.

unsigned long lastMovementTime = 0;


// True when LEDs have been shut down because the car
// has remained stationary.

bool displayTimedOut = false;


// ============================================================
// MAX7219 LOW LEVEL WRITE
// ============================================================

void maxWrite(uint8_t reg, uint8_t value) {
  spi.beginTransaction(
    SPISettings(
      1000000,
      MSBFIRST,
      SPI_MODE0));

  digitalWrite(CS_PIN, LOW);

  spi.transfer(reg);
  spi.transfer(value);

  digitalWrite(CS_PIN, HIGH);

  spi.endTransaction();

  delayMicroseconds(20);
}


// ============================================================
// CLEAR MATRIX
// ============================================================

void clearMatrix() {
  for (uint8_t row = 1; row <= 8; row++) {
    maxWrite(row, 0x00);
  }

  currentDisplayedRows = 0;
}


// ============================================================
// FILL MATRIX
// ============================================================

void fillMatrix() {
  for (uint8_t row = 1; row <= 8; row++) {
    maxWrite(row, 0xFF);
  }

  currentDisplayedRows = 8;
}


// ============================================================
// DISPLAY METER ROWS
// ============================================================
//
// rows = 0 -> empty
// rows = 8 -> full
//
// ============================================================

void displayRows(int rows) {
  rows = constrain(rows, 0, 8);

  if (rows == currentDisplayedRows) {
    return;
  }

  for (uint8_t level = 1; level <= 8; level++) {
    uint8_t physicalRow;

    if (FILL_FROM_BOTTOM) {
      physicalRow = 9 - level;
    } else {
      physicalRow = level;
    }

    if (level <= rows) {
      maxWrite(physicalRow, 0xFF);
    } else {
      maxWrite(physicalRow, 0x00);
    }
  }

  currentDisplayedRows = rows;
}


// ============================================================
// INITIALIZE MAX7219
// ============================================================

void initializeMAX7219() {
  maxWrite(0x0F, 0x00);  // Display test OFF

  maxWrite(0x0C, 0x00);  // Shutdown while configuring

  maxWrite(0x09, 0x00);  // No decode mode

  maxWrite(0x0B, 0x07);  // Use all 8 rows


  // Brightness:
  // 0x00 = dimmest
  // 0x0F = brightest

  maxWrite(0x0A, 0x08);


  clearMatrix();


  maxWrite(0x0C, 0x01);  // Normal operation


  clearMatrix();
}


// ============================================================
// READ DISTANCE FROM HC-SR04
// ============================================================

float readDistanceCm() {
  digitalWrite(TRIG_PIN, LOW);

  delayMicroseconds(2);


  digitalWrite(TRIG_PIN, HIGH);

  delayMicroseconds(10);

  digitalWrite(TRIG_PIN, LOW);


  unsigned long duration = pulseIn(
    ECHO_PIN,
    HIGH,
    ECHO_TIMEOUT);


  if (duration == 0) {
    return -1;
  }


  // Speed of sound is approximately
  // 0.0343 cm per microsecond.
  //
  // Divide by two because sound travels
  // from sensor -> object -> sensor.

  float distance =
    duration * 0.0343 / 2.0;


  return distance;
}


// ============================================================
// FILTERED DISTANCE
// ============================================================
//
// Takes several readings and averages the valid ones.
//
// This makes the parking meter less jumpy.
//
// ============================================================

float getFilteredDistance() {
  const int samples = 5;


  float total = 0.0;

  int validSamples = 0;


  for (int i = 0; i < samples; i++) {
    float distance =
      readDistanceCm();


    if (
      distance >= MIN_DISTANCE_CM && distance <= MAX_DISTANCE_CM) {
      total += distance;

      validSamples++;
    }


    delay(20);
  }


  if (validSamples == 0) {
    return -1;
  }


  return total / validSamples;
}


// ============================================================
// CALIBRATION START ANIMATION
// ============================================================

void calibrationStartAnimation() {
  currentDisplayedRows = -1;


  for (int i = 0; i < 3; i++) {
    fillMatrix();

    delay(200);


    clearMatrix();

    delay(200);
  }


  currentDisplayedRows = -1;
}


// ============================================================
// CALIBRATION SUCCESS ANIMATION
// ============================================================

void calibrationSuccessAnimation() {
  currentDisplayedRows = -1;


  for (int rows = 1; rows <= 8; rows++) {
    displayRows(rows);

    delay(100);
  }


  delay(800);


  clearMatrix();


  currentDisplayedRows = -1;
}


// ============================================================
// CALIBRATION FAILURE ANIMATION
// ============================================================

void calibrationFailureAnimation() {
  currentDisplayedRows = -1;


  for (int i = 0; i < 6; i++) {
    fillMatrix();

    delay(100);


    clearMatrix();

    delay(100);
  }


  currentDisplayedRows = -1;
}


// ============================================================
// CALIBRATION MODE HOLD ANIMATION
// ============================================================
//
// Runs while toggle switch remains ON after calibration.
//
// ============================================================

void calibrationHoldAnimation() {
  static unsigned long lastBlink = 0;

  static bool blinkState = false;


  unsigned long now = millis();


  if (now - lastBlink >= 500) {
    lastBlink = now;

    blinkState = !blinkState;


    if (blinkState) {
      displayRows(2);
    } else {
      displayRows(0);
    }
  }
}


// ============================================================
// PERFORM CALIBRATION
// ============================================================

void calibrate() {
  Serial.println();

  Serial.println("==============================");

  Serial.println("CALIBRATION STARTED");

  Serial.println("==============================");

  Serial.println();


  Serial.println(
    "Keep the car/object at the desired stopping distance.");

  Serial.println("Measuring now...");

  Serial.println();


  calibrationStartAnimation();


  float total = 0.0;

  int validSamples = 0;


  for (int i = 0; i < CALIBRATION_SAMPLES; i++) {
    float distance =
      readDistanceCm();


    if (
      distance >= MIN_DISTANCE_CM && distance <= MAX_DISTANCE_CM) {
      total += distance;

      validSamples++;


      Serial.print("Sample ");

      Serial.print(validSamples);

      Serial.print(": ");

      Serial.print(distance, 1);

      Serial.println(" cm");
    } else {
      Serial.println("Invalid sample");
    }


    delay(100);
  }


  if (validSamples < 5) {
    Serial.println();

    Serial.println("CALIBRATION FAILED");

    Serial.println(
      "Not enough valid HC-SR04 readings.");

    Serial.println(
      "Check wiring and try again.");


    calibrationFailureAnimation();


    return;
  }


  calibratedDistance =
    total / validSamples;


  preferences.putFloat(
    "parkDist",
    calibratedDistance);


  Serial.println();

  Serial.println("==============================");

  Serial.println("CALIBRATION SAVED");

  Serial.println("==============================");


  Serial.print("Stop distance: ");

  Serial.print(calibratedDistance, 1);

  Serial.println(" cm");


  Serial.print("Meter starts at: ");

  Serial.print(
    calibratedDistance * START_MULTIPLIER,
    1);

  Serial.println(" cm");


  Serial.println();

  Serial.println(
    "Turn the calibration switch OFF to enter parking mode.");


  calibrationSuccessAnimation();
}


// ============================================================
// TOO CLOSE FLASHING
// ============================================================

void flashTooClose() {
  static unsigned long lastFlash = 0;

  static bool flashState = false;


  unsigned long now = millis();


  if (now - lastFlash >= 250) {
    lastFlash = now;

    flashState = !flashState;


    if (flashState) {
      fillMatrix();
    } else {
      clearMatrix();
    }


    currentDisplayedRows = -1;
  }
}


// ============================================================
// MOVEMENT / DISPLAY TIMEOUT
// ============================================================
//
// The HC-SR04 continues running even when LEDs are OFF.
//
// If distance changes by >= 2 cm:
//      movement detected
//      timer resets
//      display wakes
//
// If distance remains essentially unchanged for 5 seconds:
//      display switches OFF
//
// ============================================================

bool displayShouldBeActive(float distance) {
  unsigned long now = millis();


  // --------------------------------------------
  // First valid distance reading
  // --------------------------------------------

  if (lastMovementDistance < 0) {
    lastMovementDistance = distance;

    lastMovementTime = now;

    displayTimedOut = false;


    return true;
  }


  // --------------------------------------------
  // Calculate distance change
  // --------------------------------------------

  float movement =
    fabs(distance - lastMovementDistance);


  // --------------------------------------------
  // Meaningful movement detected
  // --------------------------------------------

  if (movement >= MOVEMENT_THRESHOLD_CM) {
    lastMovementDistance = distance;

    lastMovementTime = now;


    if (displayTimedOut) {
      Serial.println(
        "Movement detected - display ON");


      // Force the MAX7219 meter to redraw.

      currentDisplayedRows = -1;
    }


    displayTimedOut = false;


    return true;
  }


  // --------------------------------------------
  // No meaningful movement for 5 seconds
  // --------------------------------------------

  if (
    now - lastMovementTime >= NO_MOVEMENT_TIMEOUT) {
    if (!displayTimedOut) {
      Serial.println(
        "No movement for 5 seconds - display OFF");


      clearMatrix();


      displayTimedOut = true;
    }


    return false;
  }


  return true;
}


// ============================================================
// UPDATE PARKING DISPLAY
// ============================================================

void updateParkingDisplay(float distance) {
  if (calibratedDistance <= 0) {
    displayRows(0);

    return;
  }


  float startDistance =
    calibratedDistance * START_MULTIPLIER;


  // ----------------------------------------------------------
  // Far away
  // ----------------------------------------------------------

  if (distance > startDistance) {
    displayRows(0);

    return;
  }


  // ----------------------------------------------------------
  // Too close
  // ----------------------------------------------------------
  //
  // Flash whole matrix while car is moving.
  //
  // Once car stops for 5 seconds,
  // displayShouldBeActive() prevents this function
  // from being called and the display stays OFF.
  //
  // ----------------------------------------------------------

  if (distance <= calibratedDistance) {
    flashTooClose();

    return;
  }


  // ----------------------------------------------------------
  // Convert distance into progress
  // ----------------------------------------------------------
  //
  // progress = 0.0 -> entering guidance zone
  //
  // progress = 1.0 -> calibrated stopping distance
  //
  // ----------------------------------------------------------

  float progress =

    (startDistance - distance) /

    (startDistance - calibratedDistance);


  int rows =
    1 + (int)(progress * 7.0);


  rows =
    constrain(rows, 1, 8);


  displayRows(rows);
}


// ============================================================
// SETUP
// ============================================================

void setup() {
  Serial.begin(115200);


  delay(1000);


  Serial.println();

  Serial.println("==============================");

  Serial.println("ESP32-S3 PARKING SENSOR");

  Serial.println("==============================");

  Serial.println();


  Serial.println("Wiring:");

  Serial.println(
    "HC-SR04 TRIG -> GPIO 5");

  Serial.println(
    "HC-SR04 ECHO -> GPIO 6 through voltage divider");

  Serial.println(
    "Calibration switch -> GPIO 7");

  Serial.println(
    "MAX7219 CS  -> GPIO 10");

  Serial.println(
    "MAX7219 DIN -> GPIO 11");

  Serial.println(
    "MAX7219 CLK -> GPIO 12");

  Serial.println();


  Serial.println("Safety:");

  Serial.println(
    "HC-SR04 ECHO must go through a voltage divider.");

  Serial.println(
    "Do not connect 5V directly to any ESP32-S3 GPIO pin.");

  Serial.println();


  // ==========================================================
  // HC-SR04 SETUP
  // ==========================================================

  pinMode(
    TRIG_PIN,
    OUTPUT);

  pinMode(
    ECHO_PIN,
    INPUT);


  digitalWrite(
    TRIG_PIN,
    LOW);


  // ==========================================================
  // CALIBRATION SWITCH
  // ==========================================================

  pinMode(
    CAL_SWITCH,
    INPUT_PULLDOWN);


  // ==========================================================
  // MAX7219 SETUP
  // ==========================================================

  pinMode(
    CS_PIN,
    OUTPUT);


  digitalWrite(
    CS_PIN,
    HIGH);


  spi.begin(
    CLK_PIN,
    -1,
    DIN_PIN,
    CS_PIN);


  initializeMAX7219();


  // ==========================================================
  // PREFERENCES / FLASH STORAGE
  // ==========================================================

  preferences.begin(
    "parking",
    false);


  calibratedDistance =
    preferences.getFloat(
      "parkDist",
      0.0);


  if (calibratedDistance > 0) {
    Serial.print(
      "Loaded saved stop distance: ");

    Serial.print(
      calibratedDistance,
      1);

    Serial.println(" cm");


    Serial.print(
      "Meter starts at: ");

    Serial.print(
      calibratedDistance * START_MULTIPLIER,
      1);

    Serial.println(" cm");
  } else {
    Serial.println(
      "No calibration saved yet.");

    Serial.println(
      "Turn the calibration switch ON to set the stop distance.");
  }


  Serial.println();

  Serial.println("Ready.");

  Serial.println();


  currentDisplayedRows = -1;

  displayRows(0);


  // ==========================================================
  // INITIALIZE MOVEMENT TIMER
  // ==========================================================

  lastMovementDistance = -1.0;

  lastMovementTime = millis();

  displayTimedOut = false;
}


// ============================================================
// MAIN LOOP
// ============================================================

void loop() {
  bool calibrationSwitchIsOn =

    digitalRead(CAL_SWITCH) == HIGH;


  // ----------------------------------------------------------
  // CALIBRATION SWITCH ON
  // ----------------------------------------------------------

  if (calibrationSwitchIsOn) {
    delay(30);


    calibrationSwitchIsOn =

      digitalRead(CAL_SWITCH) == HIGH;


    if (calibrationSwitchIsOn) {
      if (!calibrationSwitchWasOn) {
        calibrationSwitchWasOn = true;


        calibrate();
      }


      calibrationHoldAnimation();


      delay(50);


      return;
    }
  }


  // ----------------------------------------------------------
  // CALIBRATION SWITCH JUST TURNED OFF
  // ----------------------------------------------------------

  if (calibrationSwitchWasOn) {
    calibrationSwitchWasOn = false;


    Serial.println();

    Serial.println(
      "Calibration switch OFF.");

    Serial.println(
      "Parking mode active.");

    Serial.println();


    currentDisplayedRows = -1;

    clearMatrix();


    // Reset movement detection after calibration.

    lastMovementDistance = -1.0;

    lastMovementTime = millis();

    displayTimedOut = false;
  }


  // ----------------------------------------------------------
  // NORMAL PARKING MODE
  // ----------------------------------------------------------

  float distance =
    getFilteredDistance();


  if (distance < 0) {
    Serial.println(
      "No echo detected");


    displayRows(0);
  } else {
    Serial.print(
      "Distance: ");

    Serial.print(
      distance,
      1);

    Serial.print(
      " cm");


    if (calibratedDistance > 0) {
      Serial.print(
        "   Stop: ");

      Serial.print(
        calibratedDistance,
        1);

      Serial.print(
        " cm");
    } else {
      Serial.print(
        "   Not calibrated");
    }


    Serial.println();


    // ========================================================
    // MOVEMENT DETECTION
    // ========================================================
    //
    // If car is moving:
    //     update parking display normally.
    //
    // If car has been stationary for 5 seconds:
    //     LEDs remain OFF.
    //
    // ========================================================

    if (displayShouldBeActive(distance)) {
      updateParkingDisplay(distance);
    } else {
      displayRows(0);
    }
  }


  delay(100);
}