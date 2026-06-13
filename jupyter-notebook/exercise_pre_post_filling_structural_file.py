from dotenv import load_dotenv
load_dotenv()

import httpx
from anthropic import Anthropic

client = Anthropic(http_client=httpx.Client(verify=False))

model = "claude-sonnet-4-6"

