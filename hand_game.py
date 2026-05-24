import random
import cv2
from cvzone.HandTrackingModule import HandDetector
import math
import numpy as np
import cvzone
import time
import os
import json

# ─── Webcam ────────────────────────────────────────────────────────
cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

# ─── Hand Detector ─────────────────────────────────────────────────
detector = HandDetector(detectionCon=0.8, maxHands=1)

# ─── Kalibrasi Jarak ───────────────────────────────────────────────
x_cal = [300, 245, 200, 170, 145, 130, 112, 103, 93, 87, 80, 75, 70, 67, 62, 59, 57]
y_cal = [20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100]
coff = np.polyfit(x_cal, y_cal, 2)


# ══════════════════════════════════════════════════════════════════
#  PARTICLE SYSTEM
# ══════════════════════════════════════════════════════════════════
class Particle:
    def __init__(self, x, y, color):
        self.x = float(x)
        self.y = float(y)
        self.color = color
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(4, 12)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = 1.0
        self.decay = random.uniform(0.04, 0.09)
        self.radius = random.randint(4, 9)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.35      # gravitasi
        self.vx *= 0.98      # sedikit hambatan udara
        self.life -= self.decay
        self.radius = max(1, self.radius - 1)

    def draw(self, img):
        if self.life > 0:
            alpha = self.life
            color = tuple(int(c * alpha) for c in self.color)
            cv2.circle(img, (int(self.x), int(self.y)), self.radius, color, cv2.FILLED)


def spawn_particles(cx, cy, color, count=30):
    return [Particle(cx, cy, color) for _ in range(count)]


# ══════════════════════════════════════════════════════════════════
#  TARGET CLASS
# ══════════════════════════════════════════════════════════════════
class Target:
    def __init__(self, target_type="normal"):
        self.cx = random.randint(120, 1160)
        self.cy = random.randint(120, 580)
        self.target_type = target_type   # "normal" | "bonus" | "bomb"
        self.spawn_time = time.time()
        self.caught = False

        # Properti per tipe
        if target_type == "normal":
            self.radius = 30
            self.color = (255, 0, 255)
            self.points = 1
            self.lifetime = 5.0
        elif target_type == "bonus":
            self.radius = 25
            self.color = (0, 165, 255)   # oranye-emas
            self.points = 3
            self.lifetime = 3.5
        elif target_type == "bomb":
            self.radius = 28
            self.color = (30, 30, 220)
            self.points = -2
            self.lifetime = 6.0

        self.active = True
        self.armed = False   # True = tangan pernah dekat (<40cm) & overlap target

    # ── Update: hanya cek countdown, target tidak bergerak ────────
    def update(self):
        # Target diam di tempat, hanya cek apakah countdown habis
        if time.time() - self.spawn_time > self.lifetime:
            self.active = False

    # ── Deteksi tangkapan tangan ──────────────────────────────────
    def check_catch(self, hx, hy, hw, hh):
        return hx < self.cx < hx + hw and hy < self.cy < hy + hh

    # ── Gambar target ─────────────────────────────────────────────
    def draw(self, img):
        if not self.active:
            return

        # Timer ring (menyusut seiring waktu)
        elapsed = time.time() - self.spawn_time
        remaining = max(0.0, 1.0 - elapsed / self.lifetime)
        outer_r = self.radius + 16
        cv2.circle(img, (self.cx, self.cy), outer_r, (70, 70, 70), 2)
        sweep = int(360 * remaining)
        ring_color = {
            "normal": (100, 255, 100),
            "bonus":  (0, 200, 255),
            "bomb":   (50, 50, 255),
        }[self.target_type]
        cv2.ellipse(img, (self.cx, self.cy), (outer_r, outer_r),
                    -90, 0, sweep, ring_color, 3)

        if self.target_type == "bomb":
            cv2.circle(img, (self.cx, self.cy), self.radius, self.color, cv2.FILLED)
            cv2.circle(img, (self.cx, self.cy), self.radius, (0, 0, 120), 3)
            # Tanda X
            d = 11
            cv2.line(img, (self.cx-d, self.cy-d), (self.cx+d, self.cy+d), (255,255,255), 3)
            cv2.line(img, (self.cx+d, self.cy-d), (self.cx-d, self.cy+d), (255,255,255), 3)
            # Label
            cv2.putText(img, "BOMB", (self.cx-24, self.cy+40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 100, 100), 2)

        elif self.target_type == "bonus":
            cv2.circle(img, (self.cx, self.cy), self.radius, self.color, cv2.FILLED)
            cv2.circle(img, (self.cx, self.cy), 10, (255, 255, 255), cv2.FILLED)
            cv2.circle(img, (self.cx, self.cy), 20, (255, 255, 255), 2)
            cv2.circle(img, (self.cx, self.cy), self.radius, (30, 30, 30), 2)
            cv2.putText(img, "+3", (self.cx-16, self.cy+42),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)

        else:  # normal
            # Warna hijau saat catch_counter aktif (charging) — sama seperti asli
            draw_color = (0, 255, 0) if self.armed else self.color
            cv2.circle(img, (self.cx, self.cy), self.radius, draw_color, cv2.FILLED)
            cv2.circle(img, (self.cx, self.cy), 10, (255, 255, 255), cv2.FILLED)
            cv2.circle(img, (self.cx, self.cy), 20, (255, 255, 255), 2)
            cv2.circle(img, (self.cx, self.cy), self.radius, (50, 50, 50), 2)


# ══════════════════════════════════════════════════════════════════
#  SCREEN FLASH
# ══════════════════════════════════════════════════════════════════
class ScreenFlash:
    def __init__(self):
        self.active = False
        self.color = (0, 255, 0)
        self.start = 0.0
        self.duration = 0.25

    def trigger(self, color):
        self.active = True
        self.color = color
        self.start = time.time()

    def apply(self, img):
        if not self.active:
            return img
        elapsed = time.time() - self.start
        if elapsed >= self.duration:
            self.active = False
            return img
        alpha = 0.45 * (1.0 - elapsed / self.duration)
        overlay = np.full_like(img, self.color[::-1])   # BGR
        return cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)


# ══════════════════════════════════════════════════════════════════
#  HAND TRAIL
# ══════════════════════════════════════════════════════════════════
class HandTrail:
    def __init__(self, max_len=22):
        self.points = []
        self.max_len = max_len

    def add(self, x, y):
        self.points.append((x, y, time.time()))
        if len(self.points) > self.max_len:
            self.points.pop(0)

    def draw(self, img):
        now = time.time()
        for i, (x, y, t) in enumerate(self.points):
            age = now - t
            if age < 0.45:
                a = 1.0 - age / 0.45
                r = max(1, int(9 * a))
                frac = i / max(1, self.max_len)
                color = (int(80 + 175 * a), int(255 * a * frac), int(200 * a))
                cv2.circle(img, (x, y), r, color, cv2.FILLED)


# ══════════════════════════════════════════════════════════════════
#  LEADERBOARD
# ══════════════════════════════════════════════════════════════════
LB_FILE = "leaderboard.json"

def load_leaderboard():
    if os.path.exists(LB_FILE):
        with open(LB_FILE, "r") as f:
            return json.load(f)
    return []

def save_score(score):
    board = load_leaderboard()
    board.append({"score": score, "date": time.strftime("%d/%m %H:%M")})
    board = sorted(board, key=lambda e: e["score"], reverse=True)[:5]
    with open(LB_FILE, "w") as f:
        json.dump(board, f)
    return board


# ══════════════════════════════════════════════════════════════════
#  RESET STATE
# ══════════════════════════════════════════════════════════════════
def reset_game():
    return {
        "targets":      [Target("normal")],
        "particles":    [],
        "score":        0,
        "lives":        3,
        "combo":        0,
        "combo_timer":  time.time(),
        "timeStart":    time.time(),
        "totalTime":    30,
        "bonus_timer":  time.time(),
        "bomb_timer":   time.time() + 5,   # delay bomb pertama
        "game_over":    False,
        "leaderboard":  None,
        "is_new_high":  False,
    }


# ══════════════════════════════════════════════════════════════════
#  MAIN LOOP
# ══════════════════════════════════════════════════════════════════
flash = ScreenFlash()
trail = HandTrail()
state = reset_game()

MEDAL_COLORS = [(0, 215, 255), (180, 180, 180), (30, 100, 210), (200, 200, 200), (200, 200, 200)]

while True:
    success, img = cap.read()
    img = cv2.flip(img, 1)

    time_left = state["totalTime"] - (time.time() - state["timeStart"])
    alive      = time_left > 0 and state["lives"] > 0

    # ──────────────────────────────────────────────────────────────
    #  GAMEPLAY
    # ──────────────────────────────────────────────────────────────
    if alive:
        now = time.time()

        # Spawn bonus target setiap 9 detik
        if now - state["bonus_timer"] > 9:
            state["targets"].append(Target("bonus"))
            state["bonus_timer"] = now

        # Spawn bomb setiap 7 detik (setelah skor ≥ 3)
        if now - state["bomb_timer"] > 7 and state["score"] >= 3:
            state["targets"].append(Target("bomb"))
            state["bomb_timer"] = now

        # ── Deteksi tangan ─────────────────────────────────────
        hands, img = detector.findHands(img, draw=False)
        distanceCM = 999

        if hands:
            hand   = hands[0]
            lmList = hand['lmList']
            hx, hy, hw, hh = hand['bbox']

            x1, y1 = lmList[5][:2]
            x2, y2 = lmList[17][:2]
            dist_px = int(math.sqrt((y2 - y1)**2 + (x2 - x1)**2))
            A, B, C = coff
            distanceCM = A * dist_px**2 + B * dist_px + C

            # Trail jejak tangan
            trail.add(hx + hw // 2, hy + hh // 2)

            cv2.rectangle(img, (hx, hy), (hx + hw, hy + hh), (255, 0, 255), 3)
            cvzone.putTextRect(img, f'{int(distanceCM)} cm', (hx + 5, hy - 10))

            # ── Mekanisme skor (selain bomb) ──────────────────────────
            #
            # Syarat point:
            #   1. Tangan MENDEKAT (distanceCM < 40) + overlap target
            #      → target.armed = True  (target berubah warna hijau)
            #   2. Tangan MENJAUH (distanceCM >= 40), masih dalam frame
            #      → skor terdaftar untuk semua target yang armed
            #
            # Bomb: langsung meledak saat disentuh dekat (tidak perlu armed/menjauh).
            if distanceCM < 40:
                # Tangan dekat → cek overlap, tandai armed
                for target in state["targets"]:
                    if not target.active:
                        continue
                    if target.check_catch(hx, hy, hw, hh):
                        if target.target_type == "bomb":
                            # Bomb langsung meledak saat disentuh dekat
                            target.active = False
                            target.caught = True
                            state["lives"] -= 1
                            state["combo"]  = 0
                            flash.trigger((0, 0, 200))
                            state["particles"] += spawn_particles(
                                target.cx, target.cy, (50, 50, 255), 25)
                        else:
                            # Normal/Bonus: tandai armed, tunggu tangan menjauh
                            target.armed = True
            else:
                # Tangan menjauh >= 40cm (masih dalam frame) →
                # semua target yang armed langsung terhitung poin
                for target in state["targets"]:
                    if target.active and target.armed:
                        target.active = False
                        target.caught = True
                        state["combo"] += 1
                        state["combo_timer"] = now
                        multiplier = min(state["combo"], 4)
                        gained = target.points * multiplier
                        state["score"] = max(0, state["score"] + gained)
                        flash.trigger((0, 200, 0))
                        p_col = (30, 180, 255) if target.target_type == "bonus"                                 else (255, 80, 255)
                        state["particles"] += spawn_particles(
                            target.cx, target.cy, p_col, 30)
                        state["targets"].append(Target("normal"))

        # Combo reset jika idle 3 detik
        if state["combo"] > 0 and now - state["combo_timer"] > 3.0:
            state["combo"] = 0

        # ── Update & filter targets ────────────────────────────
        surviving = []
        for t in state["targets"]:
            t.update()
            if not t.active and not t.caught:
                # Normal yang expire → nyawa berkurang
                if t.target_type == "normal":
                    state["lives"] -= 1
                    flash.trigger((0, 0, 140))
                # Bomb expire → bebas (tidak kena hukuman)
            if t.active:
                surviving.append(t)

        # Pastikan minimal 1 normal selalu ada
        if not any(t.target_type == "normal" for t in surviving):
            surviving.append(Target("normal"))
        state["targets"] = surviving

        # ── Update particles ───────────────────────────────────
        for p in state["particles"]:
            p.update()
        state["particles"] = [p for p in state["particles"] if p.life > 0]

        # ── Draw layer ─────────────────────────────────────────
        trail.draw(img)
        for p in state["particles"]:
            p.draw(img)
        for t in state["targets"]:
            t.draw(img)
        img = flash.apply(img)

        # ── HUD ────────────────────────────────────────────────
        # Timer bar
        bar_fill = int(800 * max(0, time_left / state["totalTime"]))
        cv2.rectangle(img, (240, 12), (1040, 42), (45, 45, 45), cv2.FILLED)
        if time_left > 10:
            bar_col = (50, 220, 50)
        elif time_left > 5:
            bar_col = (0, 165, 255)
        else:
            bar_col = (30, 30, 230)
        cv2.rectangle(img, (240, 12), (240 + bar_fill, 42), bar_col, cv2.FILLED)
        cvzone.putTextRect(img, f'{int(time_left)}s', (1050, 40), scale=2, offset=5)

        # Skor
        cvzone.putTextRect(img, f'Score: {str(state["score"]).zfill(2)}',
                           (20, 75), scale=3, offset=20)

        # Nyawa (lingkaran merah)
        for i in range(3):
            col = (0, 0, 220) if i < state["lives"] else (70, 70, 70)
            cx_h = 28 + i * 48
            cv2.circle(img, (cx_h, 148), 16, col, cv2.FILLED)
            cv2.circle(img, (cx_h, 148), 16, (200, 200, 200), 2)

        # Combo banner
        if state["combo"] >= 2:
            mult = min(state["combo"], 4)
            cvzone.putTextRect(img, f'COMBO  x{mult}!',
                               (490, 160), scale=3, offset=15, colorR=(0, 150, 255))

        # Legenda target (pojok kanan bawah)
        cv2.circle(img, (1060, 660), 8, (255, 0, 255), cv2.FILLED)
        cv2.putText(img, "+1", (1073, 665), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200,200,200), 2)
        cv2.circle(img, (1120, 660), 8, (0, 165, 255), cv2.FILLED)
        cv2.putText(img, "+3", (1133, 665), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200,200,200), 2)
        cv2.circle(img, (1180, 660), 8, (30, 30, 220), cv2.FILLED)
        cv2.putText(img, "-2", (1193, 665), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200,200,200), 2)

    # ──────────────────────────────────────────────────────────────
    #  GAME OVER SCREEN
    # ──────────────────────────────────────────────────────────────
    else:
        if not state["game_over"]:
            state["game_over"]   = True
            state["leaderboard"] = save_score(state["score"])
            board = state["leaderboard"]
            state["is_new_high"] = (len(board) > 0 and
                                    board[0]["score"] == state["score"] and
                                    state["score"] > 0)

        # Semi-dark overlay
        overlay = img.copy()
        cv2.rectangle(overlay, (180, 80), (1100, 670), (15, 15, 15), cv2.FILLED)
        img = cv2.addWeighted(overlay, 0.78, img, 0.22, 0)

        board = state["leaderboard"] or []

        # Judul
        if state["is_new_high"]:
            cvzone.putTextRect(img, '<<  NEW HIGH SCORE!  >>',
                               (210, 135), scale=3, offset=22,
                               thickness=4, colorR=(0, 170, 0))
        else:
            cvzone.putTextRect(img, 'GAME  OVER',
                               (430, 135), scale=4, offset=25,
                               thickness=5, colorR=(20, 20, 200))

        cvzone.putTextRect(img, f'Your Score :  {state["score"]}',
                           (440, 245), scale=3, offset=16)

        # Garis pemisah
        cv2.line(img, (260, 310), (1020, 310), (100, 100, 100), 2)

        # TOP 5
        cvzone.putTextRect(img, '=== TOP 5 LEADERBOARD ===',
                           (310, 340), scale=2, offset=10, colorR=(50, 50, 50))
        for i, entry in enumerate(board):
            y_pos   = 395 + i * 52
            is_cur  = entry["score"] == state["score"]
            col_r   = (0, 160, 0) if is_cur else (45, 45, 45)
            prefix  = ">>" if is_cur else f" {i+1}."
            cvzone.putTextRect(img,
                               f'{prefix}  {str(entry["score"]).zfill(3)} pts    {entry["date"]}',
                               (340, y_pos), scale=2, offset=9, colorR=col_r)

        # Instruksi
        cvzone.putTextRect(img, 'R = Restart       ESC = Quit',
                           (390, 640), scale=1.8, offset=10, colorR=(40, 40, 40))

    # ── Tampilkan frame ────────────────────────────────────────────
    cv2.imshow("Hand Target Game", img)
    key = cv2.waitKey(1)

    # Restart
    if key == ord('r'):
        state = reset_game()
        trail = HandTrail()

    # Keluar
    if key == 27:
        break

cap.release()
cv2.destroyAllWindows()
