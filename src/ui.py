"""
ui.py
UI rendering for menus and selection screens
"""

import pygame
from src.config import (WIDTH, HEIGHT, UI_BG, UI_ACCENT_LIGHT, UI_BG_DARK,
                    WHITE, GRAY, ASSET_PATHS)

def draw_combined_select(surf, sel_index, sprites, fonts):
    surf.fill(UI_BG)
    if fonts['BIG']:
        title = fonts['BIG'].render("SELECT YOUR OPERATOR", True, WHITE)
        surf.blit(title, title.get_rect(center=(WIDTH//2, 40)))
    names = list(ASSET_PATHS.keys())
    if not names:
        return
    gap = WIDTH // (len(names) + 1)
    y = HEIGHT // 3
    for i, name in enumerate(names):
        x = gap * (i + 1)
        card_rect = pygame.Rect(x - 64, y - 80, 128, 160)
        bg_col = UI_ACCENT_LIGHT if i == sel_index else UI_BG_DARK
        pygame.draw.rect(surf, bg_col, card_rect, border_radius=8)
        img = sprites.get(name)
        if img:
            img_rect = img.get_rect(center=(x, y - 10))
            surf.blit(img, img_rect)
        if fonts['FONT']:
            name_text = fonts['FONT'].render(name, True, WHITE if i == sel_index else GRAY)
            surf.blit(name_text, name_text.get_rect(center=(x, y + 70)))
        if i == sel_index:
            pygame.draw.rect(surf, WHITE, card_rect, width=3, border_radius=8)
    if fonts['SMALL']:
        help_text = fonts['SMALL'].render("←/→ select  ·  ENTER confirm", True, GRAY)
        surf.blit(help_text, help_text.get_rect(center=(WIDTH//2, HEIGHT - 30)))