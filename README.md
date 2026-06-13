# repo for learning progress in Claude Code official tuition with exercise

Claude code in Action  & Building with the Calude API 

# Tips learning from the course

1. even you set the max token limit, llm will not gen based on that, only be truncated by that
2. claude has no memory of any past converations, in other words it cannot store any context
3. We can use system prompt system = ' predefined role for llm" to regulate the llm behaviour, for example system = "You are a helpful computer science professor especially in python structure" 
4. Temperature (0-1): Controls output variance; lower values force convergent, analytical outputs (ideal for coding or data analysis), whereas higher values produce divergent, creative responses.
5. we can using client.message.stream to stream the answer, which is event controlled
## Tip 6 Prefill + Stop Sequence
    When to use: When the LLM output needs to be directly parsed by code (APIs, config generation, batch data).

    Two-part combo:

    add_assistant_message(messages, "<opening marker>") — fake that the LLM already started speaking
    stop_sequences=["<closing marker>"] — hit the brakes the moment it tries to close
    Example: Generate CSV with the LLM
    Without the trick (dirty output, can't parse directly):


    Sure, here's the employee data you requested:
    ```csv
    name,age
    wen,30
    Hope this helps!

    **With the trick**:
    ```python
    add_user_message(messages, "Generate 2 rows of employee CSV")
    add_assistant_message(messages, "```csv\n")
    text = chat(messages, stop_sequences=["```"])
    Output (clean — pandas.read_csv eats it directly):

    name,age
    wen,30
    alice,25


#  Tips Learning pytest
1.  Exception must be triggered in test phase, not in importing phase. in other words, you have func A, and test_A, you need to make sure A cannot throw error while importing it. for example, you cannot have 1/0 like this will throw zero division error. 

# Tips learning python








