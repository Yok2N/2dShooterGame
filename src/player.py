"""
player.py
Player entity with different character classes
"""

import pygame
import math
import random
from pygame import Surface
from src.projectile import Projectile
from src.utils import is_solid, tint_surface
from src.config import (SPRITE_SIZE, ATT_COL, DEF_COL, UI_BG_DARK,
                    SUCCESS_LIGHT, YELLOW, DANGER_LIGHT, WHITE)

class Player:
    def __init__(self, x: float, y: float, team: str, name: str, char: str, is_bot: bool = False):
        self.x = x
        self.y = y
        self.team = team
        self.name = name
        self.char = char or "Ranger"
        self.is_bot = is_bot
        self.hp = 100
        self.max_hp = 100
        self.alive = True
        self.speed = 140 if self.char != "Knight" else 120
        self.radius = 14
        self.facing_left = False
        self.anim_timer = 0.0
        self.anim_frame = 0
        self.anim_speed = 6.0
        self.shoot_flash = 0.0

        # class-specific
        if self.char == "Knight":
            self.fire_cooldown = 0.5
            self.attack_range = 80
            self.attack_arc = 90
            self.swing_duration = 0.2
            self.swing_timer = 0.0
        elif self.char == "Ranger":
            self.fire_cooldown = 0.35
            self.attack_range = 900
            self.spread = 0.04
        else:  # Wizard
            self.fire_cooldown = 0.8
            self.attack_range = 500
            self.burst_count = 3
            self.burst_spread = 0.2
            self.burst_delay = 0.1
            self.remaining_burst = 0
            self.burst_timer = 0.0

        self.fire_timer = 0.0
        self.kills = 0
        self.has_bomb = False
        self.attack_frame = 0
        self.attack_effect = None

    def update(self, dt: float, controls: dict, game, frozen: bool = False):
        if not self.alive:
            return

        self.anim_timer += dt
        frames = game.anim_frames.get(self.char)
        if frames:
            self.anim_frame = int(self.anim_timer * self.anim_speed) % len(frames)

        self.fire_timer = max(0.0, self.fire_timer - dt)
        self.shoot_flash = max(0.0, self.shoot_flash - dt)

        if self.char == "Knight":
            self.swing_timer = max(0.0, getattr(self, "swing_timer", 0.0) - dt)
            if self.swing_timer > 0:
                self.attack_frame = int((1 - self.swing_timer / self.swing_duration) * 3)
            else:
                self.attack_effect = None
        elif self.char == "Wizard":
            if getattr(self, "remaining_burst", 0) > 0:
                self.burst_timer = max(0.0, getattr(self, "burst_timer", 0.0) - dt)

        if frozen:
            return

        if not self.is_bot:
            dx = (1 if controls.get("right") else 0) - (1 if controls.get("left") else 0)
            dy = (1 if controls.get("down") else 0) - (1 if controls.get("up") else 0)
            if dx != 0 or dy != 0:
                if dx != 0 and dy != 0:
                    dx *= 0.7071
                    dy *= 0.7071
                move_speed = self.speed * dt
                dx *= move_speed
                dy *= move_speed
                if not is_solid(self.x + dx, self.y, self.radius, game.game_map):
                    self.x += dx
                if not is_solid(self.x, self.y + dy, self.radius, game.game_map):
                    self.y += dy
                if dx != 0:
                    self.facing_left = dx < 0
        else:
            self.bot_behavior(dt, game)

    def bot_behavior(self, dt, game):
        target = None
        min_dist = float('inf')
        for p in game.players:
            if p.team != self.team and p.alive:
                dist = math.hypot(p.x - self.x, p.y - self.y)
                if dist < min_dist:
                    min_dist = dist
                    target = p
        if not target:
            return
        vx, vy = target.x - self.x, target.y - self.y
        dist = math.hypot(vx, vy) or 1.0
        if dist > 120:
            dx = vx / dist
            dy = vy / dist
            nx = self.x + dx * self.speed * dt * 0.8
            ny = self.y + dy * self.speed * dt * 0.8
            if not is_solid(nx, self.y, self.radius, game.game_map):
                self.x = nx
            if not is_solid(self.x, ny, self.radius, game.game_map):
                self.y = ny
            self.facing_left = dx < 0
        if self.fire_timer <= 0 and dist < getattr(self, "attack_range", 400):
            aim_x = target.x + random.uniform(-18, 18)
            aim_y = target.y + random.uniform(-18, 18)
            self.fire(game.projectiles, (aim_x, aim_y))

    def take_damage(self, amt, attacker=None):
        if not self.alive:
            return
        self.hp -= amt
        if self.hp <= 0:
            self.alive = False
            if attacker and attacker is not self and attacker.alive:
                attacker.kills += 1

    def fire(self, projectile_list, target):
        if self.fire_timer > 0:
            return False
        dx, dy = target[0] - self.x, target[1] - self.y
        d = math.hypot(dx, dy) or 1
        base_angle = math.atan2(dy, dx)

        if self.char == "Knight":
            if d > self.attack_range:
                return False
            self.fire_timer = self.fire_cooldown
            self.swing_timer = self.swing_duration
            self.attack_frame = 0
            half_arc = math.radians(self.attack_arc / 2)
            start_angle = base_angle - half_arc
            hit_points = 8
            for i in range(hit_points):
                check_angle = start_angle + (half_arc * 2 * i / max(1, (hit_points - 1)))
                for dist_mult in [0.3, 0.6, 0.9]:
                    check_x = self.x + math.cos(check_angle) * self.attack_range * dist_mult
                    check_y = self.y + math.sin(check_angle) * self.attack_range * dist_mult
                    projectile_list.append(Projectile(
                        check_x, check_y, 0, 0, 40, owner=self,
                        life=0.15, radius=15, is_melee=True,
                        color=(255, 255, 255)
                    ))
        elif self.char == "Ranger":
            self.fire_timer = self.fire_cooldown
            angle = base_angle + random.uniform(-self.spread, self.spread)
            speed = 820.0
            vx, vy = math.cos(angle) * speed, math.sin(angle) * speed
            projectile_list.append(Projectile(
                self.x, self.y, vx, vy, 22, owner=self,
                color=(60, 220, 60), radius=4
            ))
        else:  # Wizard - burst
            if getattr(self, "remaining_burst", 0) <= 0:
                self.fire_timer = self.fire_cooldown
                self.remaining_burst = self.burst_count
                self.burst_timer = 0
            if getattr(self, "burst_timer", 0) <= 0 and self.remaining_burst > 0:
                spread_angle = base_angle + random.uniform(-self.burst_spread, self.burst_spread)
                speed = 520.0
                vx, vy = math.cos(spread_angle) * speed, math.sin(spread_angle) * speed
                projectile_list.append(Projectile(
                    self.x, self.y, vx, vy, 30, owner=self,
                    color=(100, 100, 255), radius=8,
                    life=1.5
                ))
                self.remaining_burst -= 1
                self.burst_timer = self.burst_delay

        self.shoot_flash = 0.08
        return True

    def draw(self, surf, anim_frames, cam_x=0, cam_y=0):
        frames = anim_frames.get(self.char)
        screen_x = int(self.x - cam_x)
        screen_y = int(self.y - cam_y)
        
        if frames:
            frame = frames[self.anim_frame % len(frames)]
            img = pygame.transform.flip(frame, self.facing_left, False) if self.facing_left else frame
            if self.shoot_flash > 0:
                if self.char == "Ranger":
                    img = tint_surface(img, (120, 255, 120), alpha=90)
                elif self.char == "Wizard":
                    img = tint_surface(img, (120, 120, 255), alpha=90)
                else:
                    img = tint_surface(img, (255, 230, 180), alpha=90)
            rect = img.get_rect(center=(screen_x, screen_y))
            surf.blit(img, rect)
        else:
            col = ATT_COL if self.team == "A" else DEF_COL
            pygame.draw.circle(surf, col, (screen_x, screen_y), self.radius)
            if self.shoot_flash > 0:
                pygame.draw.circle(surf, (255, 220, 180), (screen_x, screen_y), self.radius, 2)

        # Health bar
        hp_ratio = max(0, self.hp) / self.max_hp
        bar_w, bar_h = 42, 4
        bx = int(screen_x - bar_w / 2)
        by = int(screen_y - SPRITE_SIZE // 2 - 12)
        pygame.draw.rect(surf, UI_BG_DARK, (bx, by, bar_w, bar_h), border_radius=2)
        if hp_ratio > 0:
            health_width = int(bar_w * hp_ratio)
            if health_width < 2:
                health_width = 2
            if hp_ratio > 0.6:
                color = SUCCESS_LIGHT
            elif hp_ratio > 0.3:
                color = YELLOW
            else:
                color = DANGER_LIGHT
            pygame.draw.rect(surf, color, (bx, by, health_width, bar_h), border_radius=2)

        # Bomb indicator - show icon above player with bomb
        if getattr(self, 'has_bomb', False):
            # Position above the player's head
            indicator_y = screen_y - SPRITE_SIZE // 2 - 24
            
            # Draw pulsing background circle
            pulse = (math.sin(pygame.time.get_ticks() * 0.005) + 1) / 2  # 0 to 1
            circle_radius = 10 + int(pulse * 2)
            pygame.draw.circle(surf, (80, 40, 20, 200), (screen_x, indicator_y), circle_radius)
            pygame.draw.circle(surf, YELLOW, (screen_x, indicator_y), circle_radius, 2)
            
            # Draw bomb symbol (simple geometric shape)
            # Draw bomb body
            pygame.draw.circle(surf, (60, 30, 15), (screen_x, indicator_y), 6)
            # Draw fuse
            pygame.draw.line(surf, (40, 40, 40), (screen_x - 3, indicator_y - 5), (screen_x - 5, indicator_y - 8), 2)
            # Draw spark
            spark_color = (255, 200, 0) if int(pulse * 2) % 2 == 0 else (255, 100, 0)
            pygame.draw.circle(surf, spark_color, (screen_x - 5, indicator_y - 8), 2)