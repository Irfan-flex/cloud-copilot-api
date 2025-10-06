# Copyright Flexday Solutions LLC, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# See file LICENSE.txt for full license details.

import jwt
import json
import urllib3
import logging
import time
from flask import request, g, abort
from functools import wraps
from constants import AUTH_HEADER_NAME, AUTH_SCHEME
from utils.env_config import OIDC_CONFIG, APP_CONFIG

logger = logging.getLogger(__name__)

# Cache for JWKS
JWKS = None
JWKS_TIMESTAMP = 0
KEY_CACHE = {}
JWKS_CACHE_DURATION = 3600

http = urllib3.PoolManager()


def get_jwks():
    """Fetch JWKS from OIDC provider (Cognito) with caching"""
    global JWKS, JWKS_TIMESTAMP

    current_time = time.time()

    if JWKS is None or (current_time - JWKS_TIMESTAMP) > JWKS_CACHE_DURATION:
        config_url = OIDC_CONFIG.OIDC_CONFIG_URL
        logger.info(f"Fetching OIDC config from: {config_url}")

        try:
            config_response = http.request('GET', config_url)
            if config_response.status != 200:
                raise ValueError(
                    f"Failed to fetch OIDC config: {config_response.status}")

            oidc_config = json.loads(config_response.data)
            jwks_url = oidc_config['jwks_uri']
            logger.info(f"Found JWKS URI: {jwks_url}")

            jwks_response = http.request('GET', jwks_url)
            if jwks_response.status != 200:
                raise ValueError(
                    f"Failed to fetch JWKS: {jwks_response.status}")

            JWKS = json.loads(jwks_response.data)['keys']
            JWKS_TIMESTAMP = current_time
            KEY_CACHE.clear()

            logger.info(f"JWKS refreshed successfully with {len(JWKS)} keys.")
        except Exception as e:
            logger.error(f"JWKS fetch exception: {str(e)}", exc_info=True)
            raise
    else:
        logger.debug("Using cached JWKS")

    return JWKS


def authorize(required=True):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            g.user = None

            if not APP_CONFIG.AUTH_ENABLED:
                logger.info("Auth disabled. Setting debug user.")
                g.user = {"username": "debug-user"}
                return f(*args, **kwargs)

            auth_header_value = request.headers.get(AUTH_HEADER_NAME)
            if not auth_header_value:
                if required:
                    abort(401, "Authorization header is required.")
                logger.info("No auth header found. Proceeding as anonymous.")
                return f(*args, **kwargs)

            try:
                parts = auth_header_value.split(" ")
                if len(parts) != 2 or parts[0] != AUTH_SCHEME:
                    abort(401, "Invalid auth header format.")

                token = parts[1]
                header = jwt.get_unverified_header(token)
                kid = header.get("kid")
                if not kid:
                    raise ValueError("Token header missing 'kid'")

                jwks_keys = get_jwks()
                key_data = next(
                    (k for k in jwks_keys if k['kid'] == kid), None)
                if not key_data:
                    raise ValueError("Matching key not found in JWKS")

                public_key = jwt.algorithms.RSAAlgorithm.from_jwk(
                    json.dumps(key_data))

                logger.info("Decoding and verifying access token...")
                decoded = jwt.decode(
                    token,
                    public_key,
                    algorithms=["RS256"],
                    audience=OIDC_CONFIG.OIDC_API_AUDIENCE,  # << Use API Audience here
                    issuer=OIDC_CONFIG.OIDC_TOKEN_ISSUER
                )

                g.user = {
                    "username": decoded.get("cognito:username") or decoded.get("sub"),
                    "claims": decoded
                }

                logger.info(
                    f"Token verified. Authenticated as: {g.user.get('username')}")

            except Exception as e:
                logger.warning(f"Access token validation failed: {str(e)}")
                if required:
                    abort(401, f"Unauthorized: {str(e)}")

            return f(*args, **kwargs)
        return decorated_function
    return decorator
