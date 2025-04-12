import cv2
import mediapipe as mp
import random
from flask import Flask, render_template, Response, jsonify
import os

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

# Ensure that fruit images are loaded properly
def load_fruit_image(image_path):
    if os.path.exists(image_path):
        return cv2.imread(image_path)
    else:
        print(f"Warning: {image_path} not found!")
        return None

# Fruits and their properties (use larger fruit images for realism)
fruits = [
    {"name": "apple", "image": load_fruit_image('apple.png'), "position": [random.randint(0, 500), -50]},  # Add a realistic apple image
    {"name": "banana", "image": load_fruit_image('banana.png'), "position": [random.randint(0, 500), -50]},  # Add a realistic banana image
    {"name": "watermelon", "image": load_fruit_image('watermelon.png'), "position": [random.randint(0, 500), -50]},  # Add a realistic watermelon image
]

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
            frame = cv2.putText(frame, "GAME OVER! Press SPACE to Restart", (100, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            continue
        
        if game_started:
            # Move fruits down the screen
            for fruit in fruits:
                fruit['position'][1] += 5  # Move the fruit downwards
                
                # Debug: Print fruit position
                print(f"Fruit {fruit['name']} position: {fruit['position']}")
                
                # Check if fruit is within hand's cutting range (index finger tip)
                if results_hand.multi_hand_landmarks:
                    for hand_landmarks in results_hand.multi_hand_landmarks:
                        finger_tip = hand_landmarks.landmark[8]
                        # Check if the finger is near the fruit
                        if (finger_tip.x * frame.shape[1] > fruit['position'][0] - 50 and
                            finger_tip.x * frame.shape[1] < fruit['position'][0] + 50 and
                            finger_tip.y * frame.shape[0] > fruit['position'][1] - 50 and
                            finger_tip.y * frame.shape[0] < fruit['position'][1] + 50):
                            # Debug: Log the cut fruit
                            print(f"Cut fruit: {fruit['name']} at position {fruit['position']}")
                            # Simulate fruit cut by removing it
                            fruit['position'] = [-50, -50]  # Move the fruit off-screen
                            score += 1  # Increase score when a fruit is cut

                # Draw the fruit (image representation)
                if fruit['position'][1] < frame.shape[0]:
                    fruit_img = fruit['image']
                    if fruit_img is not None:  # Check if the image is loaded correctly
                        fruit_resized = cv2.resize(fruit_img, (50, 50))  # Resize the fruit image to fit on screen
                        frame[fruit['position'][1]:fruit['position'][1] + fruit_resized.shape[0], 
                              fruit['position'][0]:fruit['position'][0] + fruit_resized.shape[1]] = fruit_resized
                
                # If fruit falls off screen, game over
                if fruit['position'][1] > frame.shape[0]:
                    game_over = True

            # Display the current score on the frame
            frame = cv2.putText(frame, f"Score: {score}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

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
    global game_started, score
    game_started = True  # Start the game when this route is triggered
    score = 0  # Reset the score
    return jsonify(message="Game Started!")  # Respond with a message to confirm the game started

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)