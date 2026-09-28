# Build Guide

This guide walks through building Parking Assist from parts to first calibration.

## 1. Gather Parts

- ESP32-S3 development board
- HC-SR04 ultrasonic distance sensor
- MAX7219 FC-16 8x8 LED matrix
- Momentary pushbutton
- Breadboard and jumper wires
- Resistors for the HC-SR04 ECHO voltage divider
- USB cable for programming
- Regulated 5V supply for a permanent build

## 2. Assemble the Circuit

Follow the wiring table in [../hardware/WIRING.md](../hardware/WIRING.md).

Key checks before powering:

- ESP32-S3, sensor, display, and external supply grounds are connected together.
- HC-SR04 ECHO is reduced before it reaches GPIO6.
- The calibration button connects GPIO7 to 3.3V when pressed.
- MAX7219 DIN, CLK, and CS are connected to GPIO11, GPIO12, and GPIO10.

## 3. Install Arduino IDE Support

1. Install the Arduino IDE.
2. Add ESP32 board support from Espressif.
3. Select an ESP32-S3 board profile that matches your board.
4. Connect the board over USB.
5. Select the correct serial port.

No extra MAX7219 library is needed. The firmware uses Arduino `SPI.h` directly.

## 4. Upload the Firmware

Open:

```text
src/parking_assist/parking_assist.ino
```

Upload it to the ESP32-S3.

Open Serial Monitor at:

```text
115200 baud
```

You should see startup text similar to:

```text
Parking Assist v1.0
Loaded stop distance: 30.0 cm
Press the calibration button at the desired parking stop point.
```

## 5. First Sensor Test

Move an object in front of the HC-SR04. Serial Monitor should show distance updates:

```text
Distance: 72.4 cm | Stop: 30.0 cm
```

If it says `no echo`, check:

- HC-SR04 VCC and GND
- TRIG on GPIO5
- ECHO path through the voltage divider to GPIO6
- Sensor direction and distance from the target
- Common ground

## 6. First Matrix Test

Move an object closer to the sensor. As it approaches the calibrated stop distance, the display should fill more rows.

Default stop distance is `30 cm`, so guidance begins at:

```text
30 cm x 3 = 90 cm
```

If the object is farther than that, the matrix may be off. That is normal.

## 7. Calibrate

1. Put the device in its intended garage location.
2. Park the vehicle at the desired final stop point.
3. Press and release the calibration button.
4. Confirm the saved distance in Serial Monitor.

The saved value remains after reset because it is stored in ESP32 nonvolatile storage.

## 8. Tune Brightness

The MAX7219 brightness is controlled here:

```cpp
constexpr uint8_t MATRIX_INTENSITY = 0x0A;
```

Valid values are:

```text
0x00 dimmest
0x0F brightest
```

The working prototype used `0x0A`.

## 9. Make It Durable

For a permanent build:

- Use a regulated 5V supply with enough current for the LED matrix.
- Secure all wires.
- Add strain relief for power and USB.
- Mount the sensor so it faces the vehicle cleanly.
- Protect the electronics from moisture and accidental contact.
- Consider an enclosure with openings for the ultrasonic sensor and LED matrix.

## 10. Document Your Build

Take photos of:

- Breadboard wiring
- Sensor and matrix mounting
- Final installation location
- Vehicle at calibrated stop point

Add them to:

```text
hardware/images/
```
