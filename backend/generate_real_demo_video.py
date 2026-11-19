"""
ColdBridge AI - Fast 15-Second Real Prototype Demo Video Generator
Uses actual screenshots captured directly from the live ColdBridge AI web application
via Chrome DevTools Protocol (CDP).

Total Duration: 15.0 Seconds (24 FPS = 360 frames)
Chapters (3.0s each):
  0:00 - 0:03  Login
  0:03 - 0:06  Add Batch
  0:06 - 0:09  SRI Score
  0:09 - 0:12  Best Match
  0:12 - 0:15  Booking
"""

import sys
import os
import math
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

WIDTH = 1280
HEIGHT = 720
FPS = 24
TOTAL_DURATION = 15
TOTAL_FRAMES = FPS * TOTAL_DURATION  # 360 frames

CHAPTERS = [
    {"label": "Login",      "start": 0,  "end": 3},
    {"label": "Add Batch",  "start": 3,  "end": 6},
    {"label": "SRI Score",  "start": 6,  "end": 9},
    {"label": "Best Match", "start": 9,  "end": 12},
    {"label": "Booking",    "start": 12, "end": 15},
]

# Color Palette
NAV_BG = (15, 23, 42)
BORDER_COLOR = (226, 232, 240)
PRIMARY_BLUE = (2, 132, 199)
EMERALD_GREEN = (16, 185, 129)
DANGER_RED = (239, 68, 68)
TEXT_MAIN = (15, 23, 42)
TEXT_MUTED = (148, 163, 184)

def load_font(size, bold=False):
    font_path = "C:\\Windows\\Fonts\\segoeuib.ttf" if bold else "C:\\Windows\\Fonts\\segoeui.ttf"
    if not os.path.exists(font_path):
        font_path = "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf"
    try:
        return ImageFont.truetype(font_path, size)
    except Exception:
        return ImageFont.load_default()

FONT_HEADER = load_font(18, bold=True)
FONT_BODY_BOLD = load_font(15, bold=True)
FONT_SMALL = load_font(13, bold=False)
FONT_SMALL_BOLD = load_font(13, bold=True)
FONT_TINY = load_font(11, bold=True)

# Load Real Screenshots
SCREEN_DIR = Path("backend/captured_screens")
SCREENS = {
    "login": Image.open(SCREEN_DIR / "01_login.png").convert("RGB"),
    "add": Image.open(SCREEN_DIR / "02_add_produce.png").convert("RGB"),
    "sri": Image.open(SCREEN_DIR / "03_sri_batches.png").convert("RGB"),
    "match": Image.open(SCREEN_DIR / "05_matching.png").convert("RGB"),
    "book": Image.open(SCREEN_DIR / "06_bookings.png").convert("RGB"),
}

# Pre-scale real screenshots to fit center canvas (1280 x 590)
TARGET_AREA_H = 590
PROCESSED_SCREENS = {}
for k, img in SCREENS.items():
    # Scale to fill width or height nicely
    aspect = img.width / img.height
    new_h = TARGET_AREA_H
    new_w = int(new_h * aspect)
    if new_w > WIDTH:
        new_w = WIDTH
        new_h = int(new_w / aspect)
    
    scaled = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (WIDTH, TARGET_AREA_H), (241, 245, 249))
    paste_x = (WIDTH - new_w) // 2
    paste_y = (TARGET_AREA_H - new_h) // 2
    canvas.paste(scaled, (paste_x, paste_y))
    PROCESSED_SCREENS[k] = canvas

def draw_top_nav(draw, current_time_sec):
    # Dark app bar (0 to 56)
    draw.rectangle([(0, 0), (WIDTH, 56)], fill=NAV_BG)
    
    # Brand
    draw.text((24, 15), "❄️ ColdBridge AI", font=FONT_HEADER, fill=(255, 255, 255))
    
    # Live node status pill
    draw.rounded_rectangle([(195, 16), (310, 40)], radius=12, fill=(16, 185, 129, 30), outline=(16, 185, 129), width=1)
    draw.ellipse([(206, 25), (214, 33)], fill=(16, 185, 129))
    draw.text((222, 21), "LIVE PROTOTYPE", font=FONT_TINY, fill=(16, 185, 129))
    
    # User pill
    draw.rounded_rectangle([(WIDTH - 290, 14), (WIDTH - 24, 42)], radius=14, fill=(30, 41, 59))
    draw.text((WIDTH - 276, 20), "🧑‍🌾 Ramesh Patil • Dindori, Nashik", font=FONT_SMALL, fill=(203, 213, 225))
    
    # Chapter Progress Bar (56 to 84)
    draw.rectangle([(0, 56), (WIDTH, 84)], fill=(255, 255, 255))
    draw.line([(0, 84), (WIDTH, 84)], fill=BORDER_COLOR, width=1)
    
    col_w = WIDTH / len(CHAPTERS)
    cur_ch_idx = min(int(current_time_sec // 3.0), len(CHAPTERS) - 1)
    
    for i, ch in enumerate(CHAPTERS):
        cx1 = int(i * col_w)
        cx2 = int((i + 1) * col_w)
        is_active = (i == cur_ch_idx)
        is_past = (i < cur_ch_idx)
        
        if is_active:
            draw.rectangle([(cx1, 56), (cx2, 83)], fill=(240, 249, 255))
            ch_prog = (current_time_sec - ch["start"]) / 3.0
            fill_x = cx1 + int((cx2 - cx1) * ch_prog)
            draw.rectangle([(cx1, 80), (fill_x, 84)], fill=PRIMARY_BLUE)
        elif is_past:
            draw.rectangle([(cx1, 81), (cx2, 84)], fill=EMERALD_GREEN)
            
        color = PRIMARY_BLUE if is_active else (EMERALD_GREEN if is_past else (100, 116, 139))
        draw.text((cx1 + 20, 63), f"{i+1}. {ch['label']}", font=FONT_SMALL_BOLD if is_active else FONT_SMALL, fill=color)

def draw_bottom_narration(draw, text, subtext, current_time_sec):
    bar_h = 58
    y1 = HEIGHT - bar_h - 12
    y2 = HEIGHT - 12
    x1 = 28
    x2 = WIDTH - 28
    
    draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=10, fill=(15, 23, 42), outline=(51, 65, 85), width=1)
    
    # Status green dot
    draw.ellipse([(x1 + 18, y1 + 22), (x1 + 28, y1 + 32)], fill=EMERALD_GREEN)
    
    draw.text((x1 + 38, y1 + 10), text, font=FONT_BODY_BOLD, fill=(255, 255, 255))
    draw.text((x1 + 38, y1 + 32), subtext, font=FONT_SMALL, fill=TEXT_MUTED)
    
    # Timer
    sec_int = int(current_time_sec)
    time_str = f"00:{sec_int:02d} / 00:15"
    draw.rounded_rectangle([(x2 - 110, y1 + 14), (x2 - 16, y1 + 44)], radius=6, fill=(30, 41, 59))
    draw.text((x2 - 100, y1 + 21), time_str, font=FONT_SMALL_BOLD, fill=(56, 189, 248))

def draw_cursor(draw, x, y, clicking=False):
    pts = [(x, y), (x, y + 16), (x + 4, y + 12), (x + 8, y + 20), (x + 12, y + 18), (x + 7, y + 11), (x + 12, y + 11)]
    if clicking:
        draw.ellipse([(x - 10, y - 10), (x + 10, y + 10)], outline=PRIMARY_BLUE, width=2)
    draw.polygon(pts, fill=(15, 23, 42), outline=(255, 255, 255))

def render_frame(f, t):
    im = Image.new("RGB", (WIDTH, HEIGHT), (241, 245, 249))
    
    # Determine Active Chapter & Screen
    if t < 3.0:
        # Chapter 1: Login
        screen_img = PROCESSED_SCREENS["login"]
        im.paste(screen_img, (0, 84))
        draw = ImageDraw.Draw(im)
        draw_top_nav(draw, t)
        
        # Cursor moves to Sign In button
        local_t = t
        cx = 640
        cy = 440
        clicking = (local_t >= 1.2 and local_t < 1.8)
        draw_cursor(draw, cx, cy, clicking=clicking)
        
        draw_bottom_narration(
            draw,
            "Step 1/5: Farmer Authentication & Maharashtra Session Entry",
            "Real login interface • Direct 1-click access to Ramesh Patil's farmgate dashboard",
            t
        )
    elif t < 6.0:
        # Chapter 2: Add Batch
        screen_img = PROCESSED_SCREENS["add"]
        im.paste(screen_img, (0, 84))
        draw = ImageDraw.Draw(im)
        draw_top_nav(draw, t)
        
        local_t = t - 3.0
        cx = 580
        cy = 510
        clicking = (local_t >= 1.5 and local_t < 2.0)
        draw_cursor(draw, cx, cy, clicking=clicking)
        
        draw_bottom_narration(
            draw,
            "Step 2/5: Log Harvest Batch • 500 kg Kesar Mango at 32°C Field Heat",
            "Field temperature & orchard coordinates captured • Triggers automated SRI analysis",
            t
        )
    elif t < 9.0:
        # Chapter 3: SRI Score
        screen_img = PROCESSED_SCREENS["sri"]
        im.paste(screen_img, (0, 84))
        draw = ImageDraw.Draw(im)
        draw_top_nav(draw, t)
        
        local_t = t - 6.0
        cx = 750
        cy = 320
        draw_cursor(draw, cx, cy, clicking=False)
        
        draw_bottom_narration(
            draw,
            "Step 3/5: Solar-Refrigeration-Index (SRI) AI Spoilage Assessment",
            "SRI 74.5/100 (HIGH RISK) • 2.8x accelerated degradation • 4.2h critical window",
            t
        )
    elif t < 12.0:
        # Chapter 4: Best Match
        screen_img = PROCESSED_SCREENS["match"]
        im.paste(screen_img, (0, 84))
        draw = ImageDraw.Draw(im)
        draw_top_nav(draw, t)
        
        local_t = t - 9.0
        cx = 920
        cy = 310
        clicking = (local_t >= 1.5 and local_t < 2.2)
        draw_cursor(draw, cx, cy, clicking=clicking)
        
        draw_bottom_narration(
            draw,
            "Step 4/5: AI Multi-Criteria Cooling Matchmaker Ranks Candidates",
            "Rank #1: SolarVan Alpha (18 min ETA, 95% solar clean energy, ₹1.50/kg/day)",
            t
        )
    else:
        # Chapter 5: Booking
        screen_img = PROCESSED_SCREENS["book"]
        im.paste(screen_img, (0, 84))
        draw = ImageDraw.Draw(im)
        draw_top_nav(draw, t)
        
        local_t = t - 12.0
        cx = 880
        cy = 380
        draw_cursor(draw, cx, cy, clicking=False)
        
        draw_bottom_narration(
            draw,
            "Step 5/5: Confirmed Allocation & Real-Time Van Dispatch",
            "Booking #CB-2026-8921 verified • Driver OTP 4829 • 500 kg produce saved!",
            t
        )
        
    return im

def main():
    assets_dir = Path("frontend/assets")
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    output_mp4 = assets_dir / "prototype-demo.mp4"
    output_poster = assets_dir / "prototype-poster.jpg"
    
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    print(f"Using ffmpeg: {ffmpeg_exe}")
    print(f"Target: {output_mp4.resolve()}")
    print(f"Generating 15.0-second video ({TOTAL_FRAMES} frames @ {FPS}fps)...")
    
    # Save Poster Thumbnail (at Best Match step)
    poster_im = render_frame(0, 10.5)
    poster_im.save(output_poster, "JPEG", quality=92)
    print(f"Saved real prototype poster: {output_poster}")
    
    cmd = [
        ffmpeg_exe,
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-profile:v", "high",
        "-level", "4.0",
        "-preset", "veryfast",
        "-crf", "22",
        "-movflags", "+faststart",
        str(output_mp4)
    ]
    
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    
    for f in range(TOTAL_FRAMES):
        t = f / FPS
        frame_img = render_frame(f, t)
        proc.stdin.write(frame_img.tobytes())
        if f % 72 == 0:
            print(f"  Rendered {f}/{TOTAL_FRAMES} frames ({int(t)}s / 15s)...")
            
    proc.stdin.close()
    stderr = proc.stderr.read()
    proc.wait()
    
    if proc.returncode == 0:
        size_kb = output_mp4.stat().st_size / 1024
        print(f"SUCCESS: 15-second real prototype video created! Size: {size_kb:.1f} KB")
    else:
        print(f"Error: {stderr.decode('utf-8', errors='ignore')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
