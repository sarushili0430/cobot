from controller import Robot, Motor, DistanceSensor, PositionSensor
from dotenv import load_dotenv
import openai
import json
import os


class AIAgent:
    def __init__(self):
        self.controller = RobotController()

    def decide_and_act(self, perception):
        # Create a prompt for GPT-4
        prompt = self.create_prompt(perception)

        # Get action plan from GPT-4
        action_plan = self.get_action_plan(prompt)

        # Execute the action plan
        if action_plan:
            self.execute_action_plan(action_plan)

    def create_prompt(self, perception):
        prompt = f"""
You are an AI agent controlling a UR robot in a factory simulation. Based on the current perception data and state, decide the next actions to perform. Provide the action plan in JSON format.

Perception data:
- Distance sensor value: {perception['distance']}
- Wrist position sensor value: {perception['wrist_position']}
- Current state: {perception['state']}

Constraints:
- Only use actions: 'GRASP', 'ROTATE', 'RELEASE', 'ROTATE_BACK', 'WAIT'.
- Ensure the action plan is appropriate based on the perception data.

Output format:
{{
  "action": "ACTION_NAME",
  "parameters": {{
    // Any parameters needed for the action
  }}
}}

Provide only the JSON output.
"""
        return prompt

    def get_action_plan(self, prompt):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0,
            )
            content = response["choices"][0]["message"]["content"]
            action_plan = json.loads(content)
            return action_plan
        except Exception as e:
            print(f"Error obtaining action plan: {e}")
            return None


class RobotController:
    def __init__(self, agent: AIAgent):
        # Initialize the robot
        self.robot = Robot()
        self.agent = agent
        self.time_step = int(self.robot.getBasicTimeStep())

        # Initialize devices
        self.initialize_devices()

        # Initialize OpenAI API
        openai.api_key = os.getenv("OPENAI_API_KEY")

        # Agent state
        self.state = "WAITING"

    def initialize_devices(self):
        # Initialize hand motors
        self.hand_motors = [
            self.robot.getDevice("finger_1_joint_1"),
            self.robot.getDevice("finger_2_joint_1"),
            self.robot.getDevice("finger_middle_joint_1"),
        ]
        for motor in self.hand_motors:
            motor.setPosition(float("inf"))  # Enable velocity control
            motor.setVelocity(0.0)

        # Initialize UR motors
        self.ur_motors = [
            self.robot.getDevice("shoulder_lift_joint"),
            self.robot.getDevice("elbow_joint"),
            self.robot.getDevice("wrist_1_joint"),
            self.robot.getDevice("wrist_2_joint"),
        ]
        for motor in self.ur_motors:
            motor.setPosition(float("inf"))  # Enable velocity control
            motor.setVelocity(0.0)

        # Initialize sensors
        self.distance_sensor = self.robot.getDevice("distance sensor")
        self.distance_sensor.enable(self.time_step)

        self.position_sensor = self.robot.getDevice("wrist_1_joint_sensor")
        self.position_sensor.enable(self.time_step)

    def run(self):
        while self.robot.step(self.time_step) != -1:
            # Perceive environment
            perception = self.perceive()

            # Decide and act
            self.decide_and_act(perception)

    def perceive(self):
        perception = {
            "distance": self.distance_sensor.getValue(),
            "wrist_position": self.position_sensor.getValue(),
            "state": self.state,
        }
        return perception

    def execute_action_plan(self, action_plan):
        action = action_plan.get("action")
        parameters = action_plan.get("parameters", {})

        if action == "GRASP":
            self.grasp()
        elif action == "ROTATE":
            self.rotate()
        elif action == "RELEASE":
            self.release()
        elif action == "ROTATE_BACK":
            self.rotate_back()
        elif action == "WAIT":
            self.wait()
        else:
            print(f"Unknown action: {action}")

    def grasp(self):
        print("Grasping object...")
        for motor in self.hand_motors:
            motor.setPosition(0.85)  # Close gripper
        self.state = "GRASPING"

    def rotate(self):
        print("Rotating arm...")
        target_positions = [-1.88, -2.14, -2.38, -1.51]
        for motor, position in zip(self.ur_motors, target_positions):
            motor.setPosition(position)
        self.state = "ROTATING"

    def release(self):
        print("Releasing object...")
        for motor in self.hand_motors:
            motor.setPosition(motor.getMinPosition())  # Open gripper
        self.state = "RELEASING"

    def rotate_back(self):
        print("Rotating arm back...")
        for motor in self.ur_motors:
            motor.setPosition(0.0)
        self.state = "ROTATING_BACK"

    def wait(self):
        print("Waiting...")
        self.state = "WAITING"


if __name__ == "__main__":
    load_dotenv()
    agent = AIAgent()
    controller = RobotController(AIAgent)
    controller.run()
