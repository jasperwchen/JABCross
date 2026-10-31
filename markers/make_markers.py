"""Generate printable ArUco markers (one per US Letter page) into markers/markers.pdf."""
from pathlib import Path

import cv2
from PIL import Image, ImageDraw, ImageFont

COUNT = 12  # marker IDs 0..11
DPI = 300
PAGE_W, PAGE_H = int(8.5 * DPI), int(11 * DPI)
MARKER_PX = 1770  # 4x4 bits + 1-bit border = 6 cells, so a multiple of 6. 1770 px at 300 DPI = 15.0 cm
MARKER_CM = round(MARKER_PX / DPI * 2.54, 1)

aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
big = ImageFont.load_default(size=110)
small = ImageFont.load_default(size=45)

pages = []
for marker_id in range(COUNT):
    marker = cv2.aruco.generateImageMarker(aruco_dict, marker_id, MARKER_PX)
    page = Image.new("L", (PAGE_W, PAGE_H), 255)
    x = (PAGE_W - MARKER_PX) // 2
    y = 450
    page.paste(Image.fromarray(marker), (x, y))

    draw = ImageDraw.Draw(page)
    draw.text((PAGE_W // 2, 220), f"JabCross marker {marker_id}", font=big, fill=0, anchor="mm")
    below = y + MARKER_PX + 150
    draw.text((PAGE_W // 2, below), "Location: ______________________", font=small, fill=0, anchor="mm")
    draw.text(
        (PAGE_W // 2, below + 150),
        f"Print at 100% / Actual size. Black square must measure {MARKER_CM} cm.",
        font=small, fill=0, anchor="mm",
    )
    draw.text((PAGE_W // 2, below + 220), "ArUco DICT_4X4_50", font=small, fill=0, anchor="mm")
    pages.append(page)

out = Path(__file__).parent / "markers.pdf"
pages[0].save(out, save_all=True, append_images=pages[1:], resolution=DPI)
print(f"wrote {out} ({COUNT} pages, marker side {MARKER_CM} cm)")
