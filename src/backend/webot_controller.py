# backend/webot_controller.py

from controller import Supervisor
import threading

class WebotController:
    def __init__(self):
        self.robot = Supervisor()
        self.time_step = 32
        self.state = "WAITING"
        self.counter = 0
        self.target_positions = [-1.88, -2.14, -2.38, -1.51]
        self.valid_actions = ["WAIT", "GRASP", "ROTATE", "RELEASE", "ROTATE_BACK"]
        self.lock = threading.Lock()

        # Initialize Motors and Sensors
        self.hand_motors = [
            self.robot.getDevice("finger_1_joint_1"),
            self.robot.getDevice("finger_2_joint_1"),
            self.robot.getDevice("finger_middle_joint_1")
        ]
        self.ur_motors = [
            self.robot.getDevice("shoulder_lift_joint"),
            self.robot.getDevice("elbow_joint"),
            self.robot.getDevice("wrist_1_joint"),
            self.robot.getDevice("wrist_2_joint")
        ]

        # Set motor velocities
        speed = 1.0
        for motor in self.ur_motors:
            if motor:
                motor.setVelocity(speed)
            else:
                print("Error: One or more UR motor devices not found.")

        # Enable Sensors
        self.distance_sensor = self.robot.getDevice("distance sensor")
        if self.distance_sensor:
            self.distance_sensor.enable(self.time_step)
        else:
            print("Error: Distance sensor not found.")

        self.position_sensor = self.robot.getDevice("wrist_1_joint_sensor")
        if self.position_sensor:
            self.position_sensor.enable(self.time_step)
        else:
            print("Error: Position sensor not found.")

    def grasp(self):
        for motor in self.hand_motors:
            if motor:
                motor.setPosition(0.85)
            else:
                print("Error: One or more hand motor devices not found.")

    def release(self):
        for motor in self.hand_motors:
            if motor:
                motor.setPosition(motor.getMinPosition())
            else:
                print("Error: One or more hand motor devices not found.")

    def rotate(self, target_positions):
        for i, motor in enumerate(self.ur_motors):
            if motor:
                motor.setPosition(target_positions[i])
            else:
                print(f"Error: UR motor {i} not found.")

    def rotate_back(self):
        for motor in self.ur_motors:
            if motor:
                motor.setPosition(0.0)
            else:
                print("Error: One or more UR motor devices not found.")

    def execute_action(self, action):
        with self.lock:
            if action not in self.valid_actions:
                print(f"Invalid action received: {action}. Defaulting to WAIT.")
                action = "WAIT"

            if action == "GRASP":
                self.state = "GRASPING"
                self.counter = 8
                print("Executing Action: GRASP")
                self.grasp()

            elif action == "ROTATE":
                self.rotate(self.target_positions)
                self.state = "ROTATING"
                print("Executing Action: ROTATE")

            elif action == "RELEASE":
                self.state = "RELEASING"
                self.counter = 8
                print("Executing Action: RELEASE")
                self.release()

            elif action == "ROTATE_BACK":
                self.rotate_back()
                self.state = "ROTATING_BACK"
                print("Executing Action: ROTATE_BACK")

            elif action == "WAIT":
                self.state = "WAITING"
                print("Executing Action: WAIT")

    def get_sensor_values(self):
        with self.lock:
            return {
                "distance_sensor": self.distance_sensor.getValue() if self.distance_sensor else None,
                "position_sensor": self.position_sensor.getValue() if self.position_sensor else None
            }

    def run(self):
        while self.robot.step(self.time_step) != -1:
            if self.counter > 0:
                self.counter -= 1
            # Additional simulation logic can be added here if needed
