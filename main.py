import cv2
import mediapipe as mp
import random
import cairosvg
import numpy as np
from flask import Flask, render_template, Response, jsonify
import os
import urllib.request

# Initialize MediaPipe Pose model
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_hand = mp.solutions.hands
hands = mp_hand.Hands()
mp_drawing = mp.solutions.drawing_utils

# Initialize Flask app
app = Flask(__name__)

# Game state flags
game_over = False
game_started = False
score = 0  # Initialize the score

# Function to convert SVG to PNG and return as a NumPy array (ensure transparency)
def svg_to_png(image_url):
    image_path = '/tmp/fruit_image.png'
    urllib.request.urlretrieve(image_url, image_path)  # Download the image to local path
    cairosvg.svg2png(url=image_path, write_to=image_path)  # Convert SVG to PNG
    fruit_image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)  # Read with alpha channel (transparency)

    # Convert RGBA to RGB by discarding the alpha channel
    if fruit_image.shape[2] == 4:  # If the image has 4 channels (RGBA)
        fruit_image = cv2.cvtColor(fruit_image, cv2.COLOR_BGRA2BGR)  # Convert to BGR (3 channels)

    return fruit_image  # Return the image with transparency removed

# Fruits and their properties (only 1 watermelon for now)
fruits = [
    {"name": "watermelon", "image": svg_to_png('https://static.wikia.nocookie.net/fruitninja/images/d/d6/Watermelon.svg/revision/latest?cb=20170717192054'), "position": [random.randint(0, 500), -50], "cut": False},
]

# Function to create juice splash effect (simple circle animation)
def create_juice_splash(position):
    splash = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.circle(splash, (position[0], position[1]), 20, (0, 255, 0), -1)  # Green splash
    return splash

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
        
        # Get pose and hand landmarks
        results_pose = pose.process(image_rgb)
        results_hand = hands.process(image_rgb)

        # Draw pose landmarks (if any)
        if results_pose.pose_landmarks:
            mp_drawing.draw_landmarks(frame, results_pose.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        # Draw hand landmarks (if any)
        if results_hand.multi_hand_landmarks:
            for hand_landmarks in results_hand.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hand.HAND_CONNECTIONS)

        # Check if game is over and handle restart
        if game_over:
            frame = cv2.putText(frame, "GAME OVER! Press START to Restart", (100, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            continue
        
        if game_started:
            # Move the single watermelon down the screen
            watermelon = fruits[0]  # Only one fruit for now (watermelon)
            if watermelon['cut']:
                # Simulate fruit moving to the side after being cut
                watermelon['position'][0] += random.randint(-50, 50)  # Move it to a side
                watermelon['position'][1] += random.randint(-20, -50)  # Make it fall faster
                frame = cv2.add(frame, create_juice_splash(watermelon['position']))  # Add juice splash
                continue  # Skip to next fruit as this one is already cut

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
                        score += 1  # Increase score when the fruit is cut

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
        {"name": "watermelon", "image": svg_to_png('https://static.wikia.nocookie.net/fruitninja/images/d/d6/Watermelon.svg/revision/latest?cb=20170717192054'), "position": [random.randint(0, 500), -50], "cut": False},
    ]
    return jsonify(message="Game Started!")  # Respond with a message to confirm the game started

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)