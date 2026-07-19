"""
Demo: stop_sequences not working through the Qualcomm internal Anthropic gateway.

This script isolates one variable at a time to prove the client SDK sends the
parameter correctly, but the gateway (ANTHROPIC_BASE_URL) ignores it.
"""
from dotenv import load_dotenv
load_dotenv()

import httpx
from anthropic import Anthropic

client = Anthropic(http_client=httpx.Client(verify=False))
model = "claude-haiku-4-5"

print("=" * 70)
print("TEST: stop_sequences=['5'] on 'count 1 to 10'")
print("Expected if working: text stops at '5', stop_reason == 'stop_sequence'")
print("=" * 70)

resp = client.messages.create(
    model=model,
    max_tokens=100,
    messages=[{"role": "user", "content": "Count from 1 to 10, one number per line."}],
    stop_sequences=["5"],
)

text = resp.content[0].text
print("stop_reason:  ", resp.stop_reason)
print("stop_sequence:", resp.stop_sequence)
print("text:         ", repr(text))
print()

if resp.stop_reason == "stop_sequence":
    print("RESULT: stop_sequences WORKED as expected.")
else:
    print("RESULT: stop_sequences was IGNORED (stop_reason should be 'stop_sequence' but is 'end_turn').")
