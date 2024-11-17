import openai
import sys
import asyncio
from controller import Supervisor

# Define the API key directly in the script
openai.api_key = ""

time_step = 16  # Reduced time step for more frequent updates

class UR5eController:
    def __init__(self):
        self.robot = Supervisor()
        self.time_step = time_step

        # Initialize Motors
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
        # Close the gripper
        for motor in self.hand_motors:
            if motor:
                motor.setPosition(0.85)
            else:
                print("Error: One or more hand motor devices not found.")

    def release(self):
        # Open the gripper
        for motor in self.hand_motors:
            if motor:
                motor.setPosition(motor.getMinPosition())
            else:
                print("Error: One or more hand motor devices not found.")

    async def ask_gpt4(self, state, sensor_values):
        prompt = f"The robot is currently in state: '{state}'. The sensor values are: {sensor_values}. What should the next action be? Options: WAIT, GRASP, ROTATE, RELEASE, ROTATE_BACK."

        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4-0613",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.7
            )
            return response['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"Error querying OpenAI API: {e}")
            return "WAIT"

    def run(self):
        state = "WAITING"
        counter = 0
        target_positions = [-1.88, -2.14, -2.38, -1.51]

        async def decision_loop():
            while True:
                if self.robot.step(self.time_step) == -1:
                    break

                sensor_values = {
                    "distance_sensor": self.distance_sensor.getValue() if self.distance_sensor else None,
                    "position_sensor": self.position_sensor.getValue() if self.position_sensor else None
                }

                if state == "WAITING" and self.distance_sensor.getValue() < 500:
                    # Simple local decision to grasp if close enough
                    state = "GRASPING"
                    counter = 8
                    print("Grasping object")
                    self.grasp()
                else:
                    # Query GPT-4 for the next action
                    action = await self.ask_gpt4(state, sensor_values)

                    if counter <= 0:
                        if action == "GRASP":
                            state = "GRASPING"
                            counter = 8
                            print("Grasping object")
                            self.grasp()

                        elif action == "ROTATE":
                            for i in range(4):
                                if self.ur_motors[i]:
                                    self.ur_motors[i].setPosition(target_positions[i])
                                else:
                                    print(f"Error: UR motor {i} not found.")
                            print("Rotating arm")
                            state = "ROTATING"

                        elif action == "RELEASE":
                            counter = 8
                            print("Releasing object")
                            state = "RELEASING"
                            self.release()

                        elif action == "ROTATE_BACK":
                            for motor in self.ur_motors:
                                if motor:
                                    motor.setPosition(0.0)
                            print("Rotating arm back")
                            state = "ROTATING_BACK"

                        elif action == "WAIT":
                            print("Waiting for next object")
                            state = "WAITING"

                counter -= 1

        # Run the decision loop asynchronously
        asyncio.run(decision_loop())

if __name__ == "__main__":
    controller = UR5eController()
    controller.run()
