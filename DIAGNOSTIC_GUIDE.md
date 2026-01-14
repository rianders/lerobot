# Motor Calibration Diagnostics Guide

## Overview

The `--diagnose` flag for `lerobot-calibrate` helps troubleshoot motor calibration issues before they cause failures. It runs pre-calibration health checks on your robot's motors and identifies common problems.

## Quick Start

### Run diagnostics before calibration:

```bash
lerobot-calibrate \
    --robot.type=so100_follower \
    --robot.port=/dev/tty.usbmodem58760431541 \
    --diagnose
```

### For teleoperators:

```bash
lerobot-calibrate \
    --teleop.type=so100_leader \
    --teleop.port=/dev/tty.usbmodem58760431551 \
    --diagnose
```

## What It Tests

For each motor, the diagnostic checks:

1. **Communication** - Can we read the motor's position?
2. **Position Changes** - Does the position update when you move the motor?
3. **Range Validity** - Is the motion range reasonable for calibration?
4. **Calibration Formula** - Will the calibration math work with this motor?

## Example Session

```
$ lerobot-calibrate --robot.type=so100_follower --robot.port=/dev/tty.usbmodem123 --diagnose

============================================================
Running motor diagnostics...
============================================================

============================================================
Diagnosing motor: shoulder_pan
============================================================
✓ Motor shoulder_pan is readable. Current position: 2048

Move 'shoulder_pan' to its MINIMUM/ZERO position, then press ENTER...
Zero position recorded: 512

Move 'shoulder_pan' to its MAXIMUM position, then press ENTER...
Maximum position recorded: 3584

✓ Position range looks good: 3072.0 units

Testing calibration formula:
  Zero position: 512
  Max position: 3584
  Range: 3072.0
  Current position 2048 → calibrated value: 50.00%

[... continues for each motor ...]

============================================================
DIAGNOSTIC SUMMARY
============================================================
shoulder_pan: ✓ PASS
shoulder_lift: ✓ PASS
elbow_flex: ✓ PASS
wrist_flex: ✓ PASS
wrist_roll: ✓ PASS
gripper: ✓ PASS

✓ All motors passed diagnostics. You can proceed with calibration.

✓ Diagnostics passed! Would you like to proceed with calibration? (y/n): y
Proceeding with calibration...
```

## Common Issues Detected

### Issue 1: Zero Position Difference

**Symptom:**
```
✗ CRITICAL: Zero position difference detected!
  The motor position is not changing. Possible causes:
  - Motor is not connected properly
  - Wrong motor ID in configuration
  - Motor is damaged or stuck
```

**Fix:**
- Check USB cable connection
- Verify motor ID matches configuration
- Try moving motor manually to ensure it's not mechanically stuck
- Use `lerobot-setup-motors` to reconfigure motor IDs

### Issue 2: Small Position Range

**Symptom:**
```
⚠ Small position range: 42.0
  This is unusually small and may indicate:
  - Motor has limited range of motion
  - Motor was not moved through full range
```

**Fix:**
- Move the motor through its **complete** range during diagnostic
- For gripper: fully open AND fully closed
- For joints: move to mechanical stops on both ends

### Issue 3: Out-of-Range Calibration Values

**Symptom:**
```
⚠ Current position calibrates to 125.50% (outside normal range [-10, 110])
```

**Fix:**
- This typically happens when zero/max positions were recorded incorrectly
- Rerun diagnostics and ensure you move to actual min/max positions
- For gripper specifically: make sure you're testing the full open-to-closed range

### Issue 4: Cannot Read Motor

**Symptom:**
```
✗ Cannot read position from gripper: [Errno 5] Input/output error
```

**Fix:**
- Check USB connection
- Verify correct port in config (use `lerobot-find-port` to identify)
- Ensure motor has power
- Check that only one process is accessing the port
- Try unplugging/replugging USB cable

## Using Diagnostics Programmatically

You can also use the diagnostic functions in your own scripts:

```python
from lerobot.motors import diagnose_motor_bus
from lerobot.robots import make_robot_from_config
from lerobot.robots.so100_follower.config_so100_follower import SO100FollowerConfig

# Create and connect robot
config = SO100FollowerConfig(port="/dev/tty.usbmodem123")
robot = make_robot_from_config(config)
robot.connect(calibrate=False)

# Run diagnostics
results = diagnose_motor_bus(robot.bus, motors=["gripper"], interactive=True)

# Check results
if results["gripper"].healthy:
    print("Gripper is healthy!")
else:
    print(f"Gripper has issues: {results['gripper'].errors}")

robot.disconnect()
```

## When to Use Diagnostics

### Always use diagnostics when:
- Setting up a new robot for the first time
- Calibration is failing with cryptic errors
- A specific motor isn't behaving correctly
- You suspect hardware issues

### Optional for:
- Routine recalibrations on known-good hardware
- Production environments with tested configurations

## Integration with Existing Debug Scripts

The `--diagnose` flag replaces the standalone `debug_gripper.py` scripts with an integrated solution that:
- Works with all robot types (not just SO100)
- Provides consistent error messages
- Offers option to proceed with calibration if diagnostics pass
- Requires no code modifications

## Tips

1. **Run diagnostics first** - Always use `--diagnose` before attempting calibration on new hardware
2. **Read errors carefully** - The diagnostic messages include suggested fixes
3. **Test one motor at a time** - If you suspect a specific motor, focus diagnostics there
4. **Move through full range** - Ensure you move each motor completely during position tests
5. **Check cables** - Most issues are connection-related

## Troubleshooting the Diagnostics Tool

If the diagnostic tool itself isn't working:

1. Ensure you're using the latest version: `git pull origin main`
2. Verify the robot type is correct: `--robot.type=so100_follower` (not so100)
3. Check that the device has a motor bus (some robots may not support diagnostics)
4. Look for import errors in the output

## Contributing

Found a bug or have suggestions? Open an issue at:
https://github.com/rianders/lerobot/issues
