import json
import ulid
import logging
import aioboto3
import asyncio
from utils.env_config import AWS_AGENT_CONFIG

logger = logging.getLogger(__name__)

class BedrockService:
    def __init__(self):
        self.agent_id = AWS_AGENT_CONFIG.AGENT_ID
        self.agent_alias_id = AWS_AGENT_CONFIG.AGENT_ALIAS_ID
        self.session = aioboto3.Session()
        self.region = "us-east-1"  
        logger.info(f"[BedrockService] Initialized with AgentID={self.agent_id}, AliasID={self.agent_alias_id}, Region={self.region}")

    async def _invoke_agent_async(self, user_input: str, session_id: str):
        """Internal async agent invocation."""
        # 👇 Pass region_name here, not in invoke_agent()
        async with self.session.client("bedrock-agent-runtime", region_name=self.region) as client:
            response = await client.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId=session_id,
                inputText=user_input,
                enableTrace=True,
            )

            chunks = []
            traces = []
            async for event in response["completion"]:
                if "chunk" in event:
                    chunks.append(event["chunk"]["bytes"].decode("utf-8"))
                elif "trace" in event:
                    traces.append(event["trace"])
                    logger.debug("[BedrockService] Trace: %s", json.dumps(event["trace"], default=str))
                else:
                    logger.debug("[BedrockService] Unknown completion event: %s", event)

            return {
                "response": "".join(chunks),
                "session_id": session_id,
                "traces": traces
            }

    def process_query(self, user_input: str, session_id: str = None):
        """Synchronous wrapper for Flask to call async Bedrock agent."""
        session_id = session_id or str(ulid.ulid())
        logger.info(f"[BedrockService] Invoking agent | Session={session_id}, Query={user_input}")

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        try:
            return loop.run_until_complete(self._invoke_agent_async(user_input, session_id))
        except Exception as e:
            logger.exception(f"[BedrockService] Failed to invoke agent: {e}")
            raise
