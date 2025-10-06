# Copyright Flexday Solutions LLC, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# See file LICENSE.txt for full license details.

class NoAnswerException(Exception):
    def __init__(self, message, errors):            
        # Call the base class constructor with the parameters it needs
        super().__init__(message)
            
        self.errors = errors