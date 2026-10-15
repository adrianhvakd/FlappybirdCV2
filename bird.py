import math

import pygame

import settings as S


class Bird:

    def __init__(self):
        self.rect = pygame.Rect(S.BIRD_X, S.BIRD_START_Y, S.BIRD_WIDTH, S.BIRD_HEIGHT)
        self.velocity = 0.0
        self.angle = 0.0
        self._flap_anim = 0.0

    def flap(self):
        self.velocity = S.FLAP_VELOCITY
        self._flap_anim = 1.0

    def update(self):
        self.velocity = min(self.velocity + S.GRAVITY, S.MAX_FALL_SPEED)
        self.rect.y += int(self.velocity)

        target = max(-80.0, min(80.0, -self.velocity * 6.0))
        self.angle += (target - self.angle) * 0.25

        if self._flap_anim > 0:
            self._flap_anim = max(0.0, self._flap_anim - 0.08)

    def reset(self):
        self.rect.y = S.BIRD_START_Y
        self.velocity = 0.0
        self.angle = 0.0
        self._flap_anim = 0.0

    def draw(self, surface):
        w, h = self.rect.width + 24, self.rect.height + 24
        img = pygame.Surface((w, h), pygame.SRCALPHA)
        self._draw_parts(img, w, h)
        rotated = pygame.transform.rotate(img, -self.angle)
        rect = rotated.get_rect(center=self.rect.center)
        surface.blit(rotated, rect.topleft)

    def _draw_parts(self, img, w, h):
        cx, cy = w // 2, h // 2
        body = pygame.Rect(cx - S.BIRD_WIDTH // 2, cy - S.BIRD_HEIGHT // 2,
                           S.BIRD_WIDTH, S.BIRD_HEIGHT)
        radius = S.BIRD_HEIGHT // 2

        pygame.draw.ellipse(img, S.COLOR_BIRD, body)
        pygame.draw.ellipse(img, S.COLOR_BIRD_OUTLINE, body, 2)

        flap_off = math.sin(self._flap_anim * math.pi) * 8
        wing = pygame.Rect(body.x + 6, body.centery - 4 + flap_off, 18, 12)
        pygame.draw.ellipse(img, (255, 236, 150), wing)
        pygame.draw.ellipse(img, S.COLOR_BIRD_OUTLINE, wing, 2)

        eye_x = body.right - 14
        eye_y = body.y + radius - 4
        pygame.draw.circle(img, (255, 255, 255), (eye_x, eye_y), 5)
        pygame.draw.circle(img, (30, 30, 30), (eye_x + 1, eye_y), 2)

        beak = [(body.right - 4, body.centery - 2),
                (body.right + 10, body.centery + 2),
                (body.right - 4, body.centery + 7)]
        pygame.draw.polygon(img, (240, 130, 40), beak)
        pygame.draw.polygon(img, (180, 90, 20), beak, 2)
