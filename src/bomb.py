"""
bomb.py
Bomb entity with planting and defusing mechanics
"""

import pygame
import math
import os
from pygame import Surface
from src.config import CONFIG, YELLOW, WHITE

class Bomb:
    def __init__(self, plant_zone):
        self.planted = False
        self.planting_player = None
        self.plant_progress = 0.0
        self.plant_done = False
        self.defusing_player = None
        self.defuse_progress = 0.0
        self.plant_zone = plant_zone
        if plant_zone:
            self.location = (plant_zone.centerx, plant_zone.centery)
        else:
            self.location = (480, 320)
        self.countdown = CONFIG.BOMB_TIMER_MS / 1000.0
        
        # Load bomb image
        self.bomb_image = None
        bomb_path = os.path.join("Assets", "bomb.png")
        print(f"Looking for bomb image at: {bomb_path}")
        print(f"Bomb image exists: {os.path.exists(bomb_path)}")
        
        if os.path.exists(bomb_path):
            try:
                self.bomb_image = pygame.image.load(bomb_path).convert_alpha()
                # Scale to reasonable size (adjust as needed)
                self.bomb_image = pygame.transform.scale(self.bomb_image, (32, 32))
                print(f"Bomb image loaded successfully: {self.bomb_image.get_size()}")
            except Exception as e:
                print(f"Could not load bomb image: {e}")

    def start_plant(self, player):
        if self.planted:
            return
        if not self.plant_zone.collidepoint(player.x, player.y):
            return
        self.planting_player = player
        self.plant_progress = CONFIG.PLANT_TIME_MS / 1000.0
        print(f"Started planting bomb at ({player.x}, {player.y})")

    def start_defuse(self, player):
        if not self.planted or not self.plant_done:
            return
        if not self.plant_zone.collidepoint(player.x, player.y):
            return
        self.defusing_player = player
        self.defuse_progress = CONFIG.DEFUSE_TIME_MS / 1000.0
        print(f"Started defusing bomb")

    def update(self, dt, game):
        # planting
        if self.planting_player:
            p = self.planting_player
            if not p.alive or not self.plant_zone.collidepoint(p.x, p.y):
                self.planting_player = None
                self.plant_progress = 0.0
                print("Planting cancelled - player moved or died")
            else:
                self.plant_progress -= dt
                if self.plant_progress <= 0:
                    self.planted = True
                    self.plant_done = True
                    self.location = (p.x, p.y)
                    self.planting_player = None
                    self.countdown = CONFIG.BOMB_TIMER_MS / 1000.0
                    print(f"BOMB PLANTED at {self.location}!")

        # bomb ticking / defuse
        if self.planted and self.plant_done:
            self.countdown -= dt
            if self.defusing_player:
                d = self.defusing_player
                if not d.alive or not self.plant_zone.collidepoint(d.x, d.y):
                    self.defusing_player = None
                    self.defuse_progress = 0.0
                else:
                    self.defuse_progress -= dt
                    if self.defuse_progress <= 0:
                        # defenders succeed
                        winner = "B" if game.attack_team == "A" else "A"
                        game.end_round(winner, reason="Defuse")
                        return None
            if self.countdown <= 0:
                # explosion: damage nearby players
                for p in game.players:
                    if math.hypot(p.x - self.location[0], p.y - self.location[1]) <= 160:
                        p.take_damage(999, None)
                game.end_round(game.attack_team, reason="Explosion")
                return "explosion"
        return None

    def draw(self, surf, font, cam_x=0, cam_y=0):
        # DEBUG: Always show what state we're in
        if self.planted and self.plant_done:
            sx = int(self.location[0] - cam_x)
            sy = int(self.location[1] - cam_y)
            print(f"Drawing planted bomb at screen pos ({sx}, {sy}), world pos {self.location}, cam ({cam_x}, {cam_y})")
        
        if not self.planted:
            # Show planting progress bar
            if self.planting_player:
                frac = 1.0 - (self.plant_progress / (CONFIG.PLANT_TIME_MS / 1000.0))
                if frac < 0:
                    frac = 0
                w = int(60 * frac)
                rz = self.plant_zone.move(-cam_x, -cam_y)
                pygame.draw.rect(surf, YELLOW, (rz.centerx - 30, rz.top - 10, w, 6))
        else:
            # Bomb is planted - show bomb image and countdown
            sx = int(self.location[0] - cam_x)
            sy = int(self.location[1] - cam_y)
            
            # Draw bomb image if available, otherwise draw circle
            if self.bomb_image:
                img_rect = self.bomb_image.get_rect(center=(sx, sy))
                surf.blit(self.bomb_image, img_rect)
                print(f"Drew bomb image at {img_rect}")
            else:
                pygame.draw.circle(surf, (80, 40, 20), (sx, sy), 12)
                print(f"Drew bomb circle at ({sx}, {sy})")
            
            # Draw countdown timer
            if font:
                countdown_text = f"{int(max(0, self.countdown))}"
                txt = font.render(countdown_text, True, WHITE)
                # Center text above the bomb
                txt_rect = txt.get_rect(center=(sx, sy - 25))
                
                # Add background for better visibility
                bg_rect = txt_rect.inflate(8, 4)
                bg_surface = Surface(bg_rect.size, pygame.SRCALPHA)
                bg_surface.fill((0, 0, 0, 180))
                surf.blit(bg_surface, bg_rect)
                
                surf.blit(txt, txt_rect)
            
            # Show defusing progress bar
            if self.defusing_player:
                rz = self.plant_zone.move(-cam_x, -cam_y)
                frac = 1.0 - (self.defuse_progress / (CONFIG.DEFUSE_TIME_MS / 1000.0))
                pygame.draw.rect(surf, (40, 160, 40), (rz.centerx - 30, rz.top - 10, int(60 * frac), 6))