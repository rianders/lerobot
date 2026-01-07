#!/usr/bin/env python3
"""
Minimal debug script for the Feetech gripper calibration issue.
Direct approach using SO100FollowerConfig.
"""

import time
from pathlib import Path

from lerobot.robots import make_robot_from_config
from lerobot.robots.so100_follower.config_so100_follower import SO100FollowerConfig


def debug_gripper():
    """Test the gripper servo to diagnose calibration issues using direct approach."""
    print("Starting minimal Feetech gripper debugging test...")

    # Remove existing calibration file to force recalibration
    calib_dir = Path(".cache/calibration/so100_follower")
    calib_dir.mkdir(parents=True, exist_ok=True)

    follower_calib = calib_dir / "calibration.json"
    if follower_calib.exists():
        print(f"Removing existing calibration file: {follower_calib}")
        follower_calib.unlink()

    # Create SO100 follower config
    # Update the port to match your device
    config = SO100FollowerConfig(
        port="/dev/tty.usbmodem59700726961",  # Update this to your actual port
        mock=False,
    )

    # Create robot instance
    print("Creating SO100 follower robot instance...")
    robot = make_robot_from_config(config)

    try:
        # Connect
        print(f"\nConnecting to port: {config.port}")
        robot.connect()

        bus = robot.bus

        if not robot.is_connected:
            print("ERROR: Failed to connect!")
            return

        # Read positions
        print("\nReading current positions:")
        try:
            for motor_name in bus.motors:
                position = bus.read("Present_Position", motor_name)
                print(f"- {motor_name}: {position}")
        except Exception as e:
            print(f"Error reading positions: {e}")
            import traceback
            traceback.print_exc()
            return

        # Focus on gripper
        print("\n--- GRIPPER TESTING ---")

        # Enable torque
        print("Enabling torque on gripper...")
        try:
            bus.write("Torque_Enable", "gripper", True)
        except Exception as e:
            print(f"Error enabling torque: {e}")
            return

        # Record positions for calibration debugging
        print("\n--- CALIBRATION POSITION TESTING ---")

        # Zero position
        input("\nMove gripper to ZERO position (FULLY CLOSED), then press Enter...")
        zero_pos = bus.read("Present_Position", "gripper")
        print(f"Zero position value: {zero_pos}")

        # Rotated position
        input("\nMove gripper to ROTATED position (FULLY OPEN), then press Enter...")
        rotated_pos = bus.read("Present_Position", "gripper")
        print(f"Rotated position value: {rotated_pos}")
        
        # Calculate difference
        difference = rotated_pos - zero_pos
        print(f"\nDifference between positions: {difference}")
        
        if difference == 0:
            print("ERROR: Zero difference! This will cause division by zero in calibration.")
        elif abs(difference) < 10:
            print(f"WARNING: Very small difference ({difference})! This might cause calibration issues.")
        else:
            print("Position difference seems acceptable.")
        
        # Test calibration formula
        print("\n--- ADDITIONAL TESTING ---")
        for i in range(3):
            input(f"\nTest {i+1}: Move gripper to a different position, then press Enter...")
            test_pos = bus.read("Present_Position", "gripper")
            print(f"Position value: {test_pos}")
            
            if difference != 0:
                calib_val = (test_pos - zero_pos) / difference * 100
                print(f"Calibrated value: {calib_val:.2f}%")
                
                if calib_val < -10 or calib_val > 110:
                    print(f"WARNING: Value {calib_val:.2f}% is outside acceptable range [-10, 110]%")
            else:
                print("Cannot calculate calibrated value due to zero difference")
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nDisconnecting...")
        if hasattr(robot, 'disconnect'):
            robot.disconnect()

if __name__ == "__main__":
    debug_gripper()
