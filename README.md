# ● Fruit Samurai  
### A Body Tracking Game for Injury Recovery  
Harnessing Computer Vision for Fun, Interactive Rehabilitation  

---

## Overview  
**Fruit Samurai** is a computer vision-powered web game designed to support **motor skill rehabilitation** and **interactive physical therapy** through playful engagement. Built using Python, MediaPipe, OpenCV, and Flask, the game leverages **real-time hand and face tracking** to allow players to slice virtual fruit using only their gestures—no controllers required.

Originally developed as an innovative blend of **rehab tech and gamification**, this application offers an immersive experience where patients recovering from upper-limb injuries can **exercise mobility** in a motivating, safe, and trackable way.

---

## Example Gameplay

Below is a snapshot of *Fruit Samurai* in action, showcasing real-time body tracking and the interactive slicing mechanic using hand gestures. The user’s fingertip is tracked to slice falling watermelons, simulating intuitive movement that supports rehabilitation exercises.

![Gameplay Example](https://github.com/sorinnicumarian/body_tracking_game/blob/main/Game%20Screenshot.png)

This image highlights the simple interface, real-time webcam feed, and the overlayed virtual fruit. The game is designed for accessibility and low hardware requirements, making it suitable for at-home recovery and experimentation with computer vision.

## Features  

- **AI-Powered Body Tracking** using MediaPipe  
- **Virtual Watermelon Slicing** controlled by hand gestures  
- **Face Mask Overlay** with facial landmark detection  
- **Real-Time Feedback** and dynamic scoring  
- **Rehabilitation-Friendly Loop** with soft reset and restart mechanics  
- **Lightweight Local Deployment** – works offline with a webcam

---

## Use Cases  

- **Rehabilitation Centers** – Arm and shoulder therapy post-surgery  
- **Gamified Physical Therapy** – For kids and adults alike  
- **Research and Prototyping** – Human-computer interaction studies  
- **At-Home Recovery** – Engaging alternative to static rehab exercises

---

## Installation

### Prerequisites  
- macOS with Homebrew installed  
- Python 3.10  
- A functional webcam  

### Setup Instructions

```bash
# 1. Install Python 3.10
brew install python@3.10

# 2. Create and activate a virtual environment
python3.10 -m venv body_tracking_env_2
source body_tracking_env_2/bin/activate

# 3. Upgrade pip
pip install --upgrade pip

# 4. Install project dependencies
pip install -r requirements.txt
```

### Run the App

```bash
python main.py
```

Then open your browser and navigate to `http://127.0.0.1:5000` to start playing.

---

## Assets Folder  
Place your `sword.png`, `mask.png`, and `watermelon.png` inside the `assets/` directory. Make sure the images have **alpha channels (PNG with transparency)** for proper blending.

---

## Requirements

```text
opencv-python
flask
mediapipe
numpy
```

*(All dependencies are listed in `requirements.txt`)*

---

## Acknowledgments  
This project draws inspiration from **Fruit Ninja**, **physical therapy games**, and **gesture-controlled interfaces**. It combines **entertainment** with **practical recovery mechanics**, aiming to support patients and clinicians alike.

---

## License  
MIT License. Use freely with attribution.
