# Copyright 2024 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Diagnostic utilities for motor calibration troubleshooting.
"""

import logging
from dataclasses import dataclass
from typing import Any

from lerobot.motors.motors_bus import MotorsBus

logger = logging.getLogger(__name__)


@dataclass
class MotorDiagnosticResult:
    """Result of a motor diagnostic check."""

    motor_name: str
    healthy: bool
    position_readable: bool
    position_changes: bool
    position_range: float
    zero_position: float | None = None
    max_position: float | None = None
    warnings: list[str] = None
    errors: list[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.errors is None:
            self.errors = []


def diagnose_motor(bus: MotorsBus, motor_name: str, interactive: bool = True) -> MotorDiagnosticResult:
    """
    Diagnose a single motor for calibration issues.

    Args:
        bus: The motor bus to test
        motor_name: Name of the motor to diagnose
        interactive: If True, prompt user to move the motor

    Returns:
        MotorDiagnosticResult with diagnostic information
    """
    result = MotorDiagnosticResult(
        motor_name=motor_name,
        healthy=True,
        position_readable=False,
        position_changes=False,
        position_range=0.0,
    )

    logger.info(f"\n{'='*60}")
    logger.info(f"Diagnosing motor: {motor_name}")
    logger.info(f"{'='*60}")

    # Test 1: Check if motor position is readable
    try:
        initial_pos = bus.read("Present_Position", motor_name)
        result.position_readable = True
        logger.info(f"✓ Motor {motor_name} is readable. Current position: {initial_pos}")
    except Exception as e:
        result.healthy = False
        result.errors.append(f"Cannot read motor position: {e}")
        logger.error(f"✗ Cannot read position from {motor_name}: {e}")
        return result

    if not interactive:
        return result

    # Test 2: Check if position changes when motor is moved (zero position)
    input(f"\nMove '{motor_name}' to its MINIMUM/ZERO position (e.g., fully closed for gripper), then press ENTER...")
    try:
        zero_pos = bus.read("Present_Position", motor_name)
        result.zero_position = zero_pos
        logger.info(f"Zero position recorded: {zero_pos}")
    except Exception as e:
        result.healthy = False
        result.errors.append(f"Cannot read zero position: {e}")
        logger.error(f"✗ Cannot read zero position: {e}")
        return result

    # Test 3: Check maximum position
    input(f"\nMove '{motor_name}' to its MAXIMUM position (e.g., fully open for gripper), then press ENTER...")
    try:
        max_pos = bus.read("Present_Position", motor_name)
        result.max_position = max_pos
        logger.info(f"Maximum position recorded: {max_pos}")
    except Exception as e:
        result.healthy = False
        result.errors.append(f"Cannot read maximum position: {e}")
        logger.error(f"✗ Cannot read maximum position: {e}")
        return result

    # Calculate range
    position_diff = abs(max_pos - zero_pos)
    result.position_range = position_diff
    result.position_changes = position_diff > 0

    # Analyze results
    if position_diff == 0:
        result.healthy = False
        result.errors.append(
            "Position did not change between zero and max! This will cause division by zero during calibration."
        )
        logger.error(f"✗ CRITICAL: Zero position difference detected!")
        logger.error("   The motor position is not changing. Possible causes:")
        logger.error("   - Motor is not connected properly")
        logger.error("   - Wrong motor ID in configuration")
        logger.error("   - Motor is damaged or stuck")
    elif position_diff < 100:
        result.warnings.append(
            f"Very small position range ({position_diff:.1f}). This may cause calibration issues."
        )
        logger.warning(f"⚠ Small position range: {position_diff:.1f}")
        logger.warning("   This is unusually small and may indicate:")
        logger.warning("   - Motor has limited range of motion")
        logger.warning("   - Motor was not moved through full range")
    else:
        logger.info(f"✓ Position range looks good: {position_diff:.1f} units")
        result.position_changes = True

    # Test calibration formula
    if position_diff > 0:
        logger.info(f"\nTesting calibration formula:")
        logger.info(f"  Zero position: {zero_pos}")
        logger.info(f"  Max position: {max_pos}")
        logger.info(f"  Range: {position_diff}")

        # Test current position would calibrate correctly
        try:
            current_pos = bus.read("Present_Position", motor_name)
            calib_value = (current_pos - zero_pos) / position_diff * 100
            logger.info(f"  Current position {current_pos} → calibrated value: {calib_value:.2f}%")

            if calib_value < -10 or calib_value > 110:
                result.warnings.append(
                    f"Current position calibrates to {calib_value:.2f}% (outside normal range [-10, 110])"
                )
                logger.warning(
                    f"⚠ Current calibrated value {calib_value:.2f}% is outside acceptable range"
                )
        except Exception as e:
            logger.warning(f"⚠ Could not test calibration formula: {e}")

    return result


def diagnose_motor_bus(
    bus: MotorsBus, motors: list[str] | None = None, interactive: bool = True
) -> dict[str, MotorDiagnosticResult]:
    """
    Run diagnostics on multiple motors.

    Args:
        bus: The motor bus to test
        motors: List of motor names to test. If None, test all motors.
        interactive: If True, prompt user to move motors

    Returns:
        Dictionary mapping motor names to diagnostic results
    """
    if motors is None:
        motors = list(bus.motors.keys())

    results = {}
    for motor_name in motors:
        results[motor_name] = diagnose_motor(bus, motor_name, interactive)

    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info("DIAGNOSTIC SUMMARY")
    logger.info(f"{'='*60}")

    all_healthy = True
    for motor_name, result in results.items():
        status = "✓ PASS" if result.healthy else "✗ FAIL"
        logger.info(f"{motor_name}: {status}")

        if result.errors:
            for error in result.errors:
                logger.error(f"  ERROR: {error}")
            all_healthy = False

        if result.warnings:
            for warning in result.warnings:
                logger.warning(f"  WARNING: {warning}")

    if all_healthy:
        logger.info("\n✓ All motors passed diagnostics. You can proceed with calibration.")
    else:
        logger.error("\n✗ Some motors failed diagnostics. Please fix the issues before calibrating.")

    return results
