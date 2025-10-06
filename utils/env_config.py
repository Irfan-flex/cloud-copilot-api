# Copyright Flexday Solutions LLC, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# See file LICENSE.txt for full license details.
import os
from constants import TRUE_STRING
from utils.map import Map
from utils.string_util import str_lower, parse_cors_origins
from dotenv import load_dotenv

load_dotenv(override=True)


APP_CONFIG = Map(
    HOST=os.getenv('HOST'),
    PORT=int(os.getenv('PORT')),
    DEBUG=True if str_lower(os.getenv('ENABLE_DEBUG')
                            ) == TRUE_STRING else False,
    LOG_LEVEL='NOTSET' if not os.getenv(
        'LOG_LEVEL') else os.getenv('LOG_LEVEL'),
    APP_SECRET=os.getenv("APP_SECRET"),
    ENABLE_HSTS=True if str_lower(
        os.getenv("ENABLE_HSTS")) == TRUE_STRING else False,
    AUTH_ENABLED=True if str_lower(os.getenv(
        'AUTH_ENABLED')) == TRUE_STRING else False,
    ENABLE_ENCRYPT=True if str_lower(os.getenv(
        'ENABLE_ENCRYPT')) == TRUE_STRING else False,
    SESSION_COOKIE_SECURE=True if str_lower(os.getenv(
        'SESSION_COOKIE_SECURE')) == TRUE_STRING else False,
    SESSION_COOKIE_SAMESITE=os.getenv('SESSION_COOKIE_SAMESITE'),
    SESSION_COOKIE_HTTPONLY=os.getenv('SESSION_COOKIE_HTTPONLY'),
    PERMANENT_SESSION_LIFETIME=int(os.getenv('PERMANENT_SESSION_LIFETIME')),
    SEND_FILE_MAX_AGE_DEFAULT=int(os.getenv('SEND_FILE_MAX_AGE_DEFAULT')),
    # ALLOWED_CORS_ORIGIN=os.getenv('CORS_ORIGIN'),
    ALLOWED_CORS_ORIGIN=parse_cors_origins(os.getenv('CORS_ORIGIN', '')),
    API_URL=os.getenv('API_URL')
)


OIDC_CONFIG = Map(
    OIDC_CONFIG_URL=os.getenv('OIDC_CONFIG_URL'),
    OIDC_TOKEN_AUDIENCE=os.getenv('OIDC_TOKEN_AUDIENCE'),
    OIDC_TOKEN_ISSUER=os.getenv('OIDC_TOKEN_ISSUER')
)


SWAGGER_CONFIG = Map(
    SWAGGER_ENABLED=True if str_lower(os.getenv(
        'SWAGGER_ENABLED')) == TRUE_STRING else False
)

DB_CONFIG = Map(
    MONGODB_HOST_URI=os.getenv('MONGODB_HOST_URI'),
    MONGODB_DBNAME=os.getenv('MONGODB_DBNAME'),
    MONGODB_MAX_POOLSIZE=os.getenv('MONGODB_MAX_POOLSIZE', 100),
    MONGODB_MIN_POOLSIZE=os.getenv('MONGODB_MIN_POOLSIZE', 0),
    MONGODB_MAX_IDLETIME_MS=os.getenv('MONGODB_MAX_IDLETIME_MS', None),
    MONGODB_MAX_CONNECTING=os.getenv('MONGODB_MAX_CONNECTING', 2)
)


AWS_CONFIG = Map(
    KMS_KEY_ID=os.getenv('KMS_KEY_ID'),
    KMS_REGION=os.getenv('KMS_REGION')
)

OIDC_CONFIG = Map(
    OIDC_CONFIG_URL=os.getenv('OIDC_CONFIG_URL'),
    OIDC_TOKEN_AUDIENCE=[origin.strip() for origin in os.getenv(
        'OIDC_TOKEN_AUDIENCE').split(',') if origin.strip()],
    OIDC_TOKEN_ISSUER=os.getenv('OIDC_TOKEN_ISSUER'),
    OIDC_AUTH_PROVIDER=os.getenv('OIDC_AUTH_PROVIDER'),
)


AWS_AGENT_CONFIG = Map(
    AGENT_ID=os.getenv('AGENT_ID'),
    AGENT_ALIAS_ID=os.getenv('AGENT_ALIAS_ID')
)