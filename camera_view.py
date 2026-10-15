from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import sys
import time

os.environ.setdefault("GLOG_minloglevel", "2")

import cv2

from hand_detector import HandDetector

WINDOW_TITLE = "Camara - deteccion de mano  (pulsa q para cerrar)"

_out = sys.stdout


def connect_to_game(port):
    global _out
    s = socket.create_connection(("127.0.0.1", port), timeout=5.0)
    _out = s.makefile("w", encoding="utf-8")
    return s


def emit(obj):
    try:
        _out.write(json.dumps(obj) + "\n")
        _out.flush()
    except (BrokenPipeError, ValueError, OSError):
        pass


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Visor de cámara + detección de mano.")
    p.add_argument("--camera", type=int, default=0)
    p.add_argument("--no-mirror", action="store_true")
    p.add_argument("--max-hands", type=int, default=1)
    p.add_argument("--gesture", choices=["pinch", "open", "both"], default="pinch")
    p.add_argument("--pinch-threshold", type=float, default=0.25,
                   help="distancia pulgar-índice (relativa a la palma) para "
                        "considerar que hay pinza. Menor = más estricto.")
    p.add_argument("--no-window", action="store_true",
                   help="no abre la ventana de cámara (solo detecta).")
    p.add_argument("--camera-port", type=int, default=0,
                   help="puerto local del juego al que enviar los eventos "
                        "(0 = escribir por stdout).")
    p.add_argument("--width", type=int, default=640)
    p.add_argument("--height", type=int, default=480)
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    if args.camera_port:
        try:
            connect_to_game(args.camera_port)
        except OSError as exc:
            print(f"[camera_view] no se pudo conectar al juego: {exc}", file=sys.stderr)
            return 1

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        emit({"type": "status", "value": "error: no se pudo abrir la cámara"})
        return 1
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    try:
        detector = HandDetector(
            max_hands=args.max_hands,
            mode=args.gesture,
            pinch_enter=args.pinch_threshold,
            pinch_exit=args.pinch_threshold + 0.15,
        )
    except Exception as exc:
        emit({"type": "status", "value": f"error: {exc}"})
        cap.release()
        return 1

    emit({"type": "status", "value": "ok"})

    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

    last_gesture = None
    last_visible = None
    frame_id = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                time.sleep(0.03)
                continue

            if not args.no_mirror:
                frame = cv2.flip(frame, 1)

            detection = detector.process(frame, frame_id * 33)
            frame_id += 1

            if detection.flap:
                emit({"type": "flap"})

            visible = detection.hand_visible
            if detection.gesture != last_gesture or visible != last_visible:
                emit({
                    "type": "gesture",
                    "value": detection.gesture,
                    "hand": visible,
                    "fingers": detection.fingers,
                })
                last_gesture = detection.gesture
                last_visible = visible

            if not args.no_window:
                annotated = detector.annotate(frame, detection)
                cv2.imshow(WINDOW_TITLE, annotated)
                if (cv2.waitKey(1) & 0xFF) == ord("q"):
                    break
    except KeyboardInterrupt:
        pass
    finally:
        detector.close()
        cap.release()
        cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    sys.exit(main())
