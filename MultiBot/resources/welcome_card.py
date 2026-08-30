import io
import os
import asyncio
import aiohttp
from PIL import Image, ImageDraw, ImageFont

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
FONT_PATH = os.path.join(FONT_DIR, "tahoma.ttf")
FONT_BOLD = os.path.join(FONT_DIR, "Arial.ttf")

async def fetch_image(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                return await resp.read()
    return None

def make_circle(im, size):
    mask = Image.new("L", size, 0)
    d = ImageDraw.Draw(mask)
    d.ellipse((0, 0) + size, fill=255)
    output = Image.new("RGBA", size, (0, 0, 0, 0))
    output.paste(im, (0, 0), mask)
    return output

BG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "background.png")

async def generate_welcome_card(avatar_url, server_icon_url, server_name, member_name, member_count):
    bg_color = (43, 45, 49)
    accent = (88, 101, 242)
    w, h = 800, 300

    img = Image.new("RGBA", (w, h), bg_color)
    if os.path.exists(BG_PATH):
        try:
            bg = Image.open(BG_PATH).convert("RGBA")
            bg = bg.resize((w, h))
            img.paste(bg, (0, 0), bg)
        except:
            pass
    draw = ImageDraw.Draw(img)

    # Semi-transparent overlay for readability
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 100))
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    font_large = ImageFont.truetype(FONT_PATH, 36) if os.path.exists(FONT_PATH) else ImageFont.load_default()
    font_medium = ImageFont.truetype(FONT_PATH, 24) if os.path.exists(FONT_PATH) else ImageFont.load_default()
    font_small = ImageFont.truetype(FONT_PATH, 18) if os.path.exists(FONT_PATH) else ImageFont.load_default()

    svg_icon = None
    if server_icon_url:
        data = await fetch_image(server_icon_url)
        if data:
            try:
                svg_icon = Image.open(io.BytesIO(data)).convert("RGBA")
                svg_icon = svg_icon.resize((48, 48))
                svg_icon = make_circle(svg_icon, (48, 48))
            except:
                svg_icon = None

    if svg_icon:
        img.paste(svg_icon, (25, 20), svg_icon)
    else:
        draw.rectangle([25, 20, 73, 68], fill=accent, outline=None)

    draw.text((85, 28), f"WELCOME TO", fill=accent, font=font_medium)
    draw.text((85, 50), server_name.upper(), fill=(255,255,255), font=font_large)

    avatar = None
    if avatar_url:
        data = await fetch_image(avatar_url)
        if data:
            try:
                avatar = Image.open(io.BytesIO(data)).convert("RGBA")
                avatar = avatar.resize((140, 140))
                avatar = make_circle(avatar, (140, 140))
            except:
                avatar = None

    if avatar:
        img.paste(avatar, (580, 70), avatar)
    else:
        draw.ellipse([580, 70, 720, 210], fill=accent)

    if avatar:
        y_text = 230
    else:
        y_text = 180

    try:
        bbox = draw.textbbox((0, 0), member_name, font=font_large)
        tw = bbox[2] - bbox[0]
    except:
        tw = len(member_name) * 20
    draw.text(((w - tw) // 2, y_text), member_name, fill=(255,255,255), font=font_large)

    badge_text = f"Member #{member_count}"
    try:
        bbox = draw.textbbox((0, 0), badge_text, font=font_small)
        bw = bbox[2] - bbox[0]
    except:
        bw = len(badge_text) * 10
    badge_x = (w - bw) // 2
    badge_y = y_text + 45

    pad = 10
    draw.rounded_rectangle(
        [badge_x - pad, badge_y - 4, badge_x + bw + pad, badge_y + 20],
        radius=12, fill=accent
    )
    draw.text((badge_x, badge_y), badge_text, fill=(255,255,255), font=font_small)

    buf = io.BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return buf
