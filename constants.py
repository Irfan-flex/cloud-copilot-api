# Copyright Flexday Solutions LLC, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# See file LICENSE.txt for full license details.

AUTH_HEADER_NAME = "authorization"
AUTH_SCHEME = "Bearer"
TRUE_STRING = "true"
EXCEPTION_HTTP_STATUS_CODE = 500
EXCEPTION_HTTP_STATUS_TYPE = 'Internal Server Error'
SWAGGER_URL = '/api/v1/swagger'
API_URL = '/api/static/swagger.json'
PRODUCT_DENSE_RETRIEVER_KEY="products_dense_retriever"
SCRIPTS_DENSE_RETRIEVER_KEY="scripts_dense_retriever"
PRODUCTS_SPARSE_RETRIEVER_KEY="products_sparse_retriever"
FAQ_DENSE_RETRIEVER_KEY="faq_dense_retriever"
BASE_URL = "https://www.delmontefoods.com"
PRESS_RELEASE_URL = "https://www.delmontefoods.com/news/press-releases?page="
MAX_RETRIES = 3

ROUTES_ALLOWING_JSON = {
    "chat.post_feedback",
    "gtts.synthesize_route"
}
CUSTOM_JSON_LIMITS = {
    "feedback": 250,
    "name": 50,
    "contact": 25,
    "upc": 12,
    "zipCode": 10,
    "mfgCode": 6,
    "store": 200
}

MAX_CONTENT_LENGTH = 100 * 1024
MAX_REQUEST_FIELD_LENGTH = 256
MAX_BODY_KEY_LENGTH = 100
MAX_BODY_DEFAULT_VALUE_LENGTH = 1000
MAX_BODY_FIELDS = 10
ROLE_USER= "user"
ROLE_ASSISTANT="assistant"
ROLE_SYSTEM="system"
INPUT_TYPE_FEEDBACK="feedback"
SYSTEM_PROMPT= "You Nova, are a customer support assistant for Del Monte Food product Company, tasked with providing accurate and helpful responses to customers on wide range of topics including ingredients, nutritional facts, complaints, comments, expiry, health advice, suitability for consumption, expiry details, feedback among others."


conversation_flow = {
    'start': """I am Nova from Del Monte foods. I can assist you with queries related to our products, where to buy them, complaints, feedback etc.
\n &nbsp;
What can I help you with?""",
    "feedback_response" : "Thank you! Your feedback has been submitted successfully. Let me know if you need help with anything else."
}