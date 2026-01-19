# -*- coding: utf-8 -*-
"""
Generate .icns and .ico from assets/app_icon.png
"""

from pathlib import Path
import sys


def ensure_square(img):
    width, height = img.size
    if width == height:
        return img
    size = max(width, height)
    background = img.new("RGBA", (size, size), (0, 0, 0, 0))
    offset = ((size - width) // 2, (size - height) // 2)
    background.paste(img, offset)
    return background


def main():
    try:
        from PIL import Image
    except ImportError:
        print("Missing dependency: Pillow. Install with: pip install pillow")
        return 1

    root = Path(__file__).resolve().parents[1]
    source = root / "assets" / "app_icon.png"
    if not source.exists():
        print(f"Source icon not found: {source}")
        return 1

    output_dir = root / "assets" / "icons"
    output_dir.mkdir(parents=True, exist_ok=True)

    sizes = [(16, 16), (32, 32), (64, 64), (128, 128), (256, 256), (512, 512), (1024, 1024)]
    with Image.open(source) as img:
        img = img.convert("RGBA")
        img = ensure_square(img)

        ico_path = output_dir / "app_icon.ico"
        img.save(ico_path, sizes=sizes)
        print(f"Wrote {ico_path}")

        icns_path = output_dir / "app_icon.icns"
        img.save(icns_path, sizes=sizes)
        print(f"Wrote {icns_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
