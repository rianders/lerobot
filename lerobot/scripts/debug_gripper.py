#!/usr/bin/env python3
"""
Simplified debug script for the Feetech gripper calibration issue.
This script isolates the gripper testing process to diagnose calibration errors.
"""

import os
import time
import sys
from pathlib import Path

# Try the direct imports from the project structure
from lerobot.common.robot_devices.robots.manipulator import ManipulatorRobot
from lerobot.common.robot_devices.robots.utils import make_robot_from_config
from lerobot.configs import parser
from lerobot.common.robot_devices.control_configs import ControlPipelineConfig
from lerobot.common.robot_devices.motors.feetech import FeetechArmController

def debug_gripper():
    """Test the gripper servo to diagnose calibration issues."""
    print("Starting Feetech gripper debugging test...")
    
    # Create robot from config (leader arm mocked, follower active)
    args = ["--robot.type=so100", 
            "--robot.follower_arms.main.mock=False",
            "--robot.leader_arms.main.mock=True"]
    
    cfg = parser.parse_args(args, data_class=ControlPipelineConfig)
    
    # Remove existing calibration file to force recalibration
    calib_dir = Path(".cache/calibration/so100")
    calib_dir.mkdir(parents=True, exist_ok=True)
    
    follower_calib = calib_dir / "main_follower.json"
    if follower_calib.exists():
        print(f"Removing existing calibration file: {follower_calib}")
        follower_calib.unlink()
    
    # Create robot instance
    print("Creating robot instance...")
    robot = make_robot_from_config(cfg.robot)
    
    try:
        # Extract the port directly from configuration
        follower_port = robot.robot_config['follower_arms']['main']['port']
        print(f"Follower arm port: {follower_port}")
        
        # Get motor IDs
        follower_motors = robot.robot_config['follower_arms']['main']['motors']
        print("\nMotor IDs:")
        for motor_name, (motor_id, motor_type) in follower_motors.items():
            print(f"- {motor_name}: ID={motor_id}, Type={motor_type}")
        
        # Direct connection to arm controller for detailed debugging
        print("\nConnecting directly to arm controller...")
        arm_controller = FeetechArmController(
            port=follower_port,
            motors=follower_motors,
            mock=False
        )
        
        # Initialize controller
        print("Initializing controller...")
        arm_controller.connect()
        
        # Test all motors to verify communication
        print("\nReading current positions for all motors:")
        try:
            positions = arm_controller.read("Present_Position")
            for motor_name, position in positions.items():
                print(f"- {motor_name}: {position}")
        except Exception as e:
            print(f"Error reading positions: {e}")
        
        # Focus on the gripper motor
        gripper_id = follower_motors['gripper'][0]
        print(f"\nFocusing on gripper (ID: {gripper_id})...")
        
        # Enable torque
        print("Enabling torque on gripper...")
        try:
            arm_controller.write("Torque_Enable", {"gripper": True})
            print("Torque enabled successfully.")
        except Exception as e:
            print(f"Error enabling torque: {e}")
        
        # Debug calibration process step by step
        print("\n--- CALIBRATION DEBUGGING ---")
        
        # Zero position
        input("\nMove gripper to ZERO position (FULLY CLOSED), then press Enter...")
        try:
            zero_pos = arm_controller.read("Present_Position")["gripper"]
            print(f"Zero position value: {zero_pos}")
        except Exception as e:
            print(f"Error reading zero position: {e}")
            zero_pos = None
            
        # Rotated position
        input("\nMove gripper to ROTATED position (FULLY OPEN), then press Enter...")
        try:
            rotated_pos = arm_controller.read("Present_Position")["gripper"]
            print(f"Rotated position value: {rotated_pos}")
        except Exception as e:
            print(f"Error reading rotated position: {e}")
            rotated_pos = None
        
        # Check the critical difference
        if zero_pos is not None and rotated_pos is not None:
            difference = rotated_pos - zero_pos
            print(f"\nDifference between positions: {difference}")
            
            if difference == 0:
                print("ERROR: Zero difference detected! This will cause division by zero during calibration.")
                print("The gripper position is not changing between calibration steps.")
            elif abs(difference) < 10:
                print(f"WARNING: Very small difference ({difference})! This might cause calibration issues.")
            else:
                print("Difference looks acceptable.")
                
            # Test calibration formula manually
            print("\nTesting calibration formula...")
            if difference != 0:
                # Test with a few positions to check calibration
                for i in range(3):
                    input(f"\nTest {i+1}: Move gripper to a different position, then press Enter...")
                    test_pos = arm_controller.read("Present_Position")["gripper"]
                    print(f"Position value: {test_pos}")
                    
                    # Calculate what the calibrated value would be
                    calib_val = (test_pos - zero_pos) / difference * 100
                    print(f"This would calibrate to approximately: {calib_val:.2f}%")
                    
                    # Check if this value would cause the calibration error
                    if calib_val < -10 or calib_val > 110:
                        print(f"WARNING: This value ({calib_val:.2f}%) is outside the acceptable range [-10, 110]")
                        print("This would trigger the 'Wrong motor position range' error during calibration.")
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        print("\nDisconnecting...")
        try:
            if 'arm_controller' in locals() and hasattr(arm_controller, 'disconnect'):
                arm_controller.disconnect()
        except Exception as e:
            print(f"Error disconnecting arm controller: {e}")

if __name__ == "__main__":
    debug_gripper()
