# Copyright Flexday Solutions LLC, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# See file LICENSE.txt for full license details.

import logging
from utils.env_config import APP_CONFIG

logging.basicConfig(format='%(name)s %(levelname)s %(asctime)s: %(message)s',
                    level=APP_CONFIG.LOG_LEVEL)