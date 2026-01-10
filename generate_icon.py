#!/usr/bin/env python3
"""
Generate SartoriusBridge app icon
Modern/minimal design with teal/blue gradient
"""

from PIL import Image, ImageDraw
import math
import os

def create_scale_icon(size=1024):
    """Create a modern minimal scale icon with teal/blue gradient"""

    # Create image with transparency
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Colors - teal/blue gradient palette
    teal_dark = (0, 128, 128)      # Deep teal
    teal_light = (64, 224, 208)    # Turquoise
    blue_accent = (30, 144, 255)   # Dodger blue

    # Calculate dimensions based on size
    center_x = size // 2
    center_y = size // 2
    margin = size // 8

    # Draw circular background with gradient effect
    for i in range(size // 2, 0, -2):
        # Gradient from dark outer to lighter inner
        progress = i / (size // 2)
        r = int(teal_dark[0] + (teal_light[0] - teal_dark[0]) * (1 - progress) * 0.5)
        g = int(teal_dark[1] + (teal_light[1] - teal_dark[1]) * (1 - progress) * 0.5)
        b = int(teal_dark[2] + (teal_light[2] - teal_dark[2]) * (1 - progress) * 0.5)

        draw.ellipse(
            [center_x - i, center_y - i, center_x + i, center_y + i],
            fill=(r, g, b, 255)
        )

    # Scale parameters
    scale_color = (255, 255, 255)  # White for contrast
    line_width = max(size // 40, 4)

    # Central pillar (vertical line)
    pillar_height = size // 3
    pillar_top = center_y - pillar_height // 2 - size // 20
    pillar_bottom = center_y + pillar_height // 2

    draw.line(
        [(center_x, pillar_top), (center_x, pillar_bottom)],
        fill=scale_color, width=line_width
    )

    # Horizontal beam at top
    beam_width = size // 2
    beam_y = pillar_top + size // 20

    draw.line(
        [(center_x - beam_width // 2, beam_y), (center_x + beam_width // 2, beam_y)],
        fill=scale_color, width=line_width
    )

    # Left pan (circle)
    pan_radius = size // 10
    left_pan_x = center_x - beam_width // 2
    left_pan_y = beam_y + size // 8

    # Strings connecting beam to pans
    draw.line(
        [(left_pan_x, beam_y), (left_pan_x, left_pan_y - pan_radius)],
        fill=scale_color, width=line_width // 2
    )

    # Left pan
    draw.ellipse(
        [left_pan_x - pan_radius, left_pan_y - pan_radius // 2,
         left_pan_x + pan_radius, left_pan_y + pan_radius // 2],
        outline=scale_color, width=line_width
    )

    # Right pan
    right_pan_x = center_x + beam_width // 2
    right_pan_y = beam_y + size // 8

    draw.line(
        [(right_pan_x, beam_y), (right_pan_x, right_pan_y - pan_radius)],
        fill=scale_color, width=line_width // 2
    )

    draw.ellipse(
        [right_pan_x - pan_radius, right_pan_y - pan_radius // 2,
         right_pan_x + pan_radius, right_pan_y + pan_radius // 2],
        outline=scale_color, width=line_width
    )

    # Base platform
    base_width = size // 4
    base_height = size // 20
    base_y = pillar_bottom

    draw.rectangle(
        [center_x - base_width // 2, base_y,
         center_x + base_width // 2, base_y + base_height],
        fill=scale_color
    )

    # Small triangle at top of pillar (fulcrum indicator)
    triangle_size = size // 25
    triangle_points = [
        (center_x, pillar_top),
        (center_x - triangle_size, pillar_top + triangle_size),
        (center_x + triangle_size, pillar_top + triangle_size)
    ]
    draw.polygon(triangle_points, fill=scale_color)

    return img


def create_menu_bar_icon(size=22):
    """Create a simple menu bar icon (template style)"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Simple scale silhouette in black (for template image)
    color = (0, 0, 0, 255)
    line_width = max(size // 11, 1)

    center_x = size // 2

    # Vertical pillar
    draw.line([(center_x, 4), (center_x, size - 4)], fill=color, width=line_width)

    # Horizontal beam
    beam_y = 6
    draw.line([(4, beam_y), (size - 4, beam_y)], fill=color, width=line_width)

    # Left pan
    draw.ellipse([2, 9, 8, 13], outline=color, width=1)

    # Right pan
    draw.ellipse([size - 8, 9, size - 2, 13], outline=color, width=1)

    # Base
    draw.rectangle([center_x - 4, size - 5, center_x + 4, size - 3], fill=color)

    return img


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Generate main app icon at multiple sizes
    sizes = [1024, 512, 256, 128, 64, 32, 16]

    print("Generating app icons...")

    # Create iconset directory for macOS
    iconset_dir = os.path.join(script_dir, "SartoriusBridge.iconset")
    os.makedirs(iconset_dir, exist_ok=True)

    # Generate icons at various sizes
    for size in sizes:
        icon = create_scale_icon(size)

        # Save regular resolution
        filename = f"icon_{size}x{size}.png"
        icon.save(os.path.join(iconset_dir, filename))
        print(f"  Created {filename}")

        # Save @2x resolution for Retina (except for largest)
        if size <= 512:
            retina_size = size * 2
            retina_icon = create_scale_icon(retina_size)
            retina_filename = f"icon_{size}x{size}@2x.png"
            retina_icon.save(os.path.join(iconset_dir, retina_filename))
            print(f"  Created {retina_filename}")

    # Also save main icon as PNG
    main_icon = create_scale_icon(1024)
    main_icon.save(os.path.join(script_dir, "icon.png"))
    print("  Created icon.png (1024x1024)")

    # Generate menu bar icon
    print("\nGenerating menu bar icon...")
    menubar_icon = create_menu_bar_icon(22)
    menubar_icon.save(os.path.join(script_dir, "menubar_icon.png"))
    print("  Created menubar_icon.png (22x22)")

    # Also create @2x version
    menubar_icon_2x = create_menu_bar_icon(44)
    menubar_icon_2x.save(os.path.join(script_dir, "menubar_icon@2x.png"))
    print("  Created menubar_icon@2x.png (44x44)")

    print("\nDone! To create .icns file on macOS, run:")
    print(f"  iconutil -c icns {iconset_dir}")


if __name__ == "__main__":
    main()
