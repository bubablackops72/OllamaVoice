#!/usr/bin/env python3
"""
Generates ollama_icon.ico - an Ollama-style llama head icon.
Run this once before building the installer.
"""

from PIL import Image, ImageDraw
import math
import os

def draw_ollama_icon(size):
    """Draw an Ollama-style llama head icon at the given size."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    s = size / 64  # scale factor (design is based on 64px)

    # Background circle - dark charcoal like Ollama's brand
    draw.ellipse([0, 0, size-1, size-1], fill=(30, 30, 30, 255))

    # ── Llama head shape ──────────────────────────────────────
    # Main head - rounded rectangle
    head_x1, head_y1 = 16*s, 18*s
    head_x2, head_y2 = 48*s, 50*s
    draw.rounded_rectangle([head_x1, head_y1, head_x2, head_y2],
                            radius=8*s, fill=(232, 255, 71, 255))  # Ollama yellow-green

    # Snout / muzzle bump
    snout_pts = [
        (22*s, 44*s),
        (20*s, 52*s),
        (28*s, 54*s),
        (36*s, 54*s),
        (44*s, 52*s),
        (42*s, 44*s),
    ]
    draw.polygon(snout_pts, fill=(232, 255, 71, 255))

    # Ears - two rounded bumps at top
    # Left ear
    draw.ellipse([14*s, 10*s, 26*s, 26*s], fill=(232, 255, 71, 255))
    # Right ear
    draw.ellipse([38*s, 10*s, 50*s, 26*s], fill=(232, 255, 71, 255))

    # Inner ears - darker
    draw.ellipse([17*s, 13*s, 23*s, 22*s], fill=(30, 30, 30, 255))
    draw.ellipse([41*s, 13*s, 47*s, 22*s], fill=(30, 30, 30, 255))

    # Eyes - dark circles with highlight
    eye_size = 4*s
    # Left eye
    draw.ellipse([21*s, 26*s, 21*s+eye_size, 26*s+eye_size], fill=(30, 30, 30, 255))
    draw.ellipse([22*s, 27*s, 22*s+1.5*s, 27*s+1.5*s], fill=(255, 255, 255, 200))
    # Right eye
    draw.ellipse([39*s, 26*s, 39*s+eye_size, 26*s+eye_size], fill=(30, 30, 30, 255))
    draw.ellipse([40*s, 27*s, 40*s+1.5*s, 27*s+1.5*s], fill=(255, 255, 255, 200))

    # Nostrils
    draw.ellipse([26*s, 48*s, 29*s, 51*s], fill=(30, 30, 30, 200))
    draw.ellipse([35*s, 48*s, 38*s, 51*s], fill=(30, 30, 30, 200))

    # Neck
    draw.rounded_rectangle([22*s, 48*s, 42*s, 60*s],
                            radius=4*s, fill=(232, 255, 71, 255))

    return img


def main():
    output_path = os.path.join(os.path.dirname(__file__), "ollama_icon.ico")

    # Generate at multiple sizes for a proper .ico file
    sizes = [256, 128, 64, 48, 32, 16]
    images = [draw_ollama_icon(s) for s in sizes]

    # Save as .ico with all sizes embedded
    images[0].save(
        output_path,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[1:]
    )
    print(f"[icon] Saved: {output_path}")


if __name__ == "__main__":
    main()
