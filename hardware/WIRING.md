# Wiring

This page documents the working prototype wiring for Parking Assist and the recommended power approach for a more permanent build.

## Pin Map

| Module | Module Pin | Connects To | Notes |
| --- | --- | --- | --- |
| HC-SR04 | VCC | 5V supply | Most HC-SR04 modules expect 5V |
| HC-SR04 | GND | Common GND | Must share ground with ESP32-S3 |
| HC-SR04 | TRIG | ESP32-S3 GPIO5 | ESP32 output to sensor |
| HC-SR04 | ECHO | ESP32-S3 GPIO6 through divider | Reduce 5V ECHO to about 3.3V |
| Button | One side | 3.3V | Calibration press sends HIGH |
| Button | Other side | ESP32-S3 GPIO7 | Firmware uses `INPUT_PULLDOWN` |
| MAX7219 FC-16 | VCC | Prefer regulated 5V | Prototype worked from 3.3V on this board only |
| MAX7219 FC-16 | GND | Common GND | Required |
| MAX7219 FC-16 | CS / LOAD | ESP32-S3 GPIO10 | Chip select |
| MAX7219 FC-16 | DIN | ESP32-S3 GPIO11 | SPI data |
| MAX7219 FC-16 | CLK | ESP32-S3 GPIO12 | SPI clock |

## Common Ground

All parts must share ground:

```text
ESP32-S3 GND ----- HC-SR04 GND
       |
       +---------- MAX7219 GND
       |
       +---------- external 5V supply GND, if used
```

Without a common ground, the signals do not have a shared reference. That can look like random display rows, missing ultrasonic readings, or behavior that changes when you touch a wire.

## HC-SR04 ECHO Level Reduction

ESP32-S3 GPIO pins use 3.3V logic and are not 5V tolerant. Many HC-SR04 modules output an ECHO signal close to 5V, so do not connect ECHO directly to the ESP32-S3.

Use a resistor voltage divider. A common pair is:

```text
HC-SR04 ECHO ---- 1 kOhm ----+---- ESP32-S3 GPIO6
                             |
                           2 kOhm
                             |
                            GND
```

That reduces a 5V echo pulse to about 3.3V:

```text
5V x 2k / (1k + 2k) = 3.33V
```

Other resistor values are fine if the ratio is similar, such as 10 kOhm and 20 kOhm.

## Calibration Button

The firmware configures GPIO7 as:

```cpp
pinMode(CAL_BUTTON_PIN, INPUT_PULLDOWN);
```

Wire the button so pressing it connects GPIO7 to 3.3V:

```text
3.3V ---- button ---- GPIO7
```

When the button is not pressed, the ESP32-S3 internal pulldown keeps the input LOW. When pressed, the input becomes HIGH.

During prototyping, the button logic was initially reversed. If pressing the button appears to do nothing, confirm that the button sends HIGH when pressed.

## MAX7219 FC-16 Wiring

The MAX7219 module is controlled with direct SPI:

```text
ESP32-S3 GPIO10 -> CS / LOAD
ESP32-S3 GPIO11 -> DIN
ESP32-S3 GPIO12 -> CLK
GND             -> GND
Power           -> VCC
```

The firmware uses a conservative 100 kHz SPI clock for reliability:

```cpp
constexpr uint32_t SPI_CLOCK_HZ = 100000;
```

## MAX7219 Power Note

The working prototype reported the MAX7219 FC-16 display working from the ESP32-S3 board's 3.3V pin because the board's labeled 5V pin did not provide output.

That prototype detail is worth documenting, but it should not be treated as the normal design recommendation.

The MAX7219 and many FC-16 modules are normally specified around 5V operation. Running the module from 3.3V may be dim, unreliable, module-specific, or outside specification. For a permanent build, use a proper regulated 5V supply sized for the LED matrix current and connect all grounds together.

## Recommended Permanent Power Design

For a robust garage installation:

```text
Regulated 5V supply
├── ESP32-S3 5V/VIN input, if your board supports it
├── HC-SR04 VCC
└── MAX7219 VCC

All grounds connected together
```

Before wiring power this way, confirm your specific ESP32-S3 board's power input labeling and limits. Board labels vary.

## Photo Placeholders

Add final images to:

```text
hardware/images/
```

Suggested files:

```text
wiring-diagram.png
breadboard-prototype.jpg
final-mounted-build.jpg
```
