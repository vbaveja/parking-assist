# ESP32 Garage Parking-Assist Enclosure

Generated files:

- `front_panel.stl`
- `main_body.stl`
- `rear_cover.stl`
- `source_model.py` is the editable source/model.
- `validation_report.txt` contains manifold checks for each mesh.

Final outside dimensions:

- Assembled width: `112.0 mm`
- Assembled height: `86.0 mm`
- Assembled depth: `41.0 mm`
- Front panel: `112.0 x 86.0 x 4.0 mm`
- Main body: `112.0 x 86.0 x 34.0 mm`
- Rear cover: `112.0 x 86.0 x 4.0 mm` total, including a `1.0 mm` inset lip that overlaps the main body.

Measured module allowances used:

- MAX7219 FC-16: `32.1 x 32.1 mm`, with a `33.6 x 33.6 mm` front opening and internal cable depth allowance.
- MAX7219 mounting bosses: four internal bosses centered behind the display opening. Your measured mounting-hole edge-to-edge distances are `28.9 x 23.2 mm`; with the modeled `2.5 mm` pilot holes, the resulting center spacing is `26.4 x 20.7 mm`. The boss support face is `8.0 mm` below the main-body top/open side, and the support is a `10.0 mm` tall retaining box with a `33.4 x 33.4 mm` inner opening around the board.
- HC-SR04: `45.3 x 26.4 mm` PCB, with two `16 mm` transducer apertures, modeled at `16.9 mm` diameter for FDM clearance. The cylinder wall-to-wall gap is `10.1 mm`, giving `27.0 mm` center spacing.
- HC-SR04 support: two center underside rails support the sensor PCB at `9.0 mm` below the main-body top/open side, with ribs tying them into the top wall and nearby ESP32/MAX support structure.
- Tactile switch: `13.6 x 18.4 mm` PCB, `14.0 mm` depth, and a `12.4 mm` front-panel opening for the exposed switch.
- ESP32-S3: `64.0 x 28.4 mm`, with `11.4 mm` depth allowance for pins/wire connectors.
- ESP32-S3 USB access: right-side opening spans the two USB ports over a `21.0 mm` port group, with added FDM/cable clearance.
- ESP32-S3 support: two center lengthwise underside rails hold the board height while leaving the edge/side-port area clear; a left end stop positions the board lengthwise, and small cross-ties join the two rails so they are structurally supported.
- Tactile switch retention: the switch is in the lower section below the ESP32-S3 bay. Switch-local retaining walls support the `14.0 mm`-deep switch assembly without extending into the ESP32-S3 area; the printed support wall height is `9.0 mm`.
- Structural note: internal supports are tied back to the main shell with small ribs, and the validation report includes a connected-component check to catch floating islands.

Print orientation:

- `front_panel.stl`: print with the outside face down on the build plate.
- `main_body.stl`: print with the rear side down and the open/front side up. This keeps the USB side opening and vents clean with minimal support.
- `rear_cover.stl`: print flat, outside face down.

Recommended Creality/FDM settings:

- Material: PLA or PETG. PLA is easiest for a first fit check; PETG is better if the garage gets warm.
- Nozzle: `0.4 mm`.
- Layer height: `0.20 mm`.
- Wall line count: `3` or `4`.
- Top/bottom layers: `5`.
- Infill: `15%` to `25%`.
- Supports: off for the front panel and rear cover; supports usually off for the body, but enable touching-build-plate supports if your slicer struggles with the USB opening.
- Brim: optional, `3-5 mm`, useful for PETG or if corners lift.
- Hardware: M3 screws for the four corner fastening points. Start with `M3 x 8-12 mm` depending on your inserts/screws.

Fit notes:

- The model intentionally uses practical FDM clearances around the display, transducer openings, threaded switch body, and ESP32-S3 dual-USB opening.
- Do a first print of the front panel only if you want to confirm the visible component fit before committing to the full enclosure.
- If your USB cable plugs have bulky molded housings, widen the USB side opening in `USB_OPENING`.

Validation summary:

front_panel.stl: 151040 triangles, 302080 vertices, 226560 unique edges, 0 non-manifold edges, 1 connected solid component(s)
main_body.stl: 379176 triangles, 758352 vertices, 568764 unique edges, 0 non-manifold edges, 1 connected solid component(s)
rear_cover.stl: 169824 triangles, 339648 vertices, 254736 unique edges, 0 non-manifold edges, 1 connected solid component(s)
