#!/usr/bin/env python3
"""
Generate Default Assets for Game Launcher

This script creates the default icon and PlayStation button icons
used by the game launcher.
"""

import os
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("Pillow not installed. Run: pip install Pillow")


def create_default_icon(output_path: str, size: int = 256):
    """
    Create a default game icon.

    Args:
        output_path: Path to save the icon
        size: Icon size in pixels
    """
    if not HAS_PIL:
        return

    # Create image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background rounded rectangle
    margin = 10
    bg_color = (50, 50, 70, 255)
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=20,
        fill=bg_color
    )

    # Draw a simple gamepad icon
    center_x, center_y = size // 2, size // 2
    pad_color = (150, 150, 170, 255)

    # Main body (ellipse)
    body_width = size * 0.5
    body_height = size * 0.3
    draw.ellipse([
        center_x - body_width // 2,
        center_y - body_height // 2,
        center_x + body_width // 2,
        center_y + body_height // 2
    ], outline=pad_color, width=4)

    # D-pad cross
    cross_size = size * 0.12
    cross_width = 4
    # Horizontal line
    draw.line([
        center_x - cross_size, center_y,
        center_x + cross_size, center_y
    ], fill=pad_color, width=cross_width)
    # Vertical line
    draw.line([
        center_x, center_y - cross_size,
        center_x, center_y + cross_size
    ], fill=pad_color, width=cross_width)

    # Left handle
    handle_offset = size * 0.2
    handle_height = size * 0.15
    draw.ellipse([
        center_x - body_width // 2 - 10,
        center_y + body_height // 4,
        center_x - body_width // 2 + 30,
        center_y + body_height // 4 + handle_height
    ], outline=pad_color, width=3)

    # Right handle
    draw.ellipse([
        center_x + body_width // 2 - 30,
        center_y + body_height // 4,
        center_x + body_width // 2 + 10,
        center_y + body_height // 4 + handle_height
    ], outline=pad_color, width=3)

    # Save
    img.save(output_path, 'PNG')
    print(f"Created: {output_path}")


def create_button_icon(output_path: str, symbol: str, color: tuple, size: int = 64):
    """
    Create a PlayStation-style button icon.

    Args:
        output_path: Path to save the icon
        symbol: Symbol to draw (X, O, △, □)
        color: RGB color tuple
        size: Icon size
    """
    if not HAS_PIL:
        return

    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    center = size // 2
    radius = size // 2 - 4

    # Draw circle background
    draw.ellipse([4, 4, size - 4, size - 4], outline=color, width=3)

    # Draw symbol
    symbol_color = color
    if symbol == 'X':
        # Cross (X)
        offset = size * 0.25
        draw.line([center - offset, center - offset, center + offset, center + offset],
                  fill=symbol_color, width=4)
        draw.line([center + offset, center - offset, center - offset, center + offset],
                  fill=symbol_color, width=4)

    elif symbol == 'O':
        # Circle (O)
        offset = size * 0.2
        draw.ellipse([center - offset, center - offset, center + offset, center + offset],
                     outline=symbol_color, width=3)

    elif symbol == '△':
        # Triangle
        offset = size * 0.25
        points = [
            (center, center - offset),  # Top
            (center - offset, center + offset * 0.7),  # Bottom left
            (center + offset, center + offset * 0.7),  # Bottom right
        ]
        draw.polygon(points, outline=symbol_color, width=3)

    elif symbol == '□':
        # Square
        offset = size * 0.2
        draw.rectangle([center - offset, center - offset, center + offset, center + offset],
                       outline=symbol_color, width=3)

    img.save(output_path, 'PNG')
    print(f"Created: {output_path}")


def create_text_button_icon(output_path: str, text: str, color: tuple, size: int = 64):
    """
    Create a button icon with text (like OPTIONS, SHARE).

    Args:
        output_path: Path to save the icon
        text: Text to display
        color: RGB color tuple
        size: Icon size
    """
    if not HAS_PIL:
        return

    img = Image.new('RGBA', (size * 2, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw rounded rectangle background
    draw.rounded_rectangle([2, 2, size * 2 - 2, size - 2], radius=size // 4, outline=color, width=3)

    # Draw text
    try:
        # Try to use a font, fall back to default if not available
        font_size = size // 4
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()

    # Center text
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (size * 2 - text_width) // 2
    text_y = (size - text_height) // 2 - bbox[1]

    draw.text((text_x, text_y), text, fill=color, font=font)

    img.save(output_path, 'PNG')
    print(f"Created: {output_path}")


def create_dpad_icon(output_path: str, direction: str, color: tuple, size: int = 64):
    """
    Create a D-pad directional icon.

    Args:
        output_path: Path to save the icon
        direction: Direction (up, down, left, right)
        color: RGB color tuple
        size: Icon size
    """
    if not HAS_PIL:
        return

    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    center = size // 2

    # Draw circle background
    draw.ellipse([4, 4, size - 4, size - 4], outline=color, width=3)

    # Draw arrow based on direction
    offset = size * 0.25
    arrow_points = []

    if direction == 'up':
        arrow_points = [
            (center, center - offset),  # Tip
            (center - offset * 0.6, center + offset * 0.3),  # Left
            (center + offset * 0.6, center + offset * 0.3),  # Right
        ]
    elif direction == 'down':
        arrow_points = [
            (center, center + offset),  # Tip
            (center - offset * 0.6, center - offset * 0.3),  # Left
            (center + offset * 0.6, center - offset * 0.3),  # Right
        ]
    elif direction == 'left':
        arrow_points = [
            (center - offset, center),  # Tip
            (center + offset * 0.3, center - offset * 0.6),  # Top
            (center + offset * 0.3, center + offset * 0.6),  # Bottom
        ]
    elif direction == 'right':
        arrow_points = [
            (center + offset, center),  # Tip
            (center - offset * 0.3, center - offset * 0.6),  # Top
            (center - offset * 0.3, center + offset * 0.6),  # Bottom
        ]

    draw.polygon(arrow_points, fill=color)

    img.save(output_path, 'PNG')
    print(f"Created: {output_path}")


def main():
    """Generate all default assets."""
    # Create directories
    assets_dir = Path("assets")
    button_icons_dir = assets_dir / "button_icons"

    assets_dir.mkdir(exist_ok=True)
    button_icons_dir.mkdir(exist_ok=True)

    # Create game icons directory
    game_icons_dir = assets_dir / "game_icons"
    game_icons_dir.mkdir(exist_ok=True)

    if not HAS_PIL:
        print("Cannot generate assets without Pillow.")
        print("Install with: pip install Pillow")
        return

    print("Generating PlayStation controller button icons...")
    print("=" * 50)

    # Create default game icon
    create_default_icon(str(assets_dir / "default_icon.png"), 256)

    # PlayStation action button colors (authentic PS4/PS5 colors)
    # X button (blue)
    create_button_icon(str(button_icons_dir / "cross.png"), 'X', (93, 156, 236), 64)

    # Circle button (red)
    create_button_icon(str(button_icons_dir / "circle.png"), 'O', (245, 90, 90), 64)

    # Triangle button (green)
    create_button_icon(str(button_icons_dir / "triangle.png"), '△', (28, 209, 162), 64)

    # Square button (pink)
    create_button_icon(str(button_icons_dir / "square.png"), '□', (244, 143, 177), 64)

    # D-pad directional icons (white/light gray)
    dpad_color = (200, 200, 200)
    create_dpad_icon(str(button_icons_dir / "dpad_up.png"), 'up', dpad_color, 64)
    create_dpad_icon(str(button_icons_dir / "dpad_down.png"), 'down', dpad_color, 64)
    create_dpad_icon(str(button_icons_dir / "dpad_left.png"), 'left', dpad_color, 64)
    create_dpad_icon(str(button_icons_dir / "dpad_right.png"), 'right', dpad_color, 64)

    # Special buttons (white/light gray)
    special_color = (200, 200, 200)
    create_text_button_icon(str(button_icons_dir / "options.png"), 'OPTIONS', special_color, 48)
    create_text_button_icon(str(button_icons_dir / "share.png"), 'SHARE', special_color, 48)

    print("\n✓ Asset generation complete!")
    print(f"Generated {len(list(button_icons_dir.glob('*.png')))} button icons")
    print(f"Icons saved to: {button_icons_dir}")


if __name__ == "__main__":
    main()
