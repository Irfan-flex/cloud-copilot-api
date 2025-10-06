# Copyright Flexday Solutions LLC, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# See file LICENSE.txt for full license details.

from flask import Blueprint,request

home_blueprint = Blueprint('home', __name__)


@home_blueprint.route("/", methods=["GET"])
def index():
    """
    returns the string "OK" to check if the server is running.
    """
    return "OK"