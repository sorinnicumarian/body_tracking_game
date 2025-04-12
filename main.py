import cv2
import random
import numpy as np
from flask import Flask, render_template, Response, jsonify
import mediapipe as mp

# Initialize Flask app
app = Flask(__name__)

# Initialize MediaPipe Hand model
mp_hand = mp.solutions.hands
hands = mp_hand.Hands()

# Global game state
games_played = 0  # Track the number of games played
game_over = False
score = 0
current_fruit = None

# GameState management
class GameState:
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    GAME_OVER = "game_over"

    def __init__(self):
        self.state = GameState.NOT_STARTED
        self.score = 0

    def start_game(self):
        self.state = GameState.IN_PROGRESS
        self.score = 0

    def end_game(self):
        self.state = GameState.GAME_OVER

    def reset_game(self):
        self.start_game()

# Fruit Class for creating watermelon
class Fruit:
    def __init__(self, name, image, position):
        self.name = name
        self.image = image
        self.position = position
        self.cut = False

    def update_position(self, y_change):
        self.position[1] += y_change

    def is_cut(self):
        return self.cut

    def cut_fruit(self):
        self.cut = True
        self.position = [-50, -50]  # Move off-screen after cut

class Watermelon(Fruit):
    def __init__(self):
        image = self.create_watermelon_image()
        super().__init__("watermelon", image, [random.randint(0, 500), -50])

    def create_watermelon_image(self):
        # Create a simple watermelon with green skin and red flesh
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.circle(image, (50, 50), 45, (0, 255, 0), -1)  # Green outer skin
        cv2.circle(image, (50, 50), 35, (0, 0, 255), -1)  # Red inner flesh
        return image

# Game class to manage the state and update
class Game:
    def __init__(self):
        self.state = GameState()
        self.fruits = []
        self.current_fruit = None

    def start(self):
        global games_played
        games_played += 1  # Increment game counter
        self.state.start_game()
        self.create_new_fruit()

    def end(self):
        self.state.end_game()

    def reset(self):
        self.state.reset_game()
        self.create_new_fruit()

    def create_new_fruit(self):
        self.current_fruit = Watermelon()
        self.fruits.append(self.current_fruit)

    def update(self):
        if self.state.state == GameState.IN_PROGRESS:
            self.current_fruit.update_position(5)

            if self.current_fruit.position[1] > 480:  # Fruit has fallen off screen
                self.end()

            if self.current_fruit.is_cut():
                self.create_new_fruit()
                self.state.score += 1

    def get_state(self):
        return self.state.state

    def get_score(self):
        return self.state.score

    def get_fruit(self):
        return self.current_fruit

# Initialize the game
game = Game()

# Frame generator for streaming video to the frontend
def gen_frames():
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Resize the frame to reduce size for streaming
        frame = cv2.resize(frame, (640, 480))  # Adjust this as needed for performance
        frame = cv2.flip(frame, 1)  # Flip the frame to correct the mirrored image

        # Game logic update
        game.update()

        # Convert the frame to RGB for MediaPipe
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Get hand landmarks
        results_hand = hands.process(image_rgb)

        # Draw the watermelon on the frame
        if game.get_state() == GameState.IN_PROGRESS:
            watermelon = game.get_fruit()
            if not watermelon.is_cut():
                fruit_img = watermelon.image
                if fruit_img is not None:
                    fruit_resized = cv2.resize(fruit_img, (50, 50))

                    # Prevent watermelon from going out of frame
                    if watermelon.position[1] + fruit_resized.shape[0] <= frame.shape[0]:
                        y_start = max(0, watermelon.position[1])
                        y_end = min(frame.shape[0], watermelon.position[1] + fruit_resized.shape[0])
                        x_start = max(0, watermelon.position[0])
                        x_end = min(frame.shape[1], watermelon.position[0] + fruit_resized.shape[1])

                        frame[y_start:y_end, x_start:x_end] = fruit_resized[:y_end - y_start, :x_end - x_start]

                # Hand detection and cutting logic
                if results_hand.multi_hand_landmarks:
                    for hand_landmarks in results_hand.multi_hand_landmarks:
                        finger_tip = hand_landmarks.landmark[8]
                        # Check if the finger is near the watermelon
                        if (finger_tip.x * frame.shape[1] > watermelon.position[0] - 50 and
                            finger_tip.x * frame.shape[1] < watermelon.position[0] + 50 and
                            finger_tip.y * frame.shape[0] > watermelon.position[1] - 50 and
                            finger_tip.y * frame.shape[0] < watermelon.position[1] + 50):
                            # Simulate fruit cut by setting 'cut' flag
                            watermelon.cut_fruit()

        # Game Over text and frame manipulation
        if game.get_state() == GameState.GAME_OVER:
            frame = cv2.putText(frame, f"GAME OVER! Final Score: {game.get_score()}", (100, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Encode image as jpeg for Flask to send to the frontend
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/start_game', methods=['POST'])
def start_game():
    game.start()  # Start or reset the game
    return jsonify(message="Game Started!")

@app.route('/game_over', methods=['GET'])
def game_over_route():
    return jsonify({
        "game_over": True,
        "final_score": game.get_score()
    })

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)