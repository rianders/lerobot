#!/usr/bin/env python3
"""
Minimal debug script for the Feetech gripper calibration issue.
"""

import os
import time
from pathlib import Path

# Direct import of just the robot module for SO100
from lerobot.common.robot_devices.robots.manipulator import ManipulatorRobot

def debug_gripper():
    """Test the gripper servo to diagnose calibration issues using direct approach."""
    print("Starting minimal Feetech gripper debugging test...")
    
    # Remove existing calibration file to force recalibration
    calib_dir = Path(".cache/calibration/so100")
    calib_dir.mkdir(parents=True, exist_ok=True)
    
    follower_calib = calib_dir / "main_follower.json"
    if follower_calib.exists():
        print(f"Removing existing calibration file: {follower_calib}")
        follower_calib.unlink()
    
    # Create a minimal robot configuration manually
    robot_config = {
        'type': 'so100',
        'calibration_dir': '.cache/calibration/so100',
        'mock': False,
        'follower_arms': {
            'main': {
                'mock': False,
                'port': '/dev/tty.usbmodem59700726961',  # This should be the same port from your error logs
                'motors': {
                    'shoulder_pan': [1, 'sts3215'],
                    'shoulder_lift': [2, 'sts3215'],
                    'elbow_flex': [3, 'sts3215'],
                    'wrist_flex': [4, 'sts3215'],
                    'wrist_roll': [5, 'sts3215'],
                    'gripper': [6, 'sts3215']
                }
            }
        },
        'leader_arms': {
            'main': {
                'mock': True,
                'port': '/dev/tty.usbmodem59700726161',  # Not used since mocked
                'motors': {
                    'shoulder_pan': [1, 'sts3215'],
                    'shoulder_lift': [2, 'sts3215'],
                    'elbow_flex': [3, 'sts3215'],
                    'wrist_flex': [4, 'sts3215'],
                    'wrist_roll': [5, 'sts3215'],
                    'gripper': [6, 'sts3215']
                }
            }
        }
    }
    
    # Create robot instance directly
    print("Creating robot instance with hardcoded config...")
    robot = ManipulatorRobot("so100", robot_config)
    
    try:
        # Connect only the follower arm
        print("\nConnecting only the follower arm...")
        robot._connect_arm('follower_arms', 'main')
        
        if not hasattr(robot, 'follower_arms') or 'main' not in robot.follower_arms:
            print("ERROR: Failed to connect to follower arm!")
            return
            
        arm = robot.follower_arms['main']
        
        # Read positions
        print("\nReading current positions:")
        try:
            positions = arm.read("Present_Position")
            for motor_name, position in positions.items():
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
            arm.write("Torque_Enable", {"gripper": True})
        except Exception as e:
            print(f"Error enabling torque: {e}")
            return
        
        # Record positions for calibration debugging
        print("\n--- CALIBRATION POSITION TESTING ---")
        
        # Zero position
        input("\nMove gripper to ZERO position (FULLY CLOSED), then press Enter...")
        zero_pos = arm.read("Present_Position")["gripper"]
        print(f"Zero position value: {zero_pos}")
        
        # Rotated position
        input("\nMove gripper to ROTATED position (FULLY OPEN), then press Enter...")
        rotated_pos = arm.read("Present_Position")["gripper"]
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
            test_pos = arm.read("Present_Position")["gripper"]
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
