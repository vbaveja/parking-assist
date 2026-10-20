from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from pathlib import Path
import shutil
import struct
from collections import deque

import numpy as np
from PIL import Image, ImageDraw, ImageFont


RESOLUTION_MM = 0.5
OUTPUT_DIR = Path("garage_parking_enclosure")
FONT_REGULAR = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
FONT_BOLD = Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf")


@dataclass(frozen=True)
class Box:
    x0: float
    x1: float
    y0: float
    y1: float
    z0: float
    z1: float


@dataclass(frozen=True)
class PartSpec:
    name: str
    width: float
    height: float
    depth: float


WALL = 2.4
CLEARANCE = 0.5
OUTER_W = 112.0
OUTER_H = 86.0
FRONT_BASE_D = 4.0
TEXT_RAISE_D = 0.0
FRONT_D = FRONT_BASE_D
BODY_D = 34.0
REAR_VISIBLE_D = 3.0
REAR_D = 4.0
TOTAL_D = FRONT_D + BODY_D + REAR_VISIBLE_D

M3_CLEARANCE_R = 1.65
BOSS_R = 4.2
CORNER_SCREWS = (
    (7.5, 7.5),
    (OUTER_W - 7.5, 7.5),
    (7.5, OUTER_H - 7.5),
    (OUTER_W - 7.5, OUTER_H - 7.5),
)

MATRIX_BOARD_SIZE = 32.1
MATRIX_BODY_DEPTH = 13.2
MATRIX_TOTAL_DEPTH_WITH_PINS = 21.7
MATRIX_OPENING = Box(7.0, 40.6, 20.2, 53.8, -1.0, FRONT_D + 1.0)
MATRIX_CLEARANCE_SIZE = MATRIX_BOARD_SIZE + 1.1
MATRIX_BOARD_KEEPIN = Box(7.6, 40.8, 20.4, 53.6, BODY_D - MATRIX_TOTAL_DEPTH_WITH_PINS - 0.8, BODY_D + 1.0)
MATRIX_CENTER = (
    (MATRIX_OPENING.x0 + MATRIX_OPENING.x1) / 2,
    (MATRIX_OPENING.y0 + MATRIX_OPENING.y1) / 2,
)
MATRIX_MOUNT_EDGE_TO_EDGE_X = 28.9
MATRIX_MOUNT_EDGE_TO_EDGE_Y = 23.2
MATRIX_BOSS_R = 2.8
MATRIX_PILOT_R = 1.25
MATRIX_SUPPORT_BELOW_BODY_TOP = 8.0
MATRIX_SUPPORT_Z_TOP = BODY_D - MATRIX_SUPPORT_BELOW_BODY_TOP
MATRIX_SUPPORT_HEIGHT = 10.0
MATRIX_SUPPORT_Z_BOTTOM = MATRIX_SUPPORT_Z_TOP - MATRIX_SUPPORT_HEIGHT
MATRIX_SUPPORT_INNER_SIZE = MATRIX_BOARD_SIZE + 1.3
MATRIX_SUPPORT_WALL = 1.6
MATRIX_SUPPORT_OUTER_SIZE = MATRIX_SUPPORT_INNER_SIZE + MATRIX_SUPPORT_WALL * 2
MATRIX_SUPPORT_INNER_X0 = MATRIX_CENTER[0] - MATRIX_SUPPORT_INNER_SIZE / 2
MATRIX_SUPPORT_INNER_X1 = MATRIX_CENTER[0] + MATRIX_SUPPORT_INNER_SIZE / 2
MATRIX_SUPPORT_INNER_Y0 = MATRIX_CENTER[1] - MATRIX_SUPPORT_INNER_SIZE / 2
MATRIX_SUPPORT_INNER_Y1 = MATRIX_CENTER[1] + MATRIX_SUPPORT_INNER_SIZE / 2
MATRIX_SUPPORT_OUTER_X0 = MATRIX_CENTER[0] - MATRIX_SUPPORT_OUTER_SIZE / 2
MATRIX_SUPPORT_OUTER_X1 = MATRIX_CENTER[0] + MATRIX_SUPPORT_OUTER_SIZE / 2
MATRIX_SUPPORT_OUTER_Y0 = MATRIX_CENTER[1] - MATRIX_SUPPORT_OUTER_SIZE / 2
MATRIX_SUPPORT_OUTER_Y1 = MATRIX_CENTER[1] + MATRIX_SUPPORT_OUTER_SIZE / 2
MATRIX_MOUNT_SPACING_X = MATRIX_MOUNT_EDGE_TO_EDGE_X - (MATRIX_PILOT_R * 2)
MATRIX_MOUNT_SPACING_Y = MATRIX_MOUNT_EDGE_TO_EDGE_Y - (MATRIX_PILOT_R * 2)
MATRIX_MOUNT_HOLES = (
    (MATRIX_CENTER[0] - MATRIX_MOUNT_SPACING_X / 2, MATRIX_CENTER[1] - MATRIX_MOUNT_SPACING_Y / 2),
    (MATRIX_CENTER[0] + MATRIX_MOUNT_SPACING_X / 2, MATRIX_CENTER[1] - MATRIX_MOUNT_SPACING_Y / 2),
    (MATRIX_CENTER[0] - MATRIX_MOUNT_SPACING_X / 2, MATRIX_CENTER[1] + MATRIX_MOUNT_SPACING_Y / 2),
    (MATRIX_CENTER[0] + MATRIX_MOUNT_SPACING_X / 2, MATRIX_CENTER[1] + MATRIX_MOUNT_SPACING_Y / 2),
)

SONAR_BOARD_LENGTH = 45.3
SONAR_BOARD_WIDTH = 26.4
SONAR_TOTAL_DEPTH = 19.3
SONAR_CENTER_Y = 68.2
SONAR_LEFT_X = 62.7
SONAR_GAP = 10.1
SONAR_R = 8.45
SONAR_RIGHT_X = SONAR_LEFT_X + (SONAR_R * 2) + SONAR_GAP
SONAR_BOARD_KEEPIN = Box(52.6, 98.9, 54.5, 81.9, BODY_D - SONAR_TOTAL_DEPTH - 0.8, BODY_D + 1.0)
SONAR_SUPPORT_BELOW_BODY_TOP = 9.0
SONAR_SUPPORT_Z_TOP = BODY_D - SONAR_SUPPORT_BELOW_BODY_TOP
SONAR_SUPPORT_HEIGHT = 1.6
SONAR_SUPPORT_RAIL_WIDTH = 2.0
SONAR_SUPPORT_RAIL_GAP = 6.0

SWITCH_CENTER = ((SONAR_LEFT_X + SONAR_RIGHT_X) / 2, 14.5)
SWITCH_PCB_WIDTH = 13.6
SWITCH_PCB_LENGTH = 18.4
SWITCH_R = 6.2
SWITCH_ASSEMBLY_DEPTH = 14.0
SWITCH_BACKSTOP_Z = BODY_D - SWITCH_ASSEMBLY_DEPTH - 0.8
SWITCH_SUPPORT_HEIGHT = 9.0
SWITCH_SUPPORT_Z_BOTTOM = BODY_D - SWITCH_SUPPORT_HEIGHT
SWITCH_SUPPORT_X0 = SWITCH_CENTER[0] - 11.0
SWITCH_SUPPORT_X1 = SWITCH_CENTER[0] + 11.0
SWITCH_SUPPORT_SIDE_WALL = 1.6
SWITCH_PCB_KEEPIN = Box(
    SWITCH_CENTER[0] - SWITCH_PCB_WIDTH / 2,
    SWITCH_CENTER[0] + SWITCH_PCB_WIDTH / 2,
    5.3,
    23.7,
    SWITCH_BACKSTOP_Z,
    BODY_D + 1.0,
)

ESP32S3_LENGTH = 64.0
ESP32S3_WIDTH = 28.4
ESP32S3_DEPTH_WITH_PINS = 11.4
ESP32S3_X0 = OUTER_W - WALL - ESP32S3_LENGTH - 0.8
ESP32S3_X1 = OUTER_W - WALL + 0.2
ESP32S3_Y0 = 25.0
ESP32S3_Y1 = ESP32S3_Y0 + ESP32S3_WIDTH + 0.6
ESP32S3_SUPPORT_Z = BODY_D - ESP32S3_DEPTH_WITH_PINS - 1.0
ESP32S3_Z0 = ESP32S3_SUPPORT_Z
ESP32S3_Z1 = BODY_D + 1.0
USB_DUAL_PORT_SPAN = 21.0
ESP32S3_RAIL_WIDTH = 2.0
ESP32S3_RAIL_GAP = 7.0
ESP32S3_CENTER_Y = (ESP32S3_Y0 + ESP32S3_Y1) / 2
USB_OPENING = Box(
    OUTER_W - WALL - 0.2,
    OUTER_W + 1.0,
    (ESP32S3_Y0 + ESP32S3_Y1) / 2 - USB_DUAL_PORT_SPAN / 2 - 1.5,
    (ESP32S3_Y0 + ESP32S3_Y1) / 2 + USB_DUAL_PORT_SPAN / 2 + 1.5,
    ESP32S3_Z0 + 1.5,
    ESP32S3_Z1 + 1.0,
)
ESP32_KEEPIN = Box(ESP32S3_X0, ESP32S3_X1, ESP32S3_Y0, ESP32S3_Y1, ESP32S3_Z0, ESP32S3_Z1)


def in_box(x, y, z, box: Box):
    return (
        (x >= box.x0)
        & (x <= box.x1)
        & (y >= box.y0)
        & (y <= box.y1)
        & (z >= box.z0)
        & (z <= box.z1)
    )


def cyl_z(x, y, cx, cy, r):
    return (x - cx) ** 2 + (y - cy) ** 2 <= r**2


def keyhole_z(x, y, cx, cy):
    upper = (x - cx) ** 2 + (y - (cy + 4.0)) ** 2 <= 3.6**2
    slot = (x >= cx - 1.9) & (x <= cx + 1.9) & (y >= cy - 7.5) & (y <= cy + 4.0)
    lower = (x - cx) ** 2 + (y - (cy - 7.5)) ** 2 <= 1.9**2
    return upper | slot | lower


def rounded_pad_z(x, y, cx, cy, sx, sy, r):
    dx = np.maximum(np.abs(x - cx) - (sx / 2 - r), 0)
    dy = np.maximum(np.abs(y - cy) - (sy / 2 - r), 0)
    return dx * dx + dy * dy <= r * r


def make_grid(spec: PartSpec):
    xs = (np.arange(int(round(spec.width / RESOLUTION_MM))) + 0.5) * RESOLUTION_MM
    ys = (np.arange(int(round(spec.height / RESOLUTION_MM))) + 0.5) * RESOLUTION_MM
    zs = (np.arange(int(round(spec.depth / RESOLUTION_MM))) + 0.5) * RESOLUTION_MM
    return np.meshgrid(xs, ys, zs, indexing="ij")


def text_mask(x, y, text, center_x, center_y, height_mm, bold=True):
    scale = 8
    image_w = int(OUTER_W * scale)
    image_h = int(OUTER_H * scale)
    image = Image.new("L", (image_w, image_h), 0)
    draw = ImageDraw.Draw(image)

    font_name = str(FONT_BOLD if bold else FONT_REGULAR)
    font_size = 8
    while True:
        font = ImageFont.truetype(font_name, font_size)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_h = bbox[3] - bbox[1]
        if text_h / scale >= height_mm:
            break
        font_size += 1

    font = ImageFont.truetype(font_name, max(1, font_size - 1))
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    px = int(center_x * scale - text_w / 2 - bbox[0])
    py = int((OUTER_H - center_y) * scale - text_h / 2 - bbox[1])
    draw.text((px, py), text, 255, font=font)
    mask = np.asarray(image) > 0

    sample_x = np.clip((x[:, :, 0] * scale).astype(int), 0, image_w - 1)
    sample_y = np.clip(((OUTER_H - y[:, :, 0]) * scale).astype(int), 0, image_h - 1)
    sampled = mask[sample_y, sample_x]
    padded = np.pad(sampled, 2, constant_values=False)
    thickened = np.zeros(sampled.shape, dtype=bool)
    for dx in (-2, -1, 0, 1, 2):
        for dy in (-2, -1, 0, 1, 2):
            thickened |= padded[2 + dx : 2 + dx + sampled.shape[0], 2 + dy : 2 + dy + sampled.shape[1]]
    return thickened[:, :, None]


def front_panel(spec: PartSpec):
    x, y, z = make_grid(spec)
    solid = z <= FRONT_BASE_D
    holes = in_box(x, y, z, MATRIX_OPENING)
    holes |= cyl_z(x, y, SONAR_LEFT_X, SONAR_CENTER_Y, SONAR_R)
    holes |= cyl_z(x, y, SONAR_RIGHT_X, SONAR_CENTER_Y, SONAR_R)
    holes |= cyl_z(x, y, SWITCH_CENTER[0], SWITCH_CENTER[1], SWITCH_R)
    for cx, cy in CORNER_SCREWS:
        holes |= cyl_z(x, y, cx, cy, M3_CLEARANCE_R)

    # Light countersink reliefs on the front face for low-profile M3 screw heads.
    for cx, cy in CORNER_SCREWS:
        holes |= cyl_z(x, y, cx, cy, 3.0) & (z <= 1.2)

    return solid & ~holes


def main_body(spec: PartSpec):
    x, y, z = make_grid(spec)
    outer = np.ones(x.shape, dtype=bool)
    cavity = (
        (x >= WALL)
        & (x <= OUTER_W - WALL)
        & (y >= WALL)
        & (y <= OUTER_H - WALL)
        & (z >= -1.0)
        & (z <= spec.depth + 1.0)
    )
    shell = outer & ~cavity

    solid = shell.copy()

    for cx, cy in CORNER_SCREWS:
        post = cyl_z(x, y, cx, cy, BOSS_R)
        bore = cyl_z(x, y, cx, cy, M3_CLEARANCE_R)
        solid |= post
        solid &= ~(bore & (z >= -1.0) & (z <= spec.depth + 1.0))

    # Rear cover ledge and front-panel seating ledge.
    solid |= in_box(x, y, z, Box(WALL, OUTER_W - WALL, WALL, WALL + 2.0, spec.depth - 4.0, spec.depth))
    solid |= in_box(x, y, z, Box(WALL, OUTER_W - WALL, OUTER_H - WALL - 2.0, OUTER_H - WALL, spec.depth - 4.0, spec.depth))
    solid |= in_box(x, y, z, Box(WALL, WALL + 2.0, WALL, OUTER_H - WALL, spec.depth - 4.0, spec.depth))
    solid |= in_box(x, y, z, Box(OUTER_W - WALL - 2.0, OUTER_W - WALL, WALL, OUTER_H - WALL, spec.depth - 4.0, spec.depth))

    # HC-SR04 board rails, placed just outside the updated PCB envelope.
    solid |= in_box(x, y, z, Box(60.0, OUTER_W - WALL + 0.5, SONAR_BOARD_KEEPIN.y0 - 2.0, SONAR_BOARD_KEEPIN.y0 - 0.4, 5.0, BODY_D - 1.0))
    solid |= in_box(x, y, z, Box(60.0, OUTER_W - WALL + 0.5, SONAR_BOARD_KEEPIN.y1 + 0.4, SONAR_BOARD_KEEPIN.y1 + 2.0, 5.0, BODY_D - 1.0))

    # Cable reliefs and USB access on the right wall.
    solid &= ~in_box(x, y, z, USB_OPENING)
    solid &= ~in_box(x, y, z, Box(42.0, 56.0, 34.0, 40.0, 6.0, 28.0))

    # Keep-out volumes for the measured modules and connectors.
    keepouts = in_box(x, y, z, MATRIX_BOARD_KEEPIN)
    keepouts |= in_box(x, y, z, SONAR_BOARD_KEEPIN)
    keepouts |= in_box(x, y, z, SWITCH_PCB_KEEPIN)
    keepouts |= in_box(x, y, z, ESP32_KEEPIN)
    solid &= ~keepouts

    # Rebuild the top-right front-panel screw boss after the HC-SR04 keepout so
    # this mounting point reaches the main-body top like the other corner bosses.
    top_right_cx, top_right_cy = CORNER_SCREWS[3]
    solid |= cyl_z(x, y, top_right_cx, top_right_cy, BOSS_R)
    solid &= ~(cyl_z(x, y, top_right_cx, top_right_cy, M3_CLEARANCE_R) & (z >= -1.0) & (z <= spec.depth + 1.0))

    # HC-SR04 center underside rails at the requested 9 mm-from-top support height.
    sonar_rail_1_y = SONAR_CENTER_Y - SONAR_SUPPORT_RAIL_GAP / 2 - SONAR_SUPPORT_RAIL_WIDTH / 2
    sonar_rail_2_y = SONAR_CENTER_Y + SONAR_SUPPORT_RAIL_GAP / 2 - SONAR_SUPPORT_RAIL_WIDTH / 2
    solid |= in_box(
        x,
        y,
        z,
        Box(SONAR_BOARD_KEEPIN.x0, OUTER_W - WALL + 0.5, sonar_rail_1_y, sonar_rail_1_y + SONAR_SUPPORT_RAIL_WIDTH, SONAR_SUPPORT_Z_TOP - SONAR_SUPPORT_HEIGHT, SONAR_SUPPORT_Z_TOP),
    )
    solid |= in_box(
        x,
        y,
        z,
        Box(SONAR_BOARD_KEEPIN.x0, OUTER_W - WALL + 0.5, sonar_rail_2_y, sonar_rail_2_y + SONAR_SUPPORT_RAIL_WIDTH, SONAR_SUPPORT_Z_TOP - SONAR_SUPPORT_HEIGHT, SONAR_SUPPORT_Z_TOP),
    )
    for tie_x in (SONAR_BOARD_KEEPIN.x0 + 6.0, SONAR_BOARD_KEEPIN.x0 + 22.0, SONAR_BOARD_KEEPIN.x0 + 38.0):
        solid |= in_box(
            x,
            y,
            z,
            Box(tie_x, tie_x + 2.0, sonar_rail_1_y, sonar_rail_2_y + SONAR_SUPPORT_RAIL_WIDTH, SONAR_SUPPORT_Z_TOP - SONAR_SUPPORT_HEIGHT, SONAR_SUPPORT_Z_TOP),
        )
    solid |= in_box(
        x,
        y,
        z,
        Box(SONAR_BOARD_KEEPIN.x0, OUTER_W - WALL + 0.5, sonar_rail_2_y + SONAR_SUPPORT_RAIL_WIDTH, OUTER_H - WALL + 0.5, SONAR_SUPPORT_Z_TOP - SONAR_SUPPORT_HEIGHT, SONAR_SUPPORT_Z_TOP),
    )
    solid |= in_box(
        x,
        y,
        z,
        Box(SONAR_BOARD_KEEPIN.x0, SONAR_BOARD_KEEPIN.x0 + 2.0, ESP32S3_Y1 + 0.2, sonar_rail_1_y, SONAR_SUPPORT_Z_TOP - SONAR_SUPPORT_HEIGHT, SONAR_SUPPORT_Z_TOP),
    )

    # ESP32-S3 support: center lengthwise underside rails and a left stop.
    rail_1_y = ESP32S3_CENTER_Y - ESP32S3_RAIL_GAP / 2 - ESP32S3_RAIL_WIDTH / 2
    rail_2_y = ESP32S3_CENTER_Y + ESP32S3_RAIL_GAP / 2 - ESP32S3_RAIL_WIDTH / 2
    solid |= in_box(x, y, z, Box(ESP32S3_X0 - 2.0, ESP32S3_X0 - 0.4, ESP32S3_Y0 - 2.0, ESP32S3_Y1 + 2.0, 8.0, BODY_D))
    solid |= in_box(x, y, z, Box(ESP32S3_X0 - 1.6, OUTER_W - WALL + 0.5, rail_1_y, rail_1_y + ESP32S3_RAIL_WIDTH, ESP32S3_SUPPORT_Z - 1.6, ESP32S3_SUPPORT_Z))
    solid |= in_box(x, y, z, Box(ESP32S3_X0 - 1.6, OUTER_W - WALL + 0.5, rail_2_y, rail_2_y + ESP32S3_RAIL_WIDTH, ESP32S3_SUPPORT_Z - 1.6, ESP32S3_SUPPORT_Z))
    for tie_x in (ESP32S3_X0 + 8.0, ESP32S3_X0 + 32.0, ESP32S3_X0 + 56.0):
        solid |= in_box(x, y, z, Box(tie_x, tie_x + 2.0, rail_1_y, rail_2_y + ESP32S3_RAIL_WIDTH, ESP32S3_SUPPORT_Z - 1.6, ESP32S3_SUPPORT_Z))

    # Switch-local retaining walls. The switch is moved below the ESP32 bay and
    # gets a shallow backstop at the measured 14 mm assembly depth.
    solid |= in_box(x, y, z, Box(SWITCH_SUPPORT_X0, SWITCH_SUPPORT_X1, 6.2, 7.8, SWITCH_SUPPORT_Z_BOTTOM, BODY_D))
    solid |= in_box(x, y, z, Box(SWITCH_SUPPORT_X0, SWITCH_SUPPORT_X1, 21.4, 22.0, SWITCH_SUPPORT_Z_BOTTOM, BODY_D))
    solid |= in_box(x, y, z, Box(SWITCH_SUPPORT_X0, SWITCH_SUPPORT_X0 + SWITCH_SUPPORT_SIDE_WALL, 7.8, 21.4, SWITCH_SUPPORT_Z_BOTTOM, BODY_D))
    solid |= in_box(x, y, z, Box(SWITCH_SUPPORT_X1 - SWITCH_SUPPORT_SIDE_WALL, SWITCH_SUPPORT_X1, 7.8, 21.4, SWITCH_SUPPORT_Z_BOTTOM, BODY_D))
    solid |= in_box(x, y, z, Box(SWITCH_SUPPORT_X0, SWITCH_SUPPORT_X1, 6.2, 22.0, SWITCH_SUPPORT_Z_BOTTOM, SWITCH_SUPPORT_Z_BOTTOM + 1.6))
    solid |= in_box(x, y, z, Box(SWITCH_SUPPORT_X0, SWITCH_SUPPORT_X0 + 4.0, WALL - 0.5, 6.4, SWITCH_SUPPORT_Z_BOTTOM, BODY_D))
    solid |= in_box(x, y, z, Box(SWITCH_SUPPORT_X1 - 4.0, SWITCH_SUPPORT_X1, WALL - 0.5, 6.4, SWITCH_SUPPORT_Z_BOTTOM, BODY_D))
    solid &= ~in_box(x, y, z, SWITCH_PCB_KEEPIN)

    for cx, cy in MATRIX_MOUNT_HOLES:
        boss = cyl_z(x, y, cx, cy, MATRIX_BOSS_R) & (z >= MATRIX_SUPPORT_Z_BOTTOM) & (z <= MATRIX_SUPPORT_Z_TOP)
        pilot = cyl_z(x, y, cx, cy, MATRIX_PILOT_R) & (z >= MATRIX_SUPPORT_Z_BOTTOM - 1.0) & (z <= MATRIX_SUPPORT_Z_TOP + 1.0)
        solid |= boss
        solid &= ~pilot

    # MAX7219 retaining box: four connected walls around the board area.
    solid |= in_box(
        x,
        y,
        z,
        Box(MATRIX_SUPPORT_OUTER_X0, MATRIX_SUPPORT_INNER_X0, MATRIX_SUPPORT_OUTER_Y0, MATRIX_SUPPORT_OUTER_Y1, MATRIX_SUPPORT_Z_BOTTOM, MATRIX_SUPPORT_Z_TOP),
    )
    solid |= in_box(
        x,
        y,
        z,
        Box(MATRIX_SUPPORT_INNER_X1, MATRIX_SUPPORT_OUTER_X1, MATRIX_SUPPORT_OUTER_Y0, MATRIX_SUPPORT_OUTER_Y1, MATRIX_SUPPORT_Z_BOTTOM, MATRIX_SUPPORT_Z_TOP),
    )
    solid |= in_box(
        x,
        y,
        z,
        Box(MATRIX_SUPPORT_INNER_X0, MATRIX_SUPPORT_INNER_X1, MATRIX_SUPPORT_OUTER_Y0, MATRIX_SUPPORT_INNER_Y0, MATRIX_SUPPORT_Z_BOTTOM, MATRIX_SUPPORT_Z_TOP),
    )
    solid |= in_box(
        x,
        y,
        z,
        Box(MATRIX_SUPPORT_INNER_X0, MATRIX_SUPPORT_INNER_X1, MATRIX_SUPPORT_INNER_Y1, MATRIX_SUPPORT_OUTER_Y1, MATRIX_SUPPORT_Z_BOTTOM, MATRIX_SUPPORT_Z_TOP),
    )

    for _, cy in MATRIX_MOUNT_HOLES[::2]:
        solid |= in_box(x, y, z, Box(MATRIX_SUPPORT_OUTER_X0, MATRIX_SUPPORT_OUTER_X1, cy - 0.8, cy + 0.8, MATRIX_SUPPORT_Z_BOTTOM, MATRIX_SUPPORT_Z_TOP))
        solid |= in_box(x, y, z, Box(WALL - 0.5, MATRIX_SUPPORT_OUTER_X0, cy - 0.8, cy + 0.8, MATRIX_SUPPORT_Z_BOTTOM, MATRIX_SUPPORT_Z_TOP))
    solid |= in_box(x, y, z, Box(WALL - 0.5, MATRIX_SUPPORT_OUTER_X0, MATRIX_SUPPORT_OUTER_Y0, MATRIX_SUPPORT_OUTER_Y0 + 1.6, MATRIX_SUPPORT_Z_BOTTOM, MATRIX_SUPPORT_Z_TOP))
    solid |= in_box(x, y, z, Box(WALL - 0.5, MATRIX_SUPPORT_OUTER_X0, MATRIX_SUPPORT_OUTER_Y1 - 1.6, MATRIX_SUPPORT_OUTER_Y1, MATRIX_SUPPORT_Z_BOTTOM, MATRIX_SUPPORT_Z_TOP))
    solid |= in_box(
        x,
        y,
        z,
        Box(
            MATRIX_SUPPORT_OUTER_X1,
            ESP32S3_X0 - 0.4,
            max(MATRIX_SUPPORT_OUTER_Y0, ESP32S3_Y0 - 2.0),
            min(MATRIX_SUPPORT_OUTER_Y1, ESP32S3_Y1 + 2.0),
            MATRIX_SUPPORT_Z_BOTTOM,
            MATRIX_SUPPORT_Z_TOP,
        ),
    )

    # Vent slots on top and bottom side walls.
    for vx in (48.0, 57.0, 66.0, 75.0, 84.0):
        solid &= ~in_box(x, y, z, Box(vx - 2.0, vx + 2.0, OUTER_H - WALL - 0.2, OUTER_H + 1.0, 11.0, 28.0))
        solid &= ~in_box(x, y, z, Box(vx - 2.0, vx + 2.0, -1.0, WALL + 0.2, 11.0, 28.0))

    return solid


def rear_cover(spec: PartSpec):
    x, y, z = make_grid(spec)
    solid = z <= REAR_VISIBLE_D

    # Inset lip that registers inside the main body.
    lip = (
        ((x >= WALL + 0.4) & (x <= OUTER_W - WALL - 0.4) & (y >= WALL + 0.4) & (y <= OUTER_H - WALL - 0.4) & (z >= REAR_VISIBLE_D))
        & ~((x >= WALL + 2.4) & (x <= OUTER_W - WALL - 2.4) & (y >= WALL + 2.4) & (y <= OUTER_H - WALL - 2.4))
    )
    solid |= lip

    holes = np.zeros(x.shape, dtype=bool)
    for cx, cy in CORNER_SCREWS:
        holes |= cyl_z(x, y, cx, cy, M3_CLEARANCE_R)
        holes |= cyl_z(x, y, cx, cy, 3.0) & (z >= spec.depth - 1.2)

    holes |= keyhole_z(x, y, 40.0, 37.0)
    holes |= keyhole_z(x, y, 72.0, 37.0)

    for vx in (49.0, 57.0, 65.0):
        holes |= rounded_pad_z(x, y, vx, 12.0, 4.0, 14.0, 1.5)
        holes |= rounded_pad_z(x, y, vx, 62.0, 4.0, 14.0, 1.5)

    return solid & ~holes


def emit_face(vertices, triangles, corners):
    start = len(vertices)
    vertices.extend(corners)
    triangles.append((start, start + 1, start + 2))
    triangles.append((start, start + 2, start + 3))


def occupancy_to_mesh(occ: np.ndarray):
    nx, ny, nz = occ.shape
    r = RESOLUTION_MM
    vertices: list[tuple[float, float, float]] = []
    triangles: list[tuple[int, int, int]] = []
    padded = np.pad(occ, 1, constant_values=False)
    dirs = (
        (-1, 0, 0),
        (1, 0, 0),
        (0, -1, 0),
        (0, 1, 0),
        (0, 0, -1),
        (0, 0, 1),
    )
    for ix in range(nx):
        for iy in range(ny):
            filled = np.flatnonzero(occ[ix, iy, :])
            for iz in filled:
                px, py, pz = ix + 1, iy + 1, iz + 1
                for dx, dy, dz in dirs:
                    if padded[px + dx, py + dy, pz + dz]:
                        continue
                    x0, x1 = ix * r, (ix + 1) * r
                    y0, y1 = iy * r, (iy + 1) * r
                    z0, z1 = iz * r, (iz + 1) * r
                    if dx == -1:
                        corners = ((x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0))
                    elif dx == 1:
                        corners = ((x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1))
                    elif dy == -1:
                        corners = ((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1))
                    elif dy == 1:
                        corners = ((x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0))
                    elif dz == -1:
                        corners = ((x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0))
                    else:
                        corners = ((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))
                    emit_face(vertices, triangles, corners)
    return vertices, triangles


def normal(a, b, c):
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    nx = uy * vz - uz * vy
    ny = uz * vx - ux * vz
    nz = ux * vy - uy * vx
    length = sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return nx / length, ny / length, nz / length


def write_binary_stl(path: Path, name: str, vertices, triangles):
    header = f"{name} generated by generate_garage_parking_enclosure.py".encode("ascii")[:80]
    header = header + b" " * (80 - len(header))
    with path.open("wb") as handle:
        handle.write(header)
        handle.write(struct.pack("<I", len(triangles)))
        for tri in triangles:
            a, b, c = (vertices[i] for i in tri)
            nx, ny, nz = normal(a, b, c)
            handle.write(struct.pack("<12fH", nx, ny, nz, *a, *b, *c, 0))


def validate_mesh(vertices, triangles):
    edge_counts: dict[tuple[tuple[float, float, float], tuple[float, float, float]], int] = {}
    for tri in triangles:
        pts = [vertices[i] for i in tri]
        for i in range(3):
            a = pts[i]
            b = pts[(i + 1) % 3]
            edge = tuple(sorted((a, b)))
            edge_counts[edge] = edge_counts.get(edge, 0) + 1
    bad_edges = sum(1 for count in edge_counts.values() if count != 2)
    return {
        "triangles": len(triangles),
        "vertices": len(vertices),
        "unique_edges": len(edge_counts),
        "non_manifold_edges": bad_edges,
    }


def connected_components(occ: np.ndarray):
    sx, sy, sz = occ.shape
    visited = np.zeros(occ.shape, dtype=bool)
    components = []
    true_indices = np.flatnonzero(occ.ravel())

    for flat_start in true_indices:
        start = np.unravel_index(flat_start, occ.shape)
        if visited[start]:
            continue

        queue = deque([start])
        visited[start] = True
        count = 0
        while queue:
            ix, iy, iz = queue.popleft()
            count += 1
            for nx, ny, nz in (
                (ix - 1, iy, iz),
                (ix + 1, iy, iz),
                (ix, iy - 1, iz),
                (ix, iy + 1, iz),
                (ix, iy, iz - 1),
                (ix, iy, iz + 1),
            ):
                if nx < 0 or ny < 0 or nz < 0 or nx >= sx or ny >= sy or nz >= sz:
                    continue
                if occ[nx, ny, nz] and not visited[nx, ny, nz]:
                    visited[nx, ny, nz] = True
                    queue.append((nx, ny, nz))
        components.append(count)

    components.sort(reverse=True)
    return components


def write_notes(report):
    text = f"""# ESP32 Garage Parking-Assist Enclosure

Generated files:

- `front_panel.stl`
- `main_body.stl`
- `rear_cover.stl`
- `source_model.py` is the editable source/model.
- `validation_report.txt` contains manifold checks for each mesh.

Final outside dimensions:

- Assembled width: `{OUTER_W:.1f} mm`
- Assembled height: `{OUTER_H:.1f} mm`
- Assembled depth: `{TOTAL_D:.1f} mm`
- Front panel: `{OUTER_W:.1f} x {OUTER_H:.1f} x {FRONT_D:.1f} mm`
- Main body: `{OUTER_W:.1f} x {OUTER_H:.1f} x {BODY_D:.1f} mm`
- Rear cover: `{OUTER_W:.1f} x {OUTER_H:.1f} x {REAR_D:.1f} mm` total, including a `{REAR_D - REAR_VISIBLE_D:.1f} mm` inset lip that overlaps the main body.

Measured module allowances used:

- MAX7219 FC-16: `32.1 x 32.1 mm`, with a `33.6 x 33.6 mm` front opening and internal cable depth allowance.
- MAX7219 mounting bosses: four internal bosses centered behind the display opening. Your measured mounting-hole edge-to-edge distances are `{MATRIX_MOUNT_EDGE_TO_EDGE_X:.1f} x {MATRIX_MOUNT_EDGE_TO_EDGE_Y:.1f} mm`; with the modeled `{MATRIX_PILOT_R * 2:.1f} mm` pilot holes, the resulting center spacing is `{MATRIX_MOUNT_SPACING_X:.1f} x {MATRIX_MOUNT_SPACING_Y:.1f} mm`. The boss support face is `{MATRIX_SUPPORT_BELOW_BODY_TOP:.1f} mm` below the main-body top/open side, and the support is a `{MATRIX_SUPPORT_HEIGHT:.1f} mm` tall retaining box with a `{MATRIX_SUPPORT_INNER_SIZE:.1f} x {MATRIX_SUPPORT_INNER_SIZE:.1f} mm` inner opening around the board.
- HC-SR04: `{SONAR_BOARD_LENGTH:.1f} x {SONAR_BOARD_WIDTH:.1f} mm` PCB, with two `16 mm` transducer apertures, modeled at `{SONAR_R * 2:.1f} mm` diameter for FDM clearance. The cylinder wall-to-wall gap is `{SONAR_GAP:.1f} mm`, giving `{SONAR_RIGHT_X - SONAR_LEFT_X:.1f} mm` center spacing.
- HC-SR04 support: two center underside rails support the sensor PCB at `{SONAR_SUPPORT_BELOW_BODY_TOP:.1f} mm` below the main-body top/open side, with ribs tying them into the top wall and nearby ESP32/MAX support structure.
- Tactile switch: `{SWITCH_PCB_WIDTH:.1f} x {SWITCH_PCB_LENGTH:.1f} mm` PCB, `{SWITCH_ASSEMBLY_DEPTH:.1f} mm` depth, and a `{SWITCH_R * 2:.1f} mm` front-panel opening for the exposed switch.
- ESP32-S3: `{ESP32S3_LENGTH:.1f} x {ESP32S3_WIDTH:.1f} mm`, with `{ESP32S3_DEPTH_WITH_PINS:.1f} mm` depth allowance for pins/wire connectors.
- ESP32-S3 USB access: right-side opening spans the two USB ports over a `{USB_DUAL_PORT_SPAN:.1f} mm` port group, with added FDM/cable clearance.
- ESP32-S3 support: two center lengthwise underside rails hold the board height while leaving the edge/side-port area clear; a left end stop positions the board lengthwise, and small cross-ties join the two rails so they are structurally supported.
- Tactile switch retention: the switch is in the lower section below the ESP32-S3 bay. Switch-local retaining walls support the `{SWITCH_ASSEMBLY_DEPTH:.1f} mm`-deep switch assembly without extending into the ESP32-S3 area; the printed support wall height is `{SWITCH_SUPPORT_HEIGHT:.1f} mm`.
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

{report}
"""
    (OUTPUT_DIR / "print_notes.md").write_text(text, encoding="utf-8")


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    specs = (
        (PartSpec("front_panel", OUTER_W, OUTER_H, FRONT_D), front_panel),
        (PartSpec("main_body", OUTER_W, OUTER_H, BODY_D), main_body),
        (PartSpec("rear_cover", OUTER_W, OUTER_H, REAR_D), rear_cover),
    )
    report_lines = []
    for spec, maker in specs:
        occ = maker(spec)
        vertices, triangles = occupancy_to_mesh(occ)
        metrics = validate_mesh(vertices, triangles)
        components = connected_components(occ)
        path = OUTPUT_DIR / f"{spec.name}.stl"
        write_binary_stl(path, spec.name, vertices, triangles)
        report_lines.append(
            f"{spec.name}.stl: {metrics['triangles']} triangles, "
            f"{metrics['vertices']} vertices, {metrics['unique_edges']} unique edges, "
            f"{metrics['non_manifold_edges']} non-manifold edges, "
            f"{len(components)} connected solid component(s)"
        )
    report = "\n".join(report_lines)
    (OUTPUT_DIR / "validation_report.txt").write_text(report + "\n", encoding="ascii")
    write_notes(report)
    shutil.copy2(Path(__file__), OUTPUT_DIR / "source_model.py")
    print(report)


if __name__ == "__main__":
    main()
