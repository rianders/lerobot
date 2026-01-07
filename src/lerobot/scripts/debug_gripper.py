#!/usr/bin/env python3
"""
Simplified debug script for the Feetech gripper calibration issue.
This script isolates the gripper testing process to diagnose calibration errors.
"""

import time
from pathlib import Path

from lerobot.motors.feetech import FeetechMotorsBus
from lerobot.robots import make_robot_from_config
from lerobot.robots.so100_follower.config_so100_follower import SO100FollowerConfig

def debug_gripper():
    """Test the gripper servo to diagnose calibration issues."""
    print("Starting Feetech gripper debugging test...")

    # Configure and create SO100 follower robot
    # Update the port to match your device
    config = SO100FollowerConfig(
        port="/dev/tty.usbmodem59700726961",  # Update this to your actual port
        mock=False,
    )

    # Remove existing calibration file to force recalibration
    calib_dir = Path(".cache/calibration/so100_follower")
    calib_dir.mkdir(parents=True, exist_ok=True)

    follower_calib = calib_dir / "calibration.json"
    if follower_calib.exists():
        print(f"Removing existing calibration file: {follower_calib}")
        follower_calib.unlink()

    # Create robot instance
    print("Creating SO100 follower robot instance...")
    robot = make_robot_from_config(config)

    try:
        # Connect to the robot
        print(f"Connecting to port: {config.port}")
        robot.connect()

        # Get the motor bus
        bus = robot.bus

        print("\nMotor IDs:")
        for motor_name in bus.motors:
            print(f"- {motor_name}")
        
        # Test all motors to verify communication
        print("\nReading current positions for all motors:")
        try:
            for motor_name in bus.motors:
                position = bus.read("Present_Position", motor_name)
                print(f"- {motor_name}: {position}")
        except Exception as e:
            print(f"Error reading positions: {e}")

        print("\nFocusing on gripper motor...")

        # Enable torque
        print("Enabling torque on gripper...")
        try:
            bus.write("Torque_Enable", "gripper", True)
            print("Torque enabled successfully.")
        except Exception as e:
            print(f"Error enabling torque: {e}")
        
        # Debug calibration process step by step
        print("\n--- CALIBRATION DEBUGGING ---")
        
        # Zero position
        input("\nMove gripper to ZERO position (FULLY CLOSED), then press Enter...")
        try:
            zero_pos = bus.read("Present_Position", "gripper")
            print(f"Zero position value: {zero_pos}")
        except Exception as e:
            print(f"Error reading zero position: {e}")
            zero_pos = None

        # Rotated position
        input("\nMove gripper to ROTATED position (FULLY OPEN), then press Enter...")
        try:
            rotated_pos = bus.read("Present_Position", "gripper")
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
                    test_pos = bus.read("Present_Position", "gripper")
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
            if robot.is_connected:
                robot.disconnect()
        except Exception as e:
            print(f"Error disconnecting robot: {e}")

if __name__ == "__main__":
    debug_gripper()
