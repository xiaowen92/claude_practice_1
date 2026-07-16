'''
Prefilling 是什么
在 API call 之前，手动往 messages 里加一条 assistant 消息，让模型"假装自己已经开始回复了"，从而延续特定格式。


add_assistant_message(messages, "```bash")  # 强制模型从 bash code block 开始
response = chat_log(messages, stop_sequences=["```"])  # 遇到结束符停止
效果：拿到干净的结构化内容，不含多余的解释文字。

为什么 4.6 起被移除
Extended thinking 架构冲突（主要原因）— 4.6 引入了 extended thinking，模型需要先内部推理再回答。Prefilling 跳过了这个阶段，两者不兼容。
安全隐患 — 可以 prefill "Sure, here's how to..." 来绕过模型的拒绝回答机制。
替代方案成熟 — 4.6+ 指令遵循能力更强，不需要 prefilling 就能稳定控制输出格式。
4.6+ 如何替代 Prefilling
场景	替代方案	示例
控制输出格式	直接 prompt 指令	"Return ONLY raw JSON, no markdown"
引导回复风格	Few-shot example	在 messages 里加一轮示范对话
结构化数据提取	Tool use	定义 schema，Claude 直接填值
去除 markdown 包装	Post-processing	re.sub(r'```.*?```', ...)
Few-shot 是最直接的等效替代，通过示范对话告诉模型期望的输出风格：


messages = [
    {"role": "user", "content": "generate 2 aws cli commands"},
    {"role": "assistant", "content": "aws s3 ls\naws sts get-caller-identity"},  # 示范格式
    {"role": "user", "content": "your actual prompt here"}
]
生产环境推荐 tool use — 不只是格式控制，而是从根本上保证输出结构合法。

方案 3：Tool use（最可靠，生产推荐）

用 tool 定义输出 schema，Claude 直接填值，完全不会有多余文字：


tools = [{
    "name": "output_rule",
    "description": "Output the EventBridge rule",
    "input_schema": {
        "type": "object",
        "properties": {
            "source": {"type": "array", "items": {"type": "string"}},
            "detail-type": {"type": "array", "items": {"type": "string"}}
        }
    }
}]

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1000,
    tools=tools,
    tool_choice={"type": "tool", "name": "output_rule"},
    messages=[{"role": "user", "content": "Generate a very short EventBridge rule"}]
)

clean_json = response.content[0].input  # 直接拿到 dict，不需要解析
'''

from dotenv import load_dotenv
load_dotenv()

import httpx
from anthropic import Anthropic

client = Anthropic(http_client=httpx.Client(verify=False))

model = "claude-sonnet-4-5-20250929"

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

add_assistant_message(messages=messages1, content='Here are all 3 commands in a single blocks without comments : \n ```bash')

response2 = chat_log(messages=messages1, system=system, stop_sequences = ['```'])
response2 = response2.strip()

print(f"response currently is \n {response2}" )



'''
without prefilling and postfilling, answer will be like this: 

'Here are 3 short AWS CLI commands:\n\n1. **List S3 buckets:**\n```\naws s3 ls\n```\n\n2. **Describe EC2 instances:**\n```\naws ec2 describe-instances\n```\n\n3. **Get caller identity:**\n```\naws sts get-caller-identity\n```

'''