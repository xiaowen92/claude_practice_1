from dotenv import load_dotenv
load_dotenv()

import httpx
from anthropic import Anthropic

client = Anthropic(http_client=httpx.Client(verify=False))

model = "claude-sonnet-4-6"

def add_user_message(messages, content):
    messages.append({
        "role": "user",
        "content": content
    })

def add_assistant_message(messages, content):
    messages.append({
        "role": "assistant",
        "content": content
    })

def chat_log (messages,system=None, stop_sequences = None):
    # we do if condition to avoid sending system as None to the API, which will cause err
    params = {
        "model": model,
        "max_tokens": 1000,
        "messages": messages
    }

    if system:
        params["system"] = system
    if stop_sequences:
        params["stop_sequences"] = stop_sequences

    response = client.messages.create(**params) 

    return response.content[0].text

system = " reply should be limited to 100 words"

# messages = [] 

# prompt = "generate 3 different sample aws cli commands, each should be very short"

# add_user_message(messages=messages, content = prompt )

# print(f"messages currently is {messages}" )

# response1 = chat_log(messages=messages, system=system)

# add_assistant_message(messages=messages, content=response1)

# print(f"messages currently is {messages}" )


##Added prefilling 
messages1 = [] 

prompt = "generate 3 different sample aws cli commands, each should be very short"

add_user_message(messages=messages1, content = prompt )

print(f"messages currently is {messages1}" )

add_assistant_message(messages=messages1, content='```')

response2 = chat_log(messages=messages1, system=system, stop_sequences = ['```'])

print(f"response currently is {response2}" )



'''
without prefilling and postfilling, answer will be like this: 

'Here are 3 short AWS CLI commands:\n\n1. **List S3 buckets:**\n```\naws s3 ls\n```\n\n2. **Describe EC2 instances:**\n```\naws ec2 describe-instances\n```\n\n3. **Get caller identity:**\n```\naws sts get-caller-identity\n```

'''