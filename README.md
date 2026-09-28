# Parking Assist

An ESP32-S3 garage parking assistant for ETHOS Builders Incubator students.

Parking Assist uses an ultrasonic distance sensor to measure how far a vehicle is from the wall, then shows a simple 8-level visual guide on an 8x8 LED matrix:

```text
Far away                                      Stop point        Too close
   |                                              |                |
   v                                              v                v
  off -> 1 row -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> full matrix -> flashing
```

Park the vehicle at the ideal stopping point, press the calibration button, and the ESP32-S3 stores that distance in nonvolatile memory. After that, guidance begins at **3x the calibrated distance**, fills the matrix as the vehicle approaches, shows a full matrix at the calibrated stop point, and flashes if the vehicle gets too close.

## Project Status

This is a GitHub-ready v1.0 build based on a working prototype:

- Board: ESP32-S3
- Distance sensor: HC-SR04 ultrasonic sensor
- Display: MAX7219 FC-16 8x8 LED matrix
- Calibration: momentary pushbutton on GPIO7
- Firmware: Arduino IDE / ESP32 Arduino core
- Display driver approach: direct `SPI.h` at 100 kHz
- Persistent calibration: ESP32 `Preferences` / NVS

## Hardware Validation

This firmware has been tested successfully on a real ESP32-S3 prototype with the HC-SR04 sensor, MAX7219 FC-16 LED matrix, GPIO7 calibration button, direct SPI display control, and persistent calibration.

## Repository Contents

```text
parking-assist/
├── README.md
├── LICENSE
├── src/
│   └── parking_assist/
│       └── parking_assist.ino
├── docs/
│   ├── BUILD_GUIDE.md
│   ├── HOW_IT_WORKS.md
│   └── TROUBLESHOOTING.md
├── hardware/
│   ├── WIRING.md
│   └── images/
│       └── .gitkeep
└── README-assets/
    └── .gitkeep
```

## Parts

| Part | Notes |
| --- | --- |
| ESP32-S3 development board | Tested with an ESP32-S3 style board |
| HC-SR04 ultrasonic sensor | Requires 5V power on most modules |
| MAX7219 FC-16 8x8 LED matrix | Normally specified for about 5V operation |
| Momentary pushbutton | Used for calibration |
| Resistors for voltage divider | Required to reduce HC-SR04 ECHO to ESP32-safe 3.3V |
| Breadboard and jumper wires | For prototype build |
| Regulated 5V supply | Recommended for a permanent build |

## Wiring Summary

| Device | Signal | ESP32-S3 Pin |
| --- | --- | --- |
| HC-SR04 | TRIG | GPIO5 |
| HC-SR04 | ECHO | GPIO6 through voltage divider |
| Calibration button | Signal | GPIO7, active HIGH with `INPUT_PULLDOWN` |
| MAX7219 FC-16 | CS / LOAD | GPIO10 |
| MAX7219 FC-16 | DIN | GPIO11 |
| MAX7219 FC-16 | CLK | GPIO12 |

All modules must share a common ground.

Important power note: the final prototype reported the MAX7219 working from the ESP32-S3 board's 3.3V pin because that board's labeled 5V pin did not provide output. That was useful for the prototype, but it is outside the normal MAX7219 module specification. For a permanent build, use a proper regulated 5V power design and confirm the display module's input compatibility.

See [hardware/WIRING.md](hardware/WIRING.md) for full wiring details.

## Install and Upload

1. Install the Arduino IDE.
2. Install ESP32 board support from Espressif.
3. Open [src/parking_assist/parking_assist.ino](src/parking_assist/parking_assist.ino).
4. Select your ESP32-S3 board and the correct USB port.
5. Upload the sketch.
6. Open Serial Monitor at `115200` baud.

No external LED matrix library is required. This project intentionally uses Arduino `SPI.h` directly because a `LedControl` library path caused an `avr/pgmspace.h` compatibility issue on ESP32-S3 during prototyping.

## Calibration

1. Place the sensor/display unit where it will live in the garage.
2. Park the vehicle at the ideal stopping point.
3. Press and release the calibration button.
4. Watch Serial Monitor for a message like:

```text
Calibration saved: 34.2 cm
```

The ESP32-S3 stores that value in NVS, so calibration survives resets and power loss.

## Display Behavior

Assume the calibrated stop distance is `30 cm`.

| Vehicle Distance | Display |
| --- | --- |
| `90 cm` or farther | Off |
| Between `90 cm` and `30 cm` | Progressively fills 1 to 8 rows |
| `30 cm` | Full 8x8 matrix |
| Less than `30 cm` | Flashing full matrix |

The start distance is calculated as:

```text
guidance_start = calibrated_stop_distance x 3
```

## Add Project Photos

Place final build photos and wiring diagrams here:

```text
hardware/images/
README-assets/
```

Suggested filenames:

```text
hardware/images/wiring-diagram.png
hardware/images/breadboard-prototype.jpg
hardware/images/final-mounted-build.jpg
README-assets/parking-assist-demo.gif
```

Then update this README to include the images.

## Documentation

- [Build Guide](docs/BUILD_GUIDE.md)
- [How It Works](docs/HOW_IT_WORKS.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Wiring](hardware/WIRING.md)

## Safety Notes

- ESP32-S3 GPIO pins are 3.3V logic and are not 5V tolerant.
- The HC-SR04 ECHO pin can output about 5V, so reduce it before connecting it to GPIO6.
- Use a common ground between the ESP32-S3, HC-SR04, MAX7219 module, and any external power supply.
- For permanent installation, mount electronics securely and protect them from moisture, heat, shorts, and vehicle contact.

## License

MIT License. See [LICENSE](LICENSE).
