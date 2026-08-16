"""Call AWS Bedrock's Titan embedding endpoint to turn text into vectors.

Used both at indexing time (embedding child chunks) and query time
(embedding the user's question), so retrieval and indexing always
share the same embedding space.
"""
import json
import os

import boto3
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")
BEDROCK_EMBED_MODEL = os.getenv("BEDROCK_EMBED_MODEL", "amazon.titan-embed-text-v2:0")

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    return _client


def embed_text(text: str) -> list[float]:
    """Embed a single string of text, returns a vector as a list of floats."""
    client = _get_client()
    response = client.invoke_model(
        modelId=BEDROCK_EMBED_MODEL,
        body=json.dumps({"inputText": text}),
    )
    result = json.loads(response["body"].read())
    return result["embedding"]
