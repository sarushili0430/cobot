import time
import openai
from controller import Supervisor
from typing import Dict, Optional, Tuple, Any

# API Key
openai.api_key = "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"

# Adjusted timing constants
TIME_STEP = 32
GRASP_POSITION = 0.85
ROTATION_TIME = 64  
GRASP_TIME = 32    
RELEASE_TIME = 32  
DISTANCE_THRESHOLD = 500
DEFAULT_SPEED = 0.8  
CACHE_EXPIRY_TIME = 300

# Robot Positions
INITIAL_POSITIONS = {
    "shoulder_lift_joint": 0.0,
    "elbow_joint": 0.0,
    "wrist_1_joint": 0.0,
    "wrist_2_joint": 0.0
}

TARGET_POSITIONS = {
    "shoulder_lift_joint": -1.88,
    "elbow_joint": -2.14,
    "wrist_1_joint": -2.38,
    "wrist_2_joint": -1.51
}

class RobotState:
    WAITING = "WAITING"
    GRASPING = "GRASPING"
    ROTATING = "ROTATING"
    RELEASING = "RELEASING"
    ROTATING_BACK = "ROTATING_BACK"

class CacheEntry:
    def __init__(self, value: str):
        self.value = value
        self.timestamp = time.time()

    def is_expired(self) -> bool:
        return (time.time() - self.timestamp) > CACHE_EXPIRY_TIME

class UR5eControllerAgent:
    def __init__(self):
        self.robot = Supervisor()
        self._initialize_motors()
        self._initialize_sensors()
        self.state = RobotState.WAITING
        self.counter = 0
        self.decision_cache: Dict[Tuple, CacheEntry] = {}

    def _initialize_motors(self) -> None:
        """Initialize and configure all robot motors."""
        self.hand_motors = {
            name: self.robot.getDevice(name) for name in [
                "finger_1_joint_1",
                "finger_2_joint_1",
                "finger_middle_joint_1"
            ]
        }

        self.ur_motors = {
            name: self.robot.getDevice(name) 
            for name in INITIAL_POSITIONS.keys()
        }

        # Set motor velocities
        for motor in self.ur_motors.values():
            if motor:
                motor.setVelocity(DEFAULT_SPEED)

    def _initialize_sensors(self) -> None:
        """Initialize and enable robot sensors."""
        self.sensors = {
            "distance": self.robot.getDevice("distance sensor"),
            "position": self.robot.getDevice("wrist_1_joint_sensor")
        }

        for sensor in self.sensors.values():
            if sensor:
                sensor.enable(TIME_STEP)

    def grasp(self) -> None:
        """Execute grasp action."""
        for motor in self.hand_motors.values():
            if motor:
                motor.setPosition(GRASP_POSITION)
        self.counter = GRASP_TIME  # Give the action some time to complete

    def release(self) -> None:
        """Execute release action."""
        for motor in self.hand_motors.values():
            if motor:
                motor.setPosition(motor.getMinPosition())
        self.counter = RELEASE_TIME  # Give the action some time to complete

    def move_to_positions(self, positions: Dict[str, float]) -> None:
        """Move robot joints to specified positions."""
        for name, position in positions.items():
            if motor := self.ur_motors.get(name):
                motor.setPosition(position)
        self.counter = ROTATION_TIME  # Give the movement some time to complete

    def get_next_action(self, state: str, sensor_values: Dict[str, Optional[float]]) -> str:
        """Determine next action using GPT-3.5-turbo with caching."""
        cache_key = (
            state,
            round(sensor_values["distance"], 2) if sensor_values["distance"] else None,
            round(sensor_values["position"], 2) if sensor_values["position"] else None
        )

        if cache_key in self.decision_cache:
            entry = self.decision_cache[cache_key]
            if not entry.is_expired():
                return entry.value

        prompt = (
            f"Robot state: '{state}'. "
            f"Sensor values: {sensor_values}. "
            f"Next action? Options: WAIT, GRASP, ROTATE, RELEASE, ROTATE_BACK."
        )

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a robot control system. Wait for actions to complete before proceeding. Respond with exactly one word from the available options."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=45,
                temperature=0.1,
                presence_penalty=0,
                frequency_penalty=0
            )
            action = response['choices'][0]['message']['content'].strip()
            self.decision_cache[cache_key] = CacheEntry(action)
            return action
        except Exception as e:
            print(f"Error in GPT API call: {e}")
            return "WAIT"

    def _handle_state_transition(self, sensor_values: Dict[str, Optional[float]]) -> None:
        """Handle robot state transitions with completion checks."""
        # Only proceed if the current action is complete
        if self.counter > 0:
            return

        # Quick local decision for obvious cases
        if (
            self.state == RobotState.WAITING and 
            sensor_values["distance"] is not None and 
            sensor_values["distance"] < DISTANCE_THRESHOLD
        ):
            self.state = RobotState.GRASPING
            self.grasp()
            return

        # Get next action from GPT
        action = self.get_next_action(self.state, sensor_values)

        # State machine transitions
        state_actions = {
            "GRASP": (RobotState.GRASPING, self.grasp),
            "ROTATE": (RobotState.ROTATING, lambda: self.move_to_positions(TARGET_POSITIONS)),
            "RELEASE": (RobotState.RELEASING, self.release),
            "ROTATE_BACK": (RobotState.ROTATING_BACK, lambda: self.move_to_positions(INITIAL_POSITIONS)),
            "WAIT": (RobotState.WAITING, lambda: None)
        }

        if action in state_actions:
            self.state, action_func = state_actions[action]
            action_func()

    def _get_sensor_values(self) -> Dict[str, Optional[float]]:
        """Retrieve sensor values."""
        return {
            "distance": self.sensors["distance"].getValue() if self.sensors["distance"] else None,
            "position": self.sensors["position"].getValue() if self.sensors["position"] else None
        }

    def run(self) -> None:
        """Main robot control loop with improved timing."""
        try:
            while self.robot.step(TIME_STEP) != -1:
                if self.counter <= 0:
                    sensor_values = self._get_sensor_values()
                    self._handle_state_transition(sensor_values)
                self.counter = max(0, self.counter - 1)
        except KeyboardInterrupt:
            print("\nGracefully shutting down robot controller...")
        except Exception as e:
            print(f"Error in main control loop: {e}")
        finally:
            self.release()
            self.move_to_positions(INITIAL_POSITIONS)

if __name__ == "__main__":
    try:
        controller = UR5eController()
        controller.run()
    except Exception as e:
        print(f"Failed to initialize controller: {e}")
        sys.exit(1)
