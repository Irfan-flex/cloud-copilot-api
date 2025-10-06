# routes/bedrock_route.py
import logging
from flask import Blueprint, request, jsonify
from services.bedrock_service import BedrockService

logger = logging.getLogger(__name__)

bedrock_blueprint = Blueprint("bedrock", __name__, url_prefix="/aws")


bedrock_service = BedrockService()

@bedrock_blueprint.route("/chat", methods=["POST"])
def query_bedrock():
    """
    Query the Bedrock agent with user input and optional session continuation.
    Form data: query=<string>&session_id=<optional>
    """
    data = request.form  # Use form data for x-www-form-urlencoded
    user_input = data.get("query")
    session_id = data.get("session_id")

    if not user_input:
        return jsonify({"error": "Missing 'query' field"}), 400

    user_id = "ANON"

    logger.info(
        f"[BedrockRoute] Session={session_id or 'NEW'}, User={user_id}, Query={user_input}"
    )

    try:
        result = bedrock_service.process_query(user_input, session_id)
        return jsonify({
            "response": result.get("response"),
            "session_id": result.get("session_id"),
            "traces": result.get("traces", []),
            "user_id": user_id,
        })
    except Exception as e:
        logger.exception(f"[BedrockRoute] Agent invocation failed: {e}")
        return jsonify({"error": f"Agent invocation failed: {e}"}), 500
