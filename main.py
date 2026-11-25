#!/usr/bin/env python3
"""news-image-20261125: Sum up 25 November 2026 world news in one image.

Draws a clean newspaper front page (1024x1024 PNG) with the day's real
world news and writes it to /output/entry.png. Fully deterministic: no
network, no clock, no randomness, fixed fonts and fixed layout, so two
runs produce identical bytes. If Pillow is unavailable, it falls back to
copying the prebuilt entry.png shipped in this repository.
"""

import os
import shutil
import sys

OUT_PATH = "/output/entry.png"
HERE = os.path.dirname(os.path.abspath(__file__))
SHIPPED = os.path.join(HERE, "entry.png")

try:
    from PIL import Image, ImageDraw, ImageFont
    HAVE_PIL = True
except Exception:
    HAVE_PIL = False

# ---------------------------------------------------------------- palette
NAVY = (20, 33, 61)
NAVY_LIGHT = (32, 52, 88)
GOLD = (201, 162, 39)
GOLD_LIGHT = (232, 196, 90)
PAPER = (247, 244, 236)
CARD = (255, 255, 255)
BORDER = (216, 210, 194)
INK = (26, 26, 26)
MUTED = (90, 86, 76)
RED = (180, 35, 24)
SKY = (38, 64, 110)
TINT_BLUE = (226, 233, 244)
TINT_GOLD = (247, 236, 203)
TINT_RED = (248, 228, 224)
TINT_GREEN = (226, 240, 228)

W = H = 1024

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]


def load_font(size, bold):
    """First usable TTF from the candidate list, else PIL's default font."""
    for path in FONT_CANDIDATES:
        is_bold = "Bold" in path
        if is_bold != bold:
            continue
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def wrap(draw, text, font, max_width):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    lines, cur = [], ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if draw.textlength(trial, font=font) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def text_block(draw, x, y, lines, font, fill, leading):
    """Draw lines top to bottom; returns the y just below the last line."""
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += leading
    return y


# ------------------------------------------------------------------- icons
def icon_skyline(draw, x, y, w, h):
    """Riyadh towers at dusk with a strike burst over the tallest tower.

    Draws inside the full panel (x, y, w, h); the caller paints the sky.
    """
    import math
    # ground line
    draw.rectangle([x, y + h - 10, x + w, y + h], fill=(24, 40, 72))
    # towers, left to right, tallest in the middle-right
    towers = [(8, 120, 34), (48, 88, 34), (88, 150, 40), (134, 60, 44),
              (184, 110, 34), (224, 140, 36), (266, 96, 22)]
    for tx, top, tw in towers:
        draw.rectangle([x + tx, y + top, x + tx + tw, y + h - 10], fill=NAVY)
    # lit windows on the tallest tower
    for wy in range(y + 68, y + h - 16, 12):
        for wx in (x + 142, x + 156):
            draw.rectangle([wx, wy, wx + 6, wy + 5], fill=GOLD_LIGHT)
    for wy in range(y + 96, y + h - 16, 12):
        draw.rectangle([x + 56, wy, x + 62, wy + 5], fill=GOLD_LIGHT)
    # strike burst above the tallest tower
    cx, cy = x + 156, y + 34
    pts = []
    for i in range(16):
        ang = math.pi * i / 8
        r = 26 if i % 2 == 0 else 12
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    draw.polygon(pts, fill=(232, 120, 40))
    draw.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=(255, 214, 90))
    # smoke wisps drifting from the burst
    draw.ellipse([x + 176, y + 26, x + 200, y + 38], fill=(180, 180, 175))
    draw.ellipse([x + 190, y + 14, x + 212, y + 26], fill=(205, 205, 200))
    # stars
    for sx, sy in [(x + 20, y + 16), (x + 250, y + 20), (x + 280, y + 52),
                   (x + 60, y + 44)]:
        draw.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=GOLD_LIGHT)


def icon_scales(draw, x, y, s):
    """Scales of justice (court verdict)."""
    draw.rectangle([x, y, x + s, y + s], fill=TINT_RED)
    cx = x + s // 2
    draw.line([cx, y + 12, cx, y + s - 14], fill=NAVY, width=4)
    draw.line([x + 12, y + 20, x + s - 12, y + 20], fill=NAVY, width=4)
    draw.line([x + 14, y + 20, x + 12, y + 44], fill=NAVY, width=3)
    draw.line([x + s - 14, y + 20, x + s - 12, y + 44], fill=NAVY, width=3)
    draw.polygon([(x + 4, y + 44), (x + 20, y + 44), (cx - 8, y + 52)], fill=RED)
    draw.polygon([(x + s - 20, y + 44), (x + s - 4, y + 44), (cx + 8, y + 52)], fill=RED)
    draw.rectangle([x + 14, y + s - 12, x + s - 14, y + s - 8], fill=NAVY)


def icon_chip(draw, x, y, s):
    """Microchip (Nvidia / AI)."""
    draw.rectangle([x, y, x + s, y + s], fill=TINT_GOLD)
    # pins
    for i in range(3):
        px = x + 16 + i * 18
        draw.line([px, y + 6, px, y + 14], fill=NAVY, width=3)
        draw.line([px, y + s - 14, px, y + s - 6], fill=NAVY, width=3)
        py = y + 16 + i * 18
        draw.line([x + 6, py, x + 14, py], fill=NAVY, width=3)
        draw.line([x + s - 14, py, x + s - 6, py], fill=NAVY, width=3)
    draw.rounded_rectangle([x + 16, y + 16, x + s - 16, y + s - 16],
                           radius=6, fill=NAVY)
    draw.rounded_rectangle([x + 28, y + 28, x + s - 28, y + s - 28],
                           radius=4, fill=GOLD)
    draw.text((x + s // 2 - 4, y + s // 2 - 9), "AI",
              font=load_font(16, True), fill=NAVY)


def icon_rocket(draw, x, y, s):
    """Rocket lifting off (Shenzhou-24)."""
    draw.rectangle([x, y, x + s, y + s], fill=TINT_BLUE)
    cx = x + s // 2
    # flame
    draw.polygon([(cx - 8, y + s - 22), (cx + 8, y + s - 22),
                  (cx, y + s - 6)], fill=(232, 120, 40))
    # fins
    draw.polygon([(cx - 12, y + s - 34), (cx - 22, y + s - 16),
                  (cx - 12, y + s - 18)], fill=RED)
    draw.polygon([(cx + 12, y + s - 34), (cx + 22, y + s - 16),
                  (cx + 12, y + s - 18)], fill=RED)
    # body
    draw.rounded_rectangle([cx - 12, y + 12, cx + 12, y + s - 22],
                           radius=10, fill=(255, 255, 255))
    draw.ellipse([cx - 7, y + 22, cx + 7, y + 36], fill=SKY)
    draw.rectangle([cx - 12, y + 44, cx + 12, y + 48], fill=RED)
    # stars
    for sx, sy in [(x + 10, y + 12), (x + s - 12, y + 18), (x + 14, y + s - 16)]:
        draw.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=GOLD_LIGHT)


def icon_search(draw, x, y, s):
    """Magnifier over a building (corruption probe)."""
    draw.rectangle([x, y, x + s, y + s], fill=TINT_GREEN)
    # building
    draw.rectangle([x + 12, y + 26, x + 40, y + s - 10], fill=NAVY_LIGHT)
    for wy in range(y + 32, y + s - 14, 10):
        for wx in (x + 17, x + 27):
            draw.rectangle([wx, wy, wx + 5, wy + 5], fill=GOLD_LIGHT)
    # magnifier
    draw.ellipse([x + 34, y + 8, x + 62, y + 36], outline=NAVY, width=5)
    draw.line([x + 56, y + 30, x + s - 8, y + s - 20], fill=NAVY, width=5)


# ------------------------------------------------------------------- build
def build():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    f_mast = load_font(62, True)
    f_date = load_font(24, True)
    f_date2 = load_font(20, False)
    f_kicker = load_font(19, True)
    f_lead_head = load_font(38, True)
    f_lead_body = load_font(20, False)
    f_card_head = load_font(23, True)
    f_card_body = load_font(17, False)
    f_section = load_font(21, True)
    f_ticker = load_font(19, False)
    f_foot = load_font(19, False)

    # ---- masthead
    d.rectangle([0, 0, W, 104], fill=NAVY)
    d.text((40, 20), "THE WORLD TODAY", font=f_mast, fill=(255, 255, 255))
    d.text((W - 40 - d.textlength("WEDNESDAY", font=f_date), 22),
           "WEDNESDAY", font=f_date, fill=GOLD_LIGHT)
    d.text((W - 40 - d.textlength("25 NOVEMBER 2026", font=f_date2), 54),
           "25 NOVEMBER 2026", font=f_date2, fill=(255, 255, 255))
    d.rectangle([0, 104, W, 110], fill=GOLD)

    # ---- dateline strip
    d.text((40, 120), "THE DAY'S WORLD NEWS — AT A GLANCE",
           font=f_section, fill=NAVY)
    d.text((W - 40 - d.textlength("6 STORIES • 1 DAY", font=f_section), 120),
           "6 STORIES • 1 DAY", font=f_section, fill=MUTED)

    # ---- lead story card
    d.rounded_rectangle([40, 150, 984, 412], radius=8, fill=CARD,
                        outline=BORDER, width=2)
    tx, ty = 64, 170
    d.text((tx, ty), "MIDDLE EAST  •  LEAD STORY", font=f_kicker, fill=RED)
    head_lines = wrap(d, "RIYADH HIT AGAIN BY HOUTHI STRIKE",
                      f_lead_head, 576)
    y = text_block(d, tx, ty + 30, head_lines, f_lead_head, INK, 46)
    body = ("Yemen's Houthis struck a tower in Riyadh's financial district "
            "for the second time in under a week. Eleven people were "
            "injured, including two Indians and three Nepalese; India "
            "condemned the attack.")
    body_lines = wrap(d, body, f_lead_body, 576)
    text_block(d, tx, y + 12, body_lines, f_lead_body, (58, 56, 50), 26)
    # lead illustration: skyline panel filling its full frame
    d.rectangle([664, 174, 960, 388], fill=TINT_BLUE)
    icon_skyline(d, 664, 174, 296, 214)

    # ---- four story cards (2 x 2)
    cards = [
        ("HUAWEI CONVICTED IN US COURT",
         "A US jury finds the Chinese tech giant guilty of conspiring to "
         "steal trade secrets, in a sprawling trial over its Iran business.",
         icon_scales),
        ("NVIDIA'S HUANG BACK AS CEO",
         "Jensen Huang is reinstated after Trump and Vance assure the board "
         "he is no security risk; he apologises to staff and says he is in "
         "therapy.",
         icon_chip),
        ("SHENZHOU-24 LIFTS OFF",
         "China launches its Shenzhou-24 mission carrying a Pakistani "
         "national — the first foreign astronaut to visit China's space "
         "station.",
         icon_rocket),
        ("CHINA PROBES TOP SHANGHAI OFFICIAL",
         "Politburo member Chen Jining, the party chief of Shanghai, is put "
         "under investigation for 'suspected severe violations' of "
         "discipline.",
         icon_search),
    ]
    card_w, card_h = 472, 164
    for i, (head, body_text, icon_fn) in enumerate(cards):
        cx = 40 + (i % 2) * (card_w + 16)
        cy = 424 + (i // 2) * (card_h + 16)
        d.rounded_rectangle([cx, cy, cx + card_w, cy + card_h], radius=8,
                            fill=CARD, outline=BORDER, width=2)
        icon_fn(d, cx + 16, cy + 16, 72)
        hx = cx + 104
        hl = wrap(d, head, f_card_head, card_w - 120)
        y = text_block(d, hx, cy + 16, hl, f_card_head, INK, 28)
        bl = wrap(d, body_text, f_card_body, card_w - 120)
        text_block(d, hx, y + 6, bl, f_card_body, (58, 56, 50), 21)

    # ---- also today
    d.text((40, 784), "ALSO TODAY", font=f_section, fill=NAVY)
    d.rectangle([192, 797, 984, 799], fill=GOLD)
    ticker = [
        "CIA, ODNI hit by cyber breach, NYT reports",
        "Gas blast at Hanoi restaurant kills seven",
        "Gunmen take 25 hostage at Colombia store",
        "Shein to pay $100m to settle US claims",
        "Senegal win Africa Cup back after CAS ruling",
        "UN: five women killed hourly by relatives",
    ]
    for i, item in enumerate(ticker):
        col, row = i % 2, i // 2
        ix = 40 + col * 484
        iy = 818 + row * 38
        d.ellipse([ix, iy + 6, ix + 9, iy + 15], fill=GOLD)
        d.text((ix + 20, iy), item, font=f_ticker, fill=INK)

    # ---- footer
    d.rectangle([0, 948, W, H], fill=NAVY)
    foot = "Compiled from wire reports  •  Wednesday, 25 November 2026"
    d.text(((W - d.textlength(foot, font=f_foot)) // 2, 972),
           foot, font=f_foot, fill=(255, 255, 255))
    return img


def main():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    if HAVE_PIL:
        img = build()
        img.save(OUT_PATH, format="PNG")
    else:
        shutil.copyfile(SHIPPED, OUT_PATH)
    print("wrote", OUT_PATH)


if __name__ == "__main__":
    main()
