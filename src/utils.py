"""
utils.py
Utility functions for collision detection, line of sight, and sprite loading
"""

import pygame
import os
import math
from pygame import Surface
from src.config import TILE, MAP_TOP, MAP_W, MAP_H, SPRITE_SIZE

def clamp(v, a, b):
    return max(a, min(b, v))

def lerp(a, b, t):
    return a + (b - a) * t

def load_and_prepare_sprite(path, size=SPRITE_SIZE):
    try:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Sprite file not found: {path}")
        img = pygame.image.load(path).convert_alpha()
        if img.get_width() == 0 or img.get_height() == 0:
            raise ValueError(f"Invalid sprite dimensions in {path}")
        img = pygame.transform.smoothscale(img, (size, size))
        return img
    except (pygame.error, FileNotFoundError, ValueError) as e:
        print(f"Warning: failed to load sprite {path}: {e}")
        surf = Surface((size, size), pygame.SRCALPHA)
        surf.fill((180, 100, 100, 180))
        pygame.draw.rect(surf, (255, 255, 255), surf.get_rect(), 2)
        pygame.draw.line(surf, (255, 255, 255), (0, 0), (size, size), 2)
        pygame.draw.line(surf, (255, 255, 255), (0, size), (size, 0), 2)
        return surf

def tint_surface(src_surf, tint_color, alpha=120):
    surf = src_surf.copy()
    overlay = Surface(surf.get_size(), pygame.SRCALPHA)
    overlay.fill((*tint_color, alpha))
    surf.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
    return surf

def make_anim_frames(base_img):
    w, h = base_img.get_size()
    f0 = base_img
    f1 = Surface((w, h), pygame.SRCALPHA)
    # slight vertical offset for simple two-frame "bobbing"
    f1.blit(base_img, (0, 2))
    return (f0, f1)

def is_solid(px, py, radius=0, game_map=None):
    """Return True if the point or circle at (px,py) overlaps any solid tile."""
    if game_map is None:
        return False
    
    # convert world coords to tile indices (y adjusted by MAP_TOP)
    left = int((px - radius) // TILE)
    right = int((px + radius) // TILE)
    top = int(((py - radius) - MAP_TOP) // TILE)
    bottom = int(((py + radius) - MAP_TOP) // TILE)

    # out-of-bounds => solid
    if left < 0 or top < 0 or right >= MAP_W or bottom >= MAP_H:
        return True

    circle_x = px
    circle_y = py - MAP_TOP

    for ty in range(top, bottom + 1):
        for tx in range(left, right + 1):
            if not game_map[ty][tx]:
                continue

            tile_left = tx * TILE
            tile_right = tile_left + TILE
            tile_top = ty * TILE
            tile_bottom = tile_top + TILE

            closest_x = max(tile_left, min(circle_x, tile_right))
            closest_y = max(tile_top, min(circle_y, tile_bottom))

            dist_x = circle_x - closest_x
            dist_y = circle_y - closest_y
            dist_squared = dist_x * dist_x + dist_y * dist_y

            if dist_squared <= radius * radius:
                return True

    return False

def can_see(observer, target, game_map, max_dist=420, step=8):
    if observer is None or target is None:
        return False
    if not target.alive:
        return False

    dx = target.x - observer.x
    dy = target.y - observer.y
    dist = math.hypot(dx, dy)
    if dist > max_dist:
        return False
    if dist > 0:
        dx /= dist
        dy /= dist

    current_x = observer.x
    current_y = observer.y
    total_steps = int(dist / step)

    for _ in range(total_steps):
        current_x += dx * step
        current_y += dy * step
        if (current_x < 0 or current_x >= MAP_W * TILE or
            current_y < MAP_TOP or current_y >= MAP_TOP + MAP_H * TILE):
            return False
        if is_solid(current_x, current_y, game_map=game_map):
            return False

    if is_solid(target.x, target.y, game_map=game_map):
        return False
    return True