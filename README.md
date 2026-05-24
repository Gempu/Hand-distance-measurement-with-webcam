# 🖐️ Hand Gesture Catching Game

> A real-time hand tracking game built with Python, OpenCV, and CVZone — no controller needed, just your bare hand!

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green?style=for-the-badge&logo=opencv)
![CVZone](https://img.shields.io/badge/CVZone-latest-orange?style=for-the-badge)
![MediaPipe](https://img.shields.io/badge/MediaPipe-Google-red?style=for-the-badge)

---

## 🎮 Demo

> Move your hand in front of your webcam to catch targets, avoid bombs, and build combos!

---

## ✨ Features

- 🖐️ **Real-time hand detection** using CVZone & MediaPipe
- 📏 **Hand distance measurement** via quadratic calibration (NumPy polyfit)
- 🎯 **3 types of targets:**
  - 🟣 **Normal** — catch for +1 point (5 sec lifetime)
  - 🟠 **Bonus** — catch for +3 points (3.5 sec lifetime)
  - 🔴 **Bomb** — avoid! -2 points & combo reset (6 sec lifetime)
- 💥 **Particle explosion effects** with gravity & air resistance
- 🌟 **Hand trail effect** — glowing trail follows your hand
- ⚡ **Screen flash feedback** — green for catch, red for miss/bomb
- 🔥 **Combo multiplier system** — up to x4 multiplier!
- 🏆 **Persistent leaderboard** — Top 5 scores saved in JSON
- ⏱️ **Timer ring** on each target showing remaining lifetime
- 🔄 **Restart anytime** with `R` key

---

## 🛠️ Tech Stack

| Library | Purpose |
|---|---|
| `opencv-python` | Webcam capture & drawing all UI elements |
| `cvzone` | Simplified hand detection wrapper |
| `mediapipe` | AI hand landmark detection engine |
| `numpy` | Distance calibration (quadratic equation) |
| `json` | Persistent leaderboard storage |

---

## 📦 Installation

**1. Clone this repository**
```bash
git clone https://github.com/username/hand-gesture-game.git
cd hand-gesture-game
```

**2. Create & activate conda environment** *(recommended)*
```bash
conda create -n kuliah python=3.10
```

- Using **Command Prompt** (recommended for Windows):
```cmd
conda activate kuliah
```

- Using **PowerShell** (run once to initialize):
```powershell
conda init powershell
# Restart terminal, then:
conda activate kuliah
```

**3. Install dependencies**
```bash
pip install opencv-python cvzone mediapipe numpy
```

---

## ▶️ How to Run

```bash
python hand_game.py
```

Or with full path in VS Code terminal:
```cmd
python "C:\path\to\your\hand_game.py"
```

> ✅ Make sure your **webcam is connected** before running!

---

## 🎮 How to Play

| Action | Description |
|---|---|
| ✋ Move hand near target | Target turns **green** (armed) |
| 🤚 Pull hand away | Target is **caught** — score added! |
| 💣 Touch bomb | Lose **2 lives** + combo reset |
| ⏳ Miss a normal target | Lose **1 life** |
| 🔁 Press `R` | Restart the game |
| ❌ Press `ESC` | Quit the game |

---

## 🧠 How Distance Measurement Works

The game uses a **quadratic calibration curve** to estimate how far your hand is from the webcam:

```python
x_cal = [300, 245, 200, 170, ...]  # hand width in pixels
y_cal = [20,  25,  30,  35,  ...]  # actual distance in cm

coff = np.polyfit(x_cal, y_cal, 2)  # fit a quadratic equation
```

When playing, the hand width in pixels is measured from **landmark 5 to 17** (index finger base to pinky base), then plugged into the equation to get the estimated distance in centimeters.

A target is only **armed** when the hand is closer than **40 cm** from the camera — preventing accidental catches.

---

## 📁 Project Structure

```
hand-gesture-game/
│
├── hand_game.py        # Main game file
├── leaderboard.json    # Auto-generated after first play
└── README.md
```

---

## ⚙️ Game Configuration

You can tweak these values in `hand_game.py`:

| Variable | Default | Description |
|---|---|---|
| `totalTime` | `30` | Game duration (seconds) |
| `lives` | `3` | Starting lives |
| `detectionCon` | `0.8` | Hand detection confidence |
| `bonus_timer` | `9 sec` | Bonus target spawn interval |
| `bomb_timer` | `7 sec` | Bomb spawn interval |
| `max combo` | `x4` | Maximum combo multiplier |

---

## 💡 Ideas for Future Improvements

- [ ] Add sound effects (`pygame.mixer`)
- [ ] Moving targets with velocity
- [ ] Difficulty levels (more bombs at higher scores)
- [ ] Two-player mode (`maxHands=2`)
- [ ] Background music

---

## 📚 Built For

> 🎓 Final Project — *Pengolahan Citra Digital* (Digital Image Processing)  
> Semester 6 — Universitas / Politeknik

---

## 📺 Tutorial Video

Watch the full build tutorial on YouTube:  
**👉 [Your Webcam Can Measure Distance?! — Python + OpenCV](#)**

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

<div align="center">
  Made with ❤️ and Python 🐍
</div>
