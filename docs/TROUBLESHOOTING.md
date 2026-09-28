# Troubleshooting

This guide collects issues encountered during the prototype and the checks most likely to fix them.

## Arduino Compile Error: `avr/pgmspace.h`

Symptom:

```text
fatal error: avr/pgmspace.h: No such file or directory
```

Cause:

Some MAX7219 examples use a `LedControl` library path written for AVR Arduino boards. ESP32-S3 is not an AVR board.

Fix:

Use this repository's firmware, which controls the MAX7219 directly with Arduino `SPI.h`. No `LedControl` library is required.

## Calibration Button Does Nothing

Likely causes:

- Button wiring is reversed for the firmware logic.
- GPIO7 is not actually connected to 3.3V when pressed.
- Button is connected to ground instead of 3.3V.
- Wrong GPIO pin is used.

Expected behavior:

```text
not pressed -> GPIO7 LOW
pressed     -> GPIO7 HIGH
```

The firmware uses:

```cpp
pinMode(CAL_BUTTON_PIN, INPUT_PULLDOWN);
```

## Serial Monitor Shows `no echo`

Likely causes:

- HC-SR04 is not powered.
- TRIG and ECHO wires are swapped.
- ECHO is not connected through the voltage divider.
- GPIO number does not match the firmware.
- Sensor is pointed away from the target.
- Target is too close, too far, angled, soft, or hard to reflect.
- Grounds are not connected together.

Checks:

- TRIG should be on GPIO5.
- ECHO should reach GPIO6 through level reduction.
- HC-SR04 GND and ESP32-S3 GND must be connected.
- Try a flat object 20-100 cm in front of the sensor.

## Matrix Is Blank

Check:

- MAX7219 VCC and GND
- Common ground with ESP32-S3
- CS / LOAD on GPIO10
- DIN on GPIO11
- CLK on GPIO12
- Module orientation and input side
- Brightness setting
- Power supply capability

Also remember that the matrix is intentionally off when the measured object is farther away than 3x the calibrated stop distance.

For a quick logic test, move a flat object closer than the default 90 cm start range or press the calibration button with an object in front of the sensor.

## Matrix Shows Random or Missing Rows

This was seen during prototyping and was strongly connected to display power behavior.

Likely causes:

- MAX7219 module is underpowered.
- Power pin on the ESP32-S3 board does not behave as expected.
- Grounds are not common.
- Jumper wires are loose.
- SPI clock is too fast for the wiring.

The firmware uses 100 kHz SPI for reliability:

```cpp
constexpr uint32_t SPI_CLOCK_HZ = 100000;
```

The prototype reported the MAX7219 working from the board's 3.3V pin because the labeled 5V pin did not provide output. That is a useful prototype note, not a permanent design recommendation. For a permanent build, use a proper regulated 5V supply.

## Matrix Too Dim or Too Bright

Adjust:

```cpp
constexpr uint8_t MATRIX_INTENSITY = 0x0A;
```

Valid range:

```text
0x00 dimmest
0x0F brightest
```

The working test used `0x0A`.

## Matrix Wiring Looks Correct but Still Fails

Try these steps:

1. Lower `MATRIX_INTENSITY` to reduce current draw.
2. Keep wires short.
3. Confirm the module input side. Some FC-16 modules have IN and OUT connectors.
4. Use the recommended 5V supply for the display.
5. Recheck common ground.
6. Confirm the firmware pin constants match your physical wiring.

## Display Works Only From 3.3V

This can happen on a particular prototype board if the labeled 5V pin is not supplying output.

Do not assume this is generally correct. The MAX7219 is normally specified for about 5V operation, and a different module may not work reliably at 3.3V.

For a permanent build:

- identify the board's actual 5V/VIN behavior
- use a regulated 5V supply
- connect grounds together
- verify current capacity

## Calibration Saves a Bad Distance

Possible causes:

- Vehicle was not at the intended stop point.
- Sensor was angled or reflecting off a bumper shape poorly.
- Object was too close to the sensor.
- Ultrasonic reading was unstable.

Fix:

Reposition the sensor, park at the desired stop point, and press the calibration button again.

## Upload Fails

Checks:

- Correct ESP32-S3 board selected.
- Correct USB port selected.
- USB cable supports data, not just charging.
- Board is in bootloader mode if required.
- Serial Monitor is closed during upload if your setup requires it.

## The Device Seems Backwards

Expected display language:

```text
farther than 3x stop distance -> off
approaching                 -> more rows
at stop point               -> full matrix
too close                   -> flashing
```

If the display fills at the wrong time, recalibrate with the vehicle at the desired stop point and confirm the Serial Monitor distance readings make sense.
