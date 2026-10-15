from __future__ import annotations

import math

import pygame

import settings as S
from bird import Bird
from fonts import load_font
from pipe import PipePair

STATE_READY = "listo"
STATE_PLAYING = "jugando"
STATE_GAMEOVER = "game over"


class Game:

    def __init__(self, high_score=0):
        self.bird = Bird()
        self.pipes = []
        self.score = 0
        self.high_score = high_score
        self.state = STATE_READY
        self.font = load_font(42, bold=True)
        self.small_font = load_font(22, bold=True)
        self.control_hint = "Pulsa ESPACIO"

        self._distance = 0.0
        self._scroll = 0.0

    def on_flap(self):
        if self.state == STATE_READY:
            self.state = STATE_PLAYING
            self.bird.flap()
        elif self.state == STATE_PLAYING:
            self.bird.flap()

    def on_restart(self):
        if self.state == STATE_GAMEOVER:
            self.reset()

    def reset(self):
        self.bird.reset()
        self.pipes.clear()
        self.score = 0
        self.state = STATE_READY
        self._distance = 0.0
        self._scroll = 0.0

    def update(self):
        if self.state != STATE_PLAYING:
            if self.state == STATE_READY:
                self.bird.rect.y = S.BIRD_START_Y + int(
                    6 * math.sin(pygame.time.get_ticks() / 250.0)
                )
            return

        self.bird.update()
        self._scroll = (self._scroll - S.PIPE_SPEED) % 40

        self._distance += S.PIPE_SPEED
        if self._distance >= S.PIPE_SPAWN_DISTANCE:
            self._distance -= S.PIPE_SPAWN_DISTANCE
            self.pipes.append(PipePair(S.WIDTH + 10))

        for pipe in self.pipes:
            pipe.update()
            if not pipe.passed and pipe.right < self.bird.rect.left:
                pipe.passed = True
                self.score += 1
                self.high_score = max(self.high_score, self.score)

        self.pipes = [p for p in self.pipes if not p.offscreen()]

        self._check_collisions()

    def _check_collisions(self):
        if self.bird.rect.top <= 0:
            self.bird.rect.top = 0
            self._game_over()
            return

        ground_y = S.HEIGHT - S.GROUND_HEIGHT
        if self.bird.rect.bottom >= ground_y:
            self.bird.rect.bottom = ground_y
            self._game_over()
            return

        for pipe in self.pipes:
            if pipe.collides(self.bird.rect):
                self._game_over()
                return

    def _game_over(self):
        self.state = STATE_GAMEOVER
        self.high_score = max(self.high_score, self.score)

    def draw(self, surface):
        surface.fill(S.COLOR_SKY)

        for cx, cy, r in self._clouds():
            pygame.draw.circle(surface, (255, 255, 255), (cx, cy), r)
            pygame.draw.circle(surface, (255, 255, 255), (cx + r, cy + 4), int(r * 0.8))
            pygame.draw.circle(surface, (255, 255, 255), (cx - r, cy + 4), int(r * 0.7))

        for pipe in self.pipes:
            pipe.draw(surface)

        self.bird.draw(surface)
        self._draw_ground(surface)

        if self.state == STATE_READY:
            self._draw_centered(surface, self.control_hint, S.HEIGHT // 2 - 120)
            self._draw_centered(surface, "para empezar", S.HEIGHT // 2 - 70,
                                self.small_font)
        elif self.state == STATE_GAMEOVER:
            self._draw_centered(surface, "Game Over", S.HEIGHT // 2 - 200)
            self._draw_centered(surface, self.control_hint, S.HEIGHT // 2 + 140,
                                self.small_font)
            self._draw_centered(surface, "para reiniciar", S.HEIGHT // 2 + 168,
                                self.small_font)

        self._draw_score(surface)

    def _draw_ground(self, surface):
        ground_y = S.HEIGHT - S.GROUND_HEIGHT
        pygame.draw.rect(surface, S.COLOR_GROUND, (0, ground_y, S.WIDTH, S.GROUND_HEIGHT))
        pygame.draw.rect(surface, S.COLOR_GROUND_DARK, (0, ground_y, S.WIDTH, 12))
        for i in range(-1, S.WIDTH // 40 + 2):
            x = int(i * 40 + self._scroll)
            pygame.draw.rect(surface, S.COLOR_GROUND_DARK, (x, ground_y + 20, 20, 10))

    def _draw_score(self, surface):
        text = self.font.render(str(self.score), True, S.COLOR_TEXT)
        shadow = self.font.render(str(self.score), True, S.COLOR_TEXT_SHADOW)
        rect = text.get_rect(center=(S.WIDTH // 2, 70))
        surface.blit(shadow, rect.move(2, 2))
        surface.blit(text, rect)

        hs = self.small_font.render(f"Mejor: {self.high_score}", True, S.COLOR_TEXT_SHADOW)
        surface.blit(hs, (12, 10))

    def _draw_centered(self, surface, message, y, font=None):
        font = font or self.font
        text = font.render(message, True, S.COLOR_TEXT)
        shadow = font.render(message, True, S.COLOR_TEXT_SHADOW)
        rect = text.get_rect(center=(S.WIDTH // 2, y))
        pad = 10
        bg = pygame.Surface((rect.width + pad * 2, rect.height + pad), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 90))
        surface.blit(bg, (rect.x - pad, rect.y - pad // 2))
        surface.blit(shadow, rect.move(2, 2))
        surface.blit(text, rect)

    def _clouds(self):
        t = pygame.time.get_ticks() / 1000.0
        clouds = []
        for i, (base_y, speed, r) in enumerate([(90, 18, 26), (180, 12, 20), (60, 24, 18)]):
            x = int((S.WIDTH + 100 - (t * speed + i * 180)) % (S.WIDTH + 200)) - 100
            clouds.append((x, base_y, r))
        return clouds
