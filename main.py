from __future__ import annotations

import argparse
import json
import os
import sys

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

import settings as S
from fonts import load_font
from game import Game, STATE_GAMEOVER

HIGHSCORE_FILE = os.path.join(os.path.dirname(__file__), "highscore.json")


def load_highscore():
    try:
        with open(HIGHSCORE_FILE, "r", encoding="utf-8") as fh:
            return int(json.load(fh).get("high_score", 0))
    except (OSError, ValueError):
        return 0


def save_highscore(score):
    try:
        with open(HIGHSCORE_FILE, "w", encoding="utf-8") as fh:
            json.dump({"high_score": int(score)}, fh)
    except OSError:
        pass


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Flappy Bird controlado con gestos de la mano (visión artificial)."
    )
    parser.add_argument("--camera", type=int, default=0,
                        help="índice de la webcam (por defecto 0).")
    parser.add_argument("--no-vision", action="store_true",
                        help="desactiva la cámara y juega solo con el teclado.")
    parser.add_argument("--no-mirror", action="store_true",
                        help="no espejar la imagen de la cámara.")
    parser.add_argument("--no-camera-window", action="store_true",
                        help="no abrir la ventana de la cámara (solo detecta).")
    parser.add_argument("--max-hands", type=int, default=1,
                        help="número máximo de manos a detectar (por defecto 1).")
    parser.add_argument("--gesture", choices=["pinch", "open", "both"], default="pinch",
                        help="gesto para aletear: 'pinch' (juntar pulgar e índice), "
                             "'open' (abrir la mano) o 'both' (por defecto: pinch).")
    parser.add_argument("--pinch-threshold", type=float, default=0.25,
                        help="distancia pulgar-índice (relativa a la palma) para la "
                             "pinza. Menor = hay que juntar más los dedos (0.25).")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    pygame.init()
    pygame.display.set_caption(S.TITLE)
    screen = pygame.display.set_mode((S.WIDTH, S.HEIGHT))
    clock = pygame.time.Clock()

    game = Game(high_score=load_highscore())
    gesto_corto = {"pinch": "Junta pulgar e índice",
                   "open": "Abre la mano",
                   "both": "Pinza o abre la mano"}[args.gesture]
    game.control_hint = gesto_corto if not args.no_vision else "Pulsa ESPACIO"

    vision = None
    if not args.no_vision:
        try:
            from vision import VisionProcess
        except ImportError as exc:
            print(f"[aviso] No se pudo cargar la visión artificial: {exc}")
            print("[aviso] Se jugará solo con el teclado.")
        else:
            vision = VisionProcess(
                camera=args.camera,
                mirror=not args.no_mirror,
                max_hands=args.max_hands,
                gesture=args.gesture,
                pinch_threshold=args.pinch_threshold,
                window=not args.no_camera_window,
            )
            vision.start()
            gesto = {"pinch": "junta el pulgar y el índice",
                     "open": "abre la mano",
                     "both": "junta pulgar e índice o abre la mano"}[args.gesture]
            print(f"[info] Cámara iniciada. Para aletear: {gesto}.")
            print("[info] La pinza también inicia y reinicia la partida.")

    def do_flap():
        if game.state == STATE_GAMEOVER:
            game.on_restart()
        game.on_flap()

    running = True
    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key in (pygame.K_SPACE, pygame.K_UP):
                        do_flap()
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        game.on_restart()

            if vision is not None and vision.poll():
                do_flap()

            game.update()
            game.draw(screen)
            _draw_hud(screen, vision)
            pygame.display.flip()
            clock.tick(S.FPS)
    finally:
        if vision is not None:
            vision.stop()
        save_highscore(game.high_score)
        pygame.quit()

    return 0


_hud_font = None


def _draw_hud(screen, vision):
    global _hud_font
    if _hud_font is None:
        _hud_font = load_font(18, bold=True)
    font = _hud_font
    if vision is None:
        text = "Modo teclado  (ESPACIO para aletear)"
    elif vision.status != "ok":
        text = f"Visión: {vision.status}  (usa ESPACIO)"
    else:
        state = "mano detectada" if vision.hand_visible else "sin mano"
        text = f"Visión: {vision.gesture} | {state}"
    shadow = font.render(text, True, S.COLOR_TEXT_SHADOW)
    label = font.render(text, True, S.COLOR_TEXT)
    y = S.HEIGHT - S.GROUND_HEIGHT + 28
    screen.blit(shadow, (42, y + 1))
    screen.blit(label, (41, y))


if __name__ == "__main__":
    if "--run-camera-process" in sys.argv:
        from camera_view import main as camera_main
        rest = [a for a in sys.argv[1:] if a != "--run-camera-process"]
        sys.exit(camera_main(rest))
    sys.exit(main())
