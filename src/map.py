# src/map.py
"""
map.py
Image -> map grid loader + renderer
Produces a grid of size MAP_H x MAP_W and a draw_map function.
"""
import pygame
from PIL import Image
import os
from src.config import MAP_W, MAP_H, TILE, MAP_TOP, BG, YELLOW

def classify_tile(tile):
    """Classify a tile as grass (0), wall (1), or crate (2) based on avg color."""
    # downscale to 1x1 to get average color
    r, g, b = tile.resize((1, 1)).getpixel((0, 0))

    # very simple color rules tuned for typical top-down tiles
    if g > 100 and g > r and g > b:
        return 0  # grass (green)
    elif r > 120 and g > 80 and b < 80:
        return 2  # crate (brown-ish)
    else:
        return 1  # wall / neutral

def generate_map_from_image(image_path, tile_size=50):
    """
    Load an image and convert it into a MAP_H x MAP_W grid.
    If the image is not exactly MAP_W*tile_size by MAP_H*tile_size,
    it will be resized (nearest neighbor) to that size so the grid matches.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Map image not found: {image_path}")

    img = Image.open(image_path).convert("RGB")
    target_w = MAP_W * tile_size
    target_h = MAP_H * tile_size

    if img.size != (target_w, target_h):
        # Resize with nearest neighbor so colors remain stable per tile
        img = img.resize((target_w, target_h), resample=Image.NEAREST)

    cols = target_w // tile_size
    rows = target_h // tile_size

    grid = []
    for y in range(rows):
        row = []
        for x in range(cols):
            left = x * tile_size
            top = y * tile_size
            right = left + tile_size
            bottom = top + tile_size
            tile = img.crop((left, top, right, bottom))
            tile_type = classify_tile(tile)
            row.append(tile_type)
        grid.append(row)

    # ensure grid dimensions match MAP_H x MAP_W
    # (should already, but be defensive)
    grid = grid[:MAP_H]
    for i in range(len(grid)):
        if len(grid[i]) < MAP_W:
            grid[i] += [1] * (MAP_W - len(grid[i]))  # pad with walls

    return grid

# wrapper for your main.py which expects no-arg generate_map()
def generate_map():
    # adjust path if your asset lives elsewhere
    image_path = os.path.join("Assets", "2dMap.png")
    return generate_map_from_image(image_path, tile_size=TILE)


# --- simple renderer used by Game.draw() ---
def draw_map(surface, game_map, plant_zone, cam_x=0, cam_y=0):
    """
    Draw the map tiles to the given surface.
    game_map is expected to be a list of rows (MAP_H x MAP_W).
    cam_x, cam_y are camera offsets in pixels.
    """
    surface.fill(BG)
    h = len(game_map)
    w = len(game_map[0]) if h > 0 else 0

    for y in range(h):
        for x in range(w):
            sx = x * TILE - cam_x
            sy = y * TILE + MAP_TOP - cam_y
            r = (sx, sy, TILE, TILE)
            tile = game_map[y][x]
            if tile == 1:
                color = (50, 50, 60)  # wall
            elif tile == 2:
                color = (150, 100, 50)  # crate (brown)
            else:
                color = (200, 220, 180)  # grass / floor
            pygame.draw.rect(surface, color, r)

    # plant zone outline (optional)
    if plant_zone:
        rz = plant_zone.move(-cam_x, -cam_y)
        pygame.draw.rect(surface, YELLOW, rz, 3)