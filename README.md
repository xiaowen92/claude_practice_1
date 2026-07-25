# repo for learning progress in Claude Code official tuition with exercise

Claude code in Action  & Building with the Calude API 

Overall tricks & tips learning are recored here: 
https://workflowy.com/#/3e82b2953e17

# Tips learning from the course

1. even you set the max token limit, llm will not gen based on that, only be truncated by that
2. claude has no memory of any past converations, in other words it cannot store any context
3. We can use system prompt system = ' predefined role for llm" to regulate the llm behaviour, for example system = "You are a helpful computer science professor especially in python structure" 
4. Temperature (0-1): Controls output variance; lower values force convergent, analytical outputs (ideal for coding or data analysis), whereas higher values produce divergent, creative responses.
5. we can using client.message.stream to stream the answer, which is event controlled
## Tip 6 Prefill + Stop Sequence
Prefilling 是什么
在 API call 之前，手动往 messages 里加一条 assistant 消息，让模型"假装自己已经开始回复了"，从而延续特定格式。

add_assistant_message(messages, "```bash")  # 强制模型从 bash code block 开始
response = chat_log(messages, stop_sequences=["```"])  # 遇到结束符停止
效果：拿到干净的结构化内容，不含多余的解释文字。


#  Tips Learning pytest
1.  Exception must be triggered in test phase, not in importing phase. in other words, you have func A, and test_A, you need to make sure A cannot throw error while importing it. for example, you cannot have 1/0 like this will throw zero division error. 

# Tips learning python








