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
Helper to recalibrate your device (robot or teleoperator).

Examples:

Normal calibration:
```shell
lerobot-calibrate \
    --robot.type=so100_follower \
    --robot.port=/dev/tty.usbmodem58760431541
```

Run diagnostics before calibration (recommended for troubleshooting):
```shell
lerobot-calibrate \
    --robot.type=so100_follower \
    --robot.port=/dev/tty.usbmodem58760431541 \
    --diagnose
```
"""

import logging
from dataclasses import asdict, dataclass
from pprint import pformat

import draccus

from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig  # noqa: F401
from lerobot.cameras.realsense.configuration_realsense import RealSenseCameraConfig  # noqa: F401
from lerobot.robots import (  # noqa: F401
    Robot,
    RobotConfig,
    hope_jr,
    koch_follower,
    lekiwi,
    make_robot_from_config,
    omx_follower,
    so100_follower,
    so101_follower,
)
from lerobot.teleoperators import (  # noqa: F401
    Teleoperator,
    TeleoperatorConfig,
    homunculus,
    koch_leader,
    make_teleoperator_from_config,
    omx_leader,
    so100_leader,
    so101_leader,
)
from lerobot.utils.import_utils import register_third_party_plugins
from lerobot.utils.utils import init_logging


@dataclass
class CalibrateConfig:
    teleop: TeleoperatorConfig | None = None
    robot: RobotConfig | None = None
    diagnose: bool = False  # Run diagnostics instead of calibration

    def __post_init__(self):
        if bool(self.teleop) == bool(self.robot):
            raise ValueError("Choose either a teleop or a robot.")

        self.device = self.robot if self.robot else self.teleop


@draccus.wrap()
def calibrate(cfg: CalibrateConfig):
    init_logging()
    logging.info(pformat(asdict(cfg)))

    if isinstance(cfg.device, RobotConfig):
        device = make_robot_from_config(cfg.device)
    elif isinstance(cfg.device, TeleoperatorConfig):
        device = make_teleoperator_from_config(cfg.device)

    device.connect(calibrate=False)

    if cfg.diagnose:
        # Run diagnostics instead of calibration
        if not hasattr(device, "bus"):
            logging.error("This device does not have a motor bus. Diagnostics are not supported.")
            device.disconnect()
            return

        from lerobot.motors.diagnostics import diagnose_motor_bus

        logging.info("\n" + "=" * 60)
        logging.info("Running motor diagnostics...")
        logging.info("=" * 60)

        # Run diagnostics on all motors
        results = diagnose_motor_bus(device.bus, interactive=True)

        # Ask if user wants to proceed with calibration
        all_healthy = all(r.healthy for r in results.values())
        if all_healthy:
            user_input = input(
                "\n✓ Diagnostics passed! Would you like to proceed with calibration? (y/n): "
            )
            if user_input.strip().lower() == "y":
                logging.info("Proceeding with calibration...")
                device.calibrate()
        else:
            logging.error(
                "\n✗ Diagnostics failed. Please fix the issues above before attempting calibration."
            )
    else:
        # Normal calibration workflow
        device.calibrate()

    device.disconnect()


def main():
    register_third_party_plugins()
    calibrate()


if __name__ == "__main__":
    main()
