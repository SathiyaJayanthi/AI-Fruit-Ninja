"""
Asset generator for AI Fruit Ninja.
Creates high-definition fruit sprites (whole and halves), bombs, effects, and backgrounds,
and saves a comprehensive asset manifest.
"""

import json
import math
import os
from PIL import Image, ImageDraw

from config import ASSETS_DIR, FRUITS_CONFIG


def generate_fruit_assets():
    fruits_dir = os.path.join(ASSETS_DIR, "fruits")
    sliced_dir = os.path.join(ASSETS_DIR, "sliced_fruits")
    bombs_dir = os.path.join(ASSETS_DIR, "bombs")
    bg_dir = os.path.join(ASSETS_DIR, "backgrounds")
    effects_dir = os.path.join(ASSETS_DIR, "effects")

    for d in [fruits_dir, sliced_dir, bombs_dir, bg_dir, effects_dir]:
        os.makedirs(d, exist_ok=True)

    manifest = {"fruits": {}, "sliced_fruits": {}, "bombs": {}, "sounds": {}, "backgrounds": {}}

    size = 140
    center = (size // 2, size // 2)

    for key, cfg in FRUITS_CONFIG.items():
        r = cfg["radius"]
        outer_c = cfg["color_outer"]
        inner_c = cfg["color_inner"]
        seed_c = cfg["seed_color"]

        # --- Whole Fruit ---
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Outer rim
        draw.ellipse([center[0] - r, center[1] - r, center[0] + r, center[1] + r], fill=outer_c)
        # Inner edible pulp
        inner_r = int(r * 0.88)
        draw.ellipse([center[0] - inner_r, center[1] - inner_r, center[0] + inner_r, center[1] + inner_r], fill=inner_c)

        # Fruit-specific details
        if key == "watermelon":
            for deg in range(0, 360, 45):
                rad = math.radians(deg)
                sx = center[0] + int(math.cos(rad) * (r - 4))
                sy = center[1] + int(math.sin(rad) * (r - 4))
                draw.ellipse([sx - 4, sy - 4, sx + 4, sy + 4], fill=(15, 80, 25))
            for so in [(-15, -10), (12, -14), (-8, 15), (14, 12), (0, 2)]:
                sp = (center[0] + so[0] * r // 45, center[1] + so[1] * r // 45)
                draw.ellipse([sp[0] - 2, sp[1] - 4, sp[0] + 2, sp[1] + 4], fill=seed_c)

        elif key == "orange":
            for deg in range(0, 360, 45):
                rad = math.radians(deg)
                ex = center[0] + int(math.cos(rad) * (inner_r - 4))
                ey = center[1] + int(math.sin(rad) * (inner_r - 4))
                draw.line([center, (ex, ey)], fill=(255, 235, 190), width=2)

        elif key == "strawberry":
            for sx, sy in [(-10, -10), (10, -8), (-6, 6), (8, 8), (0, -18), (0, 16)]:
                draw.ellipse([center[0] + sx - 1, center[1] + sy - 2, center[0] + sx + 1, center[1] + sy + 2], fill=seed_c)

        # Gloss highlight
        draw.ellipse([center[0] - r // 2 - 4, center[1] - r // 2 - 4, center[0] - r // 2 + 10, center[1] - r // 2 + 10], fill=(255, 255, 255, 140))

        whole_path = os.path.join(fruits_dir, f"{key}.png")
        img.save(whole_path, "PNG")
        manifest["fruits"][key] = {
            "path": f"assets/fruits/{key}.png",
            "name": cfg["name"],
            "radius": r,
            "points": cfg["points"],
        }

        # --- Sliced Fruit Half 1 (Top half: 180 to 360 in Pillow) ---
        img_h1 = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw_h1 = ImageDraw.Draw(img_h1)
        draw_h1.pieslice([center[0] - r, center[1] - r, center[0] + r, center[1] + r], 180, 360, fill=outer_c)
        draw_h1.pieslice([center[0] - inner_r, center[1] - inner_r, center[0] + inner_r, center[1] + inner_r], 180, 360, fill=inner_c)
        draw_h1.line([(center[0] - r, center[1]), (center[0] + r, center[1])], fill=(255, 255, 255, 210), width=3)
        h1_path = os.path.join(sliced_dir, f"{key}_half_1.png")
        img_h1.save(h1_path, "PNG")

        # --- Sliced Fruit Half 2 (Bottom half: 0 to 180 in Pillow) ---
        img_h2 = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw_h2 = ImageDraw.Draw(img_h2)
        draw_h2.pieslice([center[0] - r, center[1] - r, center[0] + r, center[1] + r], 0, 180, fill=outer_c)
        draw_h2.pieslice([center[0] - inner_r, center[1] - inner_r, center[0] + inner_r, center[1] + inner_r], 0, 180, fill=inner_c)
        draw_h2.line([(center[0] - r, center[1]), (center[0] + r, center[1])], fill=(255, 255, 255, 210), width=3)
        h2_path = os.path.join(sliced_dir, f"{key}_half_2.png")
        img_h2.save(h2_path, "PNG")

        manifest["sliced_fruits"][key] = {
            "half_1": f"assets/sliced_fruits/{key}_half_1.png",
            "half_2": f"assets/sliced_fruits/{key}_half_2.png",
        }

    # 2. Generate Bomb Sprite
    bomb_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bdraw = ImageDraw.Draw(bomb_img)
    br = 42
    bdraw.ellipse([center[0] - br, center[1] - br, center[0] + br, center[1] + br], fill=(38, 40, 48), outline=(70, 75, 88), width=3)
    bdraw.ellipse([center[0] - br // 2 - 2, center[1] - br // 2 - 2, center[0] - br // 2 + 12, center[1] - br // 2 + 12], fill=(120, 125, 140, 160))
    bdraw.rectangle([center[0] - 8, center[1] - br - 8, center[0] + 8, center[1] - br], fill=(110, 115, 130))
    bdraw.line([center[0] - 12, center[1] - 12, center[0] + 12, center[1] + 12], fill=(240, 45, 45), width=3)
    bdraw.line([center[0] + 12, center[1] - 12, center[0] - 12, center[1] + 12], fill=(240, 45, 45), width=3)
    bomb_path = os.path.join(bombs_dir, "bomb.png")
    bomb_img.save(bomb_path, "PNG")
    manifest["bombs"]["standard_bomb"] = {"path": "assets/bombs/bomb.png", "radius": br}

    # 3. Background Art
    bg_img = Image.new("RGB", (1280, 720), (16, 18, 30))
    bg_draw = ImageDraw.Draw(bg_img)
    for y in range(0, 720, 90):
        bg_draw.line([(0, y), (1280, y)], fill=(22, 26, 42), width=2)
    bg_path = os.path.join(bg_dir, "arcade_bg.png")
    bg_img.save(bg_path, "PNG")
    manifest["backgrounds"]["arcade_dojo"] = {"path": "assets/backgrounds/arcade_bg.png", "size": [1280, 720]}

    # Manifest save
    manifest_path = os.path.join(ASSETS_DIR, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Generated all fruit assets, bomb sprites, and manifest at {manifest_path}")

if __name__ == "__main__":
    generate_fruit_assets()
