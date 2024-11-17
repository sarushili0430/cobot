# webot/controllers/my_controller/my_controller.py

import socketio
from controller import Robot, Motor
import logging
import time

# Initialize Logging
logging.basicConfig(level=logging.INFO)

# Initialize Robot
robot = Robot()
timestep = int(robot.getBasicTimeStep())

# Initialize Devices
motor = robot.getDevice('motor_name')  # Replace 'motor_name' with your actual motor name
motor.setPosition(float('inf'))  # Enable velocity control
motor.setVelocity(0.0)

# Initialize SocketIO Client
sio = socketio.Client()

@sio.event
def connect():
    logging.info("Connected to backend server.")

@sio.event
def connect_error(data):
    logging.error("Connection to backend server failed.")

@sio.event
def disconnect():
    logging.info("Disconnected from backend server.")

@sio.on('execute_action')
def handle_execute_action(data):
    action = data.get('action', '').upper()
    logging.info(f"Received action: {action}")
    execute_action(action)

def execute_action(action):
    if action == "GRASP":
        motor.setVelocity(1.0)  # Example action
    elif action == "RELEASE":
        motor.setVelocity(-1.0)
    elif action == "STOP":
        motor.setVelocity(0.0)
    elif action == "WAIT":
        motor.setVelocity(0.0)
    elif action == "ROTATE":
        # Implement rotation logic
        motor.setVelocity(0.5)
    elif action == "ROTATE_BACK":
        # Implement rotate back logic
        motor.setVelocity(-0.5)
    else:
        logging.warning(f"Unknown action: {action}")
        motor.setVelocity(0.0)

def main():
    # Connect to the backend server
    try:
        sio.connect('http://localhost:5000')
    except Exception as e:
        logging.error(f"Failed to connect to backend server: {e}")
        return

    # Main simulation loop
    while robot.step(timestep) != -1:
        # Controller logic can be added here
        # For example, read sensors, send status updates, etc.
        pass

    # Disconnect when simulation ends
    sio.disconnect()

if __name__ == "__main__":
    main()
