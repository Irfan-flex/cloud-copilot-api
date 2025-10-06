# Copyright Flexday Solutions LLC, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# See file LICENSE.txt for full license details.

from utils.storage_util import create_dir_path
from utils.env_config import APP_CONFIG, SWAGGER_CONFIG
from middlewares.request_validator import (
    enforce_json_only_on_certain_routes,
    limit_body_size,
    validate_param_lengths,
    validate_json_fields,
    add_security_headers
)
from middlewares.error_handler_middleware import errorHandler
# from routes.polly_route import polly_blueprint
# from routes.whisper_route import whisper_blueprint
# from routes.health_route import health_blueprint
from routes.home_route import home_blueprint
from routes.cost_route import cost_blueprint
from routes.inventory_route import inventory_blueprint
from routes.utilisation_route import utilisation_blueprint
from routes.recommend_route import recommend_blueprint
from routes.alerts_route import alerts_blueprint
from flask_swagger_ui import get_swaggerui_blueprint
from constants import SWAGGER_URL, API_URL
from services.cache_service import init_cache
# import torch
from flask_talisman import Talisman
from datetime import timedelta
from flask import Flask
import logging
import services.logging_service
from werkzeug.middleware.proxy_fix import ProxyFix
from gevent.pywsgi import WSGIServer
from routes.bedrock_route import bedrock_blueprint
# from gevent import monkey
# monkey.patch_all()
from flask_cors import CORS


init_cache()
# torch.set_num_threads(1)
# create_dir_path("audios")

logger = logging.getLogger(__name__)

application = Flask(__name__, static_folder='api')

# Initialize Talisman with default security settings
if APP_CONFIG.ENABLE_HSTS:
    talisman = Talisman(application, force_https=True, strict_transport_security=True, content_security_policy={
        'default-src': '\'self\'',
        'script-src': '\'self\'',
    }, force_https_permanent=True)

application.secret_key = APP_CONFIG.APP_SECRET
application.wsgi_app = ProxyFix(application.wsgi_app, x_proto=1, x_host=1)
application.url_map.strict_slashes = False

CORS(application, origins=["http://localhost:5173"], methods='GET,POST, PUT, PATCH, DELETE, OPTIONS', allow_headers=['Authorization', 'Content-Type'], supports_credentials=True, max_age=86400)

application.config.update(
    # Prevents CSRF by sending cookie only on same-site requests
    SESSION_COOKIE_SAMESITE=APP_CONFIG.SESSION_COOKIE_SAMESITE,
    # Ensures cookie is sent via HTTPS
    SESSION_COOKIE_SECURE=APP_CONFIG.SESSION_COOKIE_SECURE,
    # Ensures cookie is inaccessible to JavaScript
    SESSION_COOKIE_HTTPONLY=APP_CONFIG.SESSION_COOKIE_HTTPONLY,
    PERMANENT_SESSION_LIFETIME=timedelta(
        minutes=APP_CONFIG.PERMANENT_SESSION_LIFETIME),  # Set session to expire
    # prevent caching of static files
    SEND_FILE_MAX_AGE_DEFAULT=APP_CONFIG.SEND_FILE_MAX_AGE_DEFAULT,

)

application.before_request(limit_body_size)
application.before_request(validate_param_lengths)
application.before_request(validate_json_fields)
application.before_request(enforce_json_only_on_certain_routes)

# Add security headers after each request
application.after_request(add_security_headers)


V1_ROUTE_PREFIX = '/api/v1'

SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Delmonte Customer Support"
    }
)

if SWAGGER_CONFIG.SWAGGER_ENABLED:
    application.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)


application.register_blueprint(
    home_blueprint, url_prefix="")
# application.register_blueprint(
#     health_blueprint, url_prefix=V1_ROUTE_PREFIX)
application.register_blueprint(
    cost_blueprint, url_prefix=V1_ROUTE_PREFIX)
application.register_blueprint(
    inventory_blueprint, url_prefix=V1_ROUTE_PREFIX)
application.register_blueprint(
    alerts_blueprint, url_prefix=V1_ROUTE_PREFIX
)
application.register_blueprint(
    utilisation_blueprint, url_prefix=V1_ROUTE_PREFIX
)
application.register_blueprint(
    recommend_blueprint, url_prefix=V1_ROUTE_PREFIX
)

# application.register_blueprint(
#     polly_blueprint, url_prefix=V1_ROUTE_PREFIX
# )
application.register_blueprint(errorHandler)


application.register_blueprint(
    bedrock_blueprint, url_prefix=V1_ROUTE_PREFIX
)

if __name__ == "__main__":
    # Wrap up the Flask App using Gevent
    http_server = WSGIServer((APP_CONFIG.HOST, APP_CONFIG.PORT), application)
    http_server.serve_forever()
