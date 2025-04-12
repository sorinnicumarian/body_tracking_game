import cv2
import mediapipe as mp
import random
import numpy as np
from flask import Flask, render_template, Response, jsonify

# Initialize MediaPipe Hand model
mp_hand = mp.solutions.hands
hands = mp_hand.Hands()

# Initialize Flask app
app = Flask(__name__)

# Game state flags
game_over = False
game_started = False
score = 0  # Initialize the score

# Function to draw a simple watermelon (green outer layer, red inner layer)
def draw_watermelon():
    # Create a blank image with a black background
    image = np.zeros((100, 100, 3), dtype=np.uint8)

    # Draw the green outer skin (circle)
    cv2.circle(image, (50, 50), 45, (0, 255, 0), -1)  # Green circle for outer skin

    # Draw the red inner flesh (circle)
    cv2.circle(image, (50, 50), 35, (0, 0, 255), -1)  # Red circle for flesh

    return image

# Function to create a new watermelon with random position
def create_new_watermelon():
    return {
        "name": "watermelon",
        "image": draw_watermelon(),
        "position": [random.randint(0, 500), -50],  # Random horizontal position and start from above
        "cut": False
    }

# Fruits and their properties (start with 1 watermelon)
fruits = [create_new_watermelon()]

# Frame generator to send video frames to the web page
def gen_frames():
    global fruits, game_over, game_started, score
    
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Resize the frame to reduce size for streaming
        frame = cv2.resize(frame, (640, 480))  # Adjust this as needed for performance
        
        # Flip the frame to correct the mirrored image
        frame = cv2.flip(frame, 1)

        # Convert the frame to RGB for MediaPipe
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Get hand landmarks
        results_hand = hands.process(image_rgb)

        # Check if game is over and handle restart
        if game_over:
            frame = cv2.putText(frame, "GAME OVER! Press START to Restart", (100, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            continue
        
        if game_started:
            if fruits:  # Ensure there's a watermelon to process
                watermelon = fruits[0]  # Only one fruit for now (watermelon)
                
                if watermelon['cut']:
                    # Make the watermelon disappear from the screen
                    watermelon['position'] = [-50, -50]  # Move it off-screen
                    score += 1  # Increase score when the fruit is cut

                    # After cutting, create a new watermelon
                    fruits[0] = create_new_watermelon()

                    continue  # Skip the rest of the code for the watermelon

                watermelon['position'][1] += 5  # Move the fruit downwards
                
                # Check if fruit is within hand's cutting range (index finger tip)
                if results_hand.multi_hand_landmarks:
                    for hand_landmarks in results_hand.multi_hand_landmarks:
                        finger_tip = hand_landmarks.landmark[8]
                        # Check if the finger is near the fruit
                        if (finger_tip.x * frame.shape[1] > watermelon['position'][0] - 50 and
                            finger_tip.x * frame.shape[1] < watermelon['position'][0] + 50 and
                            finger_tip.y * frame.shape[0] > watermelon['position'][1] - 50 and
                            finger_tip.y * frame.shape[0] < watermelon['position'][1] + 50):
                            # Simulate fruit cut by setting 'cut' flag
                            watermelon['cut'] = True

                # Ensure the fruit's position is within frame boundaries
                if watermelon['position'][0] >= 0 and watermelon['position'][0] + 50 <= frame.shape[1] and watermelon['position'][1] >= 0:
                    # Draw the fruit (image representation)
                    fruit_img = watermelon['image']
                    if fruit_img is not None:  # Check if the image is loaded correctly
                        fruit_resized = cv2.resize(fruit_img, (50, 50))  # Resize the fruit image to fit on screen
                        # Make sure the fruit is within the frame before placing
                        if watermelon['position'][1] + fruit_resized.shape[0] <= frame.shape[0]:
                            frame[watermelon['position'][1]:watermelon['position'][1] + fruit_resized.shape[0], 
                                  watermelon['position'][0]:watermelon['position'][0] + fruit_resized.shape[1]] = fruit_resized

                # If fruit falls off screen, game over
                if watermelon['position'][1] > frame.shape[0]:
                    game_over = True

                # Display the current score on the top of the frame
                frame = cv2.putText(frame, f"Score: {score}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # Start game prompt when the game is not started
        if not game_started:
            frame = cv2.putText(frame, "Press Start to Begin", (100, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # Encode image as jpeg for Flask
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
    global game_started, score, fruits, game_over
    game_started = True  # Start the game when this route is triggered
    score = 0  # Reset the score
    game_over = False  # Reset the game over state
    fruits = [
        create_new_watermelon(),
    ]
    return jsonify(message="Game Started!")  # Respond with a message to confirm the game started

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)  # Disable reloader to avoid SystemExit