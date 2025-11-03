"""
game.py
Main game logic and state management
"""

import pygame
import random
from typing import Optional, List
from src.player import Player
from src.projectile import Projectile
from src.bomb import Bomb
from src.map import generate_map, draw_map  # Added draw_map import
from src.utils import clamp, can_see
from src.config import (WIDTH, HEIGHT, MAP_W, MAP_H, TILE, MAP_TOP, CONFIG,
                    ASSET_PATHS)

class Game:
    def __init__(self, game_map, plant_zone, sprites, anim_frames):
        self.state = "TEAM_SELECT"
        self.round = 1
        self.scores = {"A": 0, "B": 0}
        self.attack_team = "A"
        self.round_time = 110.0
        self.between_timer = 0
        self.frozen = True
        self.side_swap_event = False

        self.players: List[Player] = []
        self.projectiles: List[Projectile] = []
        self.plant_zone = plant_zone
        self.bomb = Bomb(plant_zone)
        self.human_player: Optional[Player] = None

        self.camera_x = 0
        self.camera_y = MAP_TOP

        self.game_map = game_map
        self.sprites = sprites
        self.anim_frames = anim_frames

        self.spawn_points = {
            "A": (TILE * 2 + TILE // 2, TILE * 2 + TILE // 2 + MAP_TOP),
            "B": ((MAP_W - 3) * TILE + TILE // 2, (MAP_H - 3) * TILE + TILE // 2 + MAP_TOP)
        }

        self.selected_chars = {"A": None, "B": None}
        self.intro_start_ms = 0
        self.team_data = {
            'A': [("Player", None), ("Bot-A2", None)],
            'B': [("Bot", None), ("Bot-B2", None)]
        }

    def create_players(self):
        self.players = []
        a_spawn = self.spawn_points["A"]
        b_spawn = self.spawn_points["B"]

        pA = Player(a_spawn[0], a_spawn[1], "A", "Player", self.selected_chars["A"], is_bot=False)
        pB = Player(b_spawn[0], b_spawn[1], "B", "Bot", self.selected_chars["B"], is_bot=True)
        pA.has_bomb = True

        self.players.extend([pA, pB])
        self.human_player = pA
        self.projectiles.clear()
        self.bomb = Bomb(self.plant_zone)
        self.round_time = 110.0
        self.frozen = True
        self.intro_start_ms = pygame.time.get_ticks()
        self.state = "ROUND_INTRO"

    def end_round(self, winner_team, reason=""):
        self.scores[winner_team] += 1

        # handle side swap
        if self.round == CONFIG.SIDE_SWAP_ROUND:
            self.attack_team = "B" if self.attack_team == "A" else "A"
            self.side_swap_event = True

        # check match end
        if self.scores["A"] >= CONFIG.WIN_SCORE or self.scores["B"] >= CONFIG.WIN_SCORE:
            self.state = "MATCH_END"
        else:
            self.state = "ROUND_END"
            self.between_timer = pygame.time.get_ticks()
            # freeze players until next round reset
            self.frozen = True

    def reset_for_next_round(self):
        self.round += 1
        self.round_time = 110.0
        self.frozen = True
        self.projectiles.clear()
        # swap attack team if necessary handled on end_round already
        # recreate players, keep selected chars
        self.create_players()

    def update(self, dt, keys, mouse_buttons, mouse_pos):
        # Handle round intro freeze
        if self.state == "ROUND_INTRO":
            elapsed = pygame.time.get_ticks() - self.intro_start_ms
            if elapsed >= CONFIG.FREEZE_TIME_MS:
                self.frozen = False
                self.state = "PLAYING"
            return

        # handle round end wait
        if self.state == "ROUND_END":
            current_time = pygame.time.get_ticks()
            if current_time - self.between_timer > CONFIG.ROUND_END_WAIT_MS:
                self.reset_for_next_round()
            return

        if self.state == "MATCH_END":
            return

        if self.state == "PLAYING":
            # decrement round timer
            self.round_time -= dt
            self.round_time = max(0, self.round_time)
            if self.round_time <= 0:
                # time up => defenders win
                winner = "B" if self.attack_team == "A" else "A"
                self.end_round(winner, reason="Time up")
                return

            # update players
            for p in self.players:
                if not p.is_bot:
                    controls = {
                        "up": keys[pygame.K_w],
                        "down": keys[pygame.K_s],
                        "left": keys[pygame.K_a],
                        "right": keys[pygame.K_d]
                    }
                else:
                    controls = {}
                p.update(dt, controls, self, frozen=self.frozen)

            # player input: firing and interaction for human
            if self.human_player and self.human_player.alive and not self.frozen:
                if mouse_buttons[0]:
                    # primary fire
                    self.human_player.fire(self.projectiles, mouse_pos)
                
                # plant/defuse interaction - CHANGED TO K_4
                if keys[pygame.K_4]:
                    print(f"4 key pressed!")  # DEBUG
                    print(f"Player position: ({self.human_player.x}, {self.human_player.y})")  # DEBUG
                    print(f"Plant zone: {self.plant_zone}")  # DEBUG
                    print(f"In plant zone: {self.plant_zone.collidepoint(self.human_player.x, self.human_player.y)}")  # DEBUG
                    
                    # planting
                    if not self.bomb.planted and self.plant_zone.collidepoint(self.human_player.x, self.human_player.y):
                        # start planting
                        self.bomb.start_plant(self.human_player)
                    # defusing
                    elif self.bomb.planted and self.bomb.plant_done and self.plant_zone.collidepoint(self.human_player.x, self.human_player.y):
                        self.bomb.start_defuse(self.human_player)

            # update projectiles
            for pr in list(self.projectiles):
                pr.update(dt, self)
                if pr.life <= 0:
                    try:
                        self.projectiles.remove(pr)
                    except ValueError:
                        pass

            # update bomb
            bomb_event = self.bomb.update(dt, self)
            if bomb_event == "explosion":
                return

            # check elimination victory
            alive_a = sum(1 for p in self.players if p.team == "A" and p.alive)
            alive_b = sum(1 for p in self.players if p.team == "B" and p.alive)
            if alive_a == 0 and alive_b > 0:
                self.end_round("B", reason="Elimination")
            elif alive_b == 0 and alive_a > 0:
                self.end_round("A", reason="Elimination")

    def draw(self, surf, fonts):
        if self.state == "TEAM_SELECT":
            return

        hp = self.human_player
        if hp:
            self.camera_x = clamp(hp.x - WIDTH // 2, 0, MAP_W * TILE - WIDTH)
            self.camera_y = clamp(hp.y - HEIGHT // 2, MAP_TOP, MAP_H * TILE + MAP_TOP - HEIGHT)

        cam_x = int(self.camera_x)
        cam_y = int(self.camera_y)

        # FIXED: Draw the map!
        draw_map(surf, self.game_map, self.plant_zone, cam_x, cam_y)

        for p in self.players:
            # draw allies fully, enemies only if visible
            if p is self.human_player or p.team == self.human_player.team:
                p.draw(surf, self.anim_frames, cam_x, cam_y)
            elif can_see(self.human_player, p, self.game_map):
                p.draw(surf, self.anim_frames, cam_x, cam_y)

        for pr in self.projectiles:
            pr.draw(surf, cam_x, cam_y)

        self.bomb.draw(surf, fonts['FONT'], cam_x, cam_y)

        self._draw_hud(surf, fonts)

        # Round intro overlay
        if self.state == "ROUND_INTRO":
            self._draw_round_intro(surf, fonts)

    def _draw_hud(self, surf, fonts):
        from pygame import Surface
        from src.config import (UI_BG, UI_BG_LIGHT, MAP_TOP, WIDTH, HEIGHT,
                           GRAY, WHITE, ATT_COL_LIGHT, DEF_COL_LIGHT, DANGER_LIGHT)
        import math
        
        # Top HUD
        hud_height = MAP_TOP - 10
        hud_surface = Surface((WIDTH, hud_height), pygame.SRCALPHA)
        for y in range(hud_height):
            alpha = int(180 * (1 - y/hud_height * 0.6))
            pygame.draw.line(hud_surface, (*UI_BG[:3], alpha), (0, y), (WIDTH, y))
        surf.blit(hud_surface, (0, 0))

        # Round counter
        if fonts['SMALL']:
            round_txt = fonts['SMALL'].render(f"R{self.round}", True, GRAY)
            round_bg = Surface((round_txt.get_width() + 20, 24), pygame.SRCALPHA)
            pygame.draw.rect(round_bg, (*UI_BG_LIGHT, 160), (0, 0, round_bg.get_width(), 24), border_radius=12)
            surf.blit(round_bg, (16, 8))
            surf.blit(round_txt, (26, 12))

        # Score display
        score_width = 160
        score_x = WIDTH // 2 - score_width // 2
        score_height = 32
        score_rect = pygame.Rect(score_x, 4, score_width, score_height)
        score_bg = Surface((score_width, score_height), pygame.SRCALPHA)
        pygame.draw.rect(score_bg, (*UI_BG_LIGHT, 160), (0, 0, score_width, score_height), border_radius=16)
        surf.blit(score_bg, score_rect)

        a_score = fonts['BIG'].render(str(self.scores['A']), True, ATT_COL_LIGHT) if fonts['BIG'] else None
        b_score = fonts['BIG'].render(str(self.scores['B']), True, DEF_COL_LIGHT) if fonts['BIG'] else None

        if a_score:
            surf.blit(a_score, (score_x + score_width//4 - a_score.get_width()//2, 8))
        if b_score:
            surf.blit(b_score, (score_x + 3*score_width//4 - b_score.get_width()//2, 8))

        # Timer
        time_left = int(max(0, self.round_time))
        time_color = WHITE if time_left > 30 else DANGER_LIGHT
        time_txt = fonts['FONT'].render(f"{time_left:02d}", True, time_color) if fonts['FONT'] else None

        if time_txt:
            timer_width = time_txt.get_width() + 20
            timer_height = 24
            timer_bg = Surface((timer_width, timer_height), pygame.SRCALPHA)
            pygame.draw.rect(timer_bg, (*UI_BG_LIGHT, 160), (0, 0, timer_width, timer_height), border_radius=12)
            timer_x = WIDTH - timer_width - 16
            surf.blit(timer_bg, (timer_x, 8))
            surf.blit(time_txt, (timer_x + 10, 10))

    def _draw_round_intro(self, surf, fonts):
        from pygame import Surface
        from src.config import WIDTH, HEIGHT, WHITE, ATT_COL, DEF_COL, CONFIG
        import math
        
        elapsed = pygame.time.get_ticks() - self.intro_start_ms
        remaining = max(0, math.ceil((CONFIG.FREEZE_TIME_MS - elapsed) / 1000.0))
        overlay = Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surf.blit(overlay, (0, 0))
        if fonts['BIG'] and fonts['FONT']:
            txt = fonts['BIG'].render(f"ROUND {self.round}", True, WHITE)
            surf.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 50))
            team_name = "ATTACKERS" if self.human_player.team == self.attack_team else "DEFENDERS"
            team_color = ATT_COL if self.human_player.team == self.attack_team else DEF_COL
            team_txt = fonts['FONT'].render(team_name, True, team_color)
            surf.blit(team_txt, (WIDTH // 2 - team_txt.get_width() // 2, HEIGHT // 2 - 10))
            sub = fonts['BIG'].render(str(remaining), True, WHITE)
            surf.blit(sub, (WIDTH // 2 - sub.get_width() // 2, HEIGHT // 2 + 20))