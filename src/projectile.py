"""
projectile.py
Projectile entity
"""

import pygame
import math
from src.utils import is_solid
from src.config import MAP_W, MAP_H, TILE, MAP_TOP

class Projectile:
    def __init__(self, x, y, vx, vy, dmg, owner=None, life=2.0, radius=4, color=(20, 20, 20), is_melee=False):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.dmg = dmg
        self.owner = owner
        self.life = life
        self.radius = radius
        self.color = color
        self.is_melee = is_melee
        self.has_hit = False

    def update(self, dt, game):
        if not self.is_melee:
            self.x += self.vx * dt
            self.y += self.vy * dt

        self.life -= dt

        # check collision with level geometry
        if not self.is_melee and is_solid(self.x, self.y, game_map=game.game_map):
            self.life = -1
            return

        if self.has_hit:
            return

        # check collision with players
        for p in game.players:
            if not p.alive or p is self.owner:
                continue
            if math.hypot(p.x - self.x, p.y - self.y) <= p.radius + self.radius:
                p.take_damage(self.dmg, attacker=self.owner)
                if not self.is_melee:
                    self.life = -1
                self.has_hit = True
                return

    def draw(self, surf, cam_x=0, cam_y=0):
        if self.life <= 0:
            return
        screen_x = int(self.x - cam_x)
        screen_y = int(self.y - cam_y)
        pygame.draw.circle(surf, self.color, (screen_x, screen_y), self.radius)