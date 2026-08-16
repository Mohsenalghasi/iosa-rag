"""Call AWS Bedrock's chat endpoint to get an LLM text response.

Shared by every reasoning node in the agent (router, grade, rewrite,
generate), each passes its own prompt and system message. This module
has no task-specific logic, same pattern as embedder.py.
"""
import json
import os

import boto3
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")
BEDROCK_CHAT_MODEL = os.getenv("BEDROCK_CHAT_MODEL", "global.amazon.nova-2-lite-v1:0")

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    return _client


def chat(prompt: str, system: str = "", temperature: float = 0.0) -> str:
    """Send a prompt to the chat model, return its text reply."""
    client = _get_client()

    body = {
        "messages": [{"role": "user", "content": [{"text": prompt}]}],
        "inferenceConfig": {"temperature": temperature, "maxTokens": 2048},
    }
    if system:
        body["system"] = [{"text": system}]

    response = client.invoke_model(
        modelId=BEDROCK_CHAT_MODEL,
        body=json.dumps(body),
    )
    result = json.loads(response["body"].read())
    return result["output"]["message"]["content"][0]["text"]
