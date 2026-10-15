import random

import pygame

import settings as S


class PipePair:

    def __init__(self, x):
        playable = S.HEIGHT - S.GROUND_HEIGHT
        top_max = playable - S.PIPE_GAP - S.PIPE_MIN_BOTTOM
        self.gap_y = random.randint(S.PIPE_MIN_TOP, max(S.PIPE_MIN_TOP, top_max))
        self.gap_height = S.PIPE_GAP
        self.x = float(x)
        self.passed = False
        self._update_rects()

    def _update_rects(self):
        ix = int(self.x)
        self.top_rect = pygame.Rect(ix, 0, S.PIPE_WIDTH, self.gap_y)
        bottom_y = self.gap_y + self.gap_height
        self.bottom_rect = pygame.Rect(
            ix, bottom_y, S.PIPE_WIDTH, S.HEIGHT - S.GROUND_HEIGHT - bottom_y
        )

    def update(self):
        self.x -= S.PIPE_SPEED
        self._update_rects()

    @property
    def right(self):
        return self.x + S.PIPE_WIDTH

    def offscreen(self):
        return self.right < 0

    def collides(self, bird_rect):
        return bird_rect.colliderect(self.top_rect) or bird_rect.colliderect(self.bottom_rect)

    def draw(self, surface):
        self._draw_pipe(surface, self.top_rect, is_top=True)
        self._draw_pipe(surface, self.bottom_rect, is_top=False)

    @staticmethod
    def _draw_pipe(surface, rect, is_top):
        pygame.draw.rect(surface, S.COLOR_PIPE, rect)
        pygame.draw.rect(surface, S.COLOR_PIPE_DARK,
                         (rect.right - 14, rect.y, 14, rect.height))
        pygame.draw.rect(surface, S.COLOR_PIPE_OUTLINE, rect, 3)

        lip_h = 26
        if is_top:
            lip = pygame.Rect(rect.x - 4, rect.bottom - lip_h, rect.width + 8, lip_h)
        else:
            lip = pygame.Rect(rect.x - 4, rect.y, rect.width + 8, lip_h)
        pygame.draw.rect(surface, S.COLOR_PIPE, lip)
        pygame.draw.rect(surface, S.COLOR_PIPE_DARK,
                         (lip.right - 18, lip.y + 3, 14, lip.height - 6))
        pygame.draw.rect(surface, S.COLOR_PIPE_OUTLINE, lip, 3)
