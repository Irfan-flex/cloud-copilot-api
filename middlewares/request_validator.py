# Copyright Flexday Solutions LLC, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# See file LICENSE.txt for full license details.

from flask import request, abort
from constants import ROUTES_ALLOWING_JSON, MAX_CONTENT_LENGTH, MAX_REQUEST_FIELD_LENGTH, MAX_BODY_DEFAULT_VALUE_LENGTH, MAX_BODY_KEY_LENGTH, MAX_BODY_FIELDS, CUSTOM_JSON_LIMITS

def limit_body_size():
      # 100 KB for JSON/string-only apps
    skip_paths = ["/api/v1/whisper/transcribe"]
    if request.path in skip_paths:
        return
    if request.content_length and request.content_length > MAX_CONTENT_LENGTH:
        abort(413, "Request payload too large")

def validate_param_lengths():
    custom_limits = {
        "q": 1000         # Allow up to 5000 chars for user feedbac
    }
    for key, value in request.args.items():
        max_len = custom_limits.get(key, MAX_REQUEST_FIELD_LENGTH)
        if len(value) > max_len:
            abort(400, f"Query parameter '{key}' exceeds max length of {max_len} characters.")

def validate_json_fields():
    if not request.is_json:
        return  # Skip if not JSON

    try:
        data = request.get_json(force=True)
    except Exception:
        abort(400, "Invalid JSON payload.")


    if not isinstance(data, dict):
        abort(400, "JSON payload must be a flat object.")

    if len(data) > MAX_BODY_FIELDS:
        abort(400, f"Too many fields in JSON body (max {MAX_BODY_FIELDS}).")

    for k, v in data.items():
        # Reject if key name is too long
        if k not in CUSTOM_JSON_LIMITS and len(k) > MAX_BODY_KEY_LENGTH:
            abort(400, f"Key '{k}' exceeds max key length of {MAX_BODY_KEY_LENGTH} characters.")

        # Validate value lengths for string fields
        if isinstance(v, str):
            max_len = CUSTOM_JSON_LIMITS.get(k, MAX_BODY_DEFAULT_VALUE_LENGTH)
            if len(v) > max_len:
                abort(400, f"Value for key '{k}' exceeds max allowed length of {max_len} characters.")


def add_security_headers(response):
    # Disable caching for all responses
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

def enforce_json_only_on_certain_routes():
    if request.is_json and request.endpoint not in ROUTES_ALLOWING_JSON:
        abort(415, "This endpoint does not accept JSON input.")