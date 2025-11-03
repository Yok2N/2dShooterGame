"""
main.py
Main entry point for Pixel Tactics game

Run this file to start the game.
Place knight.png, ranger.png, wizard.png in the same directory (or placeholders will be drawn)
"""

import pygame
import sys
import random
import traceback
from src.config import (WIDTH, HEIGHT, FPS, ASSET_PATHS, MAP_W, MAP_H, 
                    TILE, MAP_TOP, BG, CONFIG)
from src.utils import load_and_prepare_sprite, make_anim_frames
from src.map import generate_map
from src.game import Game
from src.ui import draw_combined_select

def init_fonts():
    """Initialize pygame fonts"""
    fonts = {}
    if pygame.font.get_init():
        fonts['FONT'] = pygame.font.SysFont("Segoe UI", 16)
        fonts['BIG'] = pygame.font.SysFont("Segoe UI", 32)
        fonts['SMALL'] = pygame.font.SysFont("Segoe UI", 12)
    return fonts

def load_sprites():
    """Load and prepare all character sprites"""
    sprites = {}
    for k, p in ASSET_PATHS.items():
        sprites[k] = load_and_prepare_sprite(p)
    return sprites

def create_animation_frames(sprites):
    """Create animation frames from sprites"""
    return {name: make_anim_frames(sprites[name]) for name in ASSET_PATHS.keys()}

def handle_game_state(game, events, sel_index):
    """Handle game state transitions and input"""
    names = list(ASSET_PATHS.keys())
    for event in events:
        if event.type == pygame.QUIT:
            return False, sel_index
        if event.type == pygame.KEYDOWN:
            if game.state == "TEAM_SELECT":
                if event.key == pygame.K_LEFT:
                    sel_index = (sel_index - 1) % len(names)
                elif event.key == pygame.K_RIGHT:
                    sel_index = (sel_index + 1) % len(names)
                elif event.key == pygame.K_RETURN:
                    if names:
                        game.selected_chars["A"] = names[sel_index]
                        game.selected_chars["B"] = random.choice(names)
                        game.create_players()
            elif game.state == "ROUND_END":
                current_time = pygame.time.get_ticks()
                if current_time - game.between_timer > CONFIG.ROUND_END_WAIT_MS:
                    game.reset_for_next_round()
            elif event.key == pygame.K_ESCAPE:
                return False, sel_index
    return True, sel_index

def main():
    """Main game loop"""
    try:
        # Initialize pygame
        pygame.init()
        pygame.font.init()
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Pixel Tactics — With Art (Fixed)")
        clock = pygame.time.Clock()

        # Load resources
        fonts = init_fonts()
        sprites = load_sprites()
        anim_frames = create_animation_frames(sprites)
        game_map = generate_map()
        plant_zone = pygame.Rect((MAP_W * TILE) // 2 - 40, MAP_TOP + (MAP_H * TILE) // 2 - 40, 80, 80)

        # Create game instance
        game = Game(game_map, plant_zone, sprites, anim_frames)
        sel_index = 0
        running = True

        # Main game loop
        while running:
            dt = clock.tick(FPS) / 1000.0
            events = pygame.event.get()
            running, sel_index = handle_game_state(game, events, sel_index)
            if not running:
                break

            keys = pygame.key.get_pressed()
            mouse_buttons = pygame.mouse.get_pressed()
            mouse_pos = pygame.mouse.get_pos()

            screen.fill(BG)

            if game.state == "TEAM_SELECT":
                draw_combined_select(screen, sel_index, sprites, fonts)
            else:
                game.update(dt, keys, mouse_buttons, mouse_pos)
                game.draw(screen, fonts)

            pygame.display.flip()

    except Exception as e:
        print(f"Game crashed: {e}")
        traceback.print_exc()
    finally:
        pygame.quit()
        sys.exit()

if __name__ == '__main__':
    main()