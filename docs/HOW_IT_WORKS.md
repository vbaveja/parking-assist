# How It Works

Parking Assist combines four beginner-friendly embedded systems ideas:

- ultrasonic time-of-flight distance measurement
- SPI communication with an LED driver
- a digital calibration button
- nonvolatile memory

## Ultrasonic Distance Measurement

The HC-SR04 sensor measures distance using sound.

1. The ESP32-S3 sends a short pulse to the sensor's TRIG pin.
2. The sensor emits an ultrasonic sound pulse.
3. The sound bounces off the vehicle and returns to the sensor.
4. The sensor raises the ECHO pin for the amount of time the sound was traveling.
5. The ESP32-S3 measures that ECHO pulse width.

The firmware uses:

```cpp
float distanceCm = durationUs * 0.0343 / 2.0;
```

Why divide by 2? The sound travels from the sensor to the vehicle and back again. The distance to the vehicle is only half of that round trip.

## ESP32-S3 GPIO Voltage

ESP32-S3 GPIO pins use 3.3V logic. That means a HIGH signal is about 3.3V.

Many HC-SR04 modules output a 5V ECHO signal. Since ESP32-S3 GPIO pins are not 5V tolerant, the ECHO signal needs a voltage divider before connecting to GPIO6.

This is one of the most important hardware lessons in the project: a signal can be logically correct but electrically unsafe.

## Calibration Button

The calibration button lets the builder teach the device the correct stop distance.

The firmware uses:

```cpp
pinMode(CAL_BUTTON_PIN, INPUT_PULLDOWN);
```

That means GPIO7 naturally reads LOW. Pressing the button connects GPIO7 to 3.3V, so it reads HIGH.

When the button is pressed, the ESP32-S3 reads the current ultrasonic distance and stores it as the stop point.

## Nonvolatile Storage

The ESP32-S3 can store small values in nonvolatile storage, often called NVS. Nonvolatile means the value remains even after power is removed.

This project uses Arduino's `Preferences` library:

```cpp
preferences.putFloat("stop_cm", stopDistanceCm);
```

On the next boot, the firmware loads the stored value:

```cpp
stopDistanceCm = preferences.getFloat("stop_cm", DEFAULT_STOP_DISTANCE_CM);
```

That is why the device does not need to be recalibrated every time it powers on.

## SPI and the MAX7219

The MAX7219 is a display driver chip. Instead of the ESP32-S3 controlling every LED directly, the ESP32-S3 sends compact commands to the MAX7219.

This project uses three signal wires:

| Signal | Meaning |
| --- | --- |
| DIN | Data sent from ESP32-S3 to MAX7219 |
| CLK | Clock pulse that times the data |
| CS / LOAD | Selects the chip and loads the command |

The firmware sends two bytes at a time:

```text
register address + register value
```

For example, the intensity register is address `0x0A`. The prototype used:

```cpp
writeMax7219(0x0A, 0x0A);
```

That sets the brightness to a medium-high level.

## Why Direct SPI Instead of LedControl

During prototyping, a `LedControl` library path included `avr/pgmspace.h`, which is meant for AVR Arduino boards rather than ESP32-S3.

The clean fix was to use Arduino `SPI.h` directly. That removes the dependency problem and makes the MAX7219 commands visible for students to study.

The firmware uses a conservative SPI speed:

```cpp
constexpr uint32_t SPI_CLOCK_HZ = 100000;
```

100 kHz is slow for SPI, but reliable and easy to debug.

## Distance-to-Display Mapping

The project converts distance into 8 visual levels.

First, it calculates the guidance start distance:

```text
guidance_start = calibrated_stop_distance x 3
```

If the calibrated stop distance is `30 cm`, guidance starts at `90 cm`.

Then it maps the vehicle's position between those two distances:

```text
90 cm -> 0 rows
30 cm -> 8 rows
```

As the vehicle gets closer, more rows turn on.

## Too Close Behavior

If the measured distance is less than the calibrated stop distance, the display flashes.

This creates a simple language:

```text
Off       = not close yet
More rows = keep approaching
Full      = stop here
Flashing  = too close
```

## Why This Is a Good ETHOS Project

Parking Assist is small enough to build in a workshop, but it contains real engineering decisions:

- electrical safety for 3.3V GPIO
- sensor noise and invalid readings
- human-centered feedback
- persistent configuration
- debugging library compatibility
- separating prototype behavior from permanent power design

Students get to see how a simple idea becomes a real embedded system.
