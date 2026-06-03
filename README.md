# repo for learning progress in Claude Code official tuition with exercise

Claude code in Action  & Building with the Calude API 

# Tips learning from the course

1. even you set the max token limit, llm will not gen based on that, only be truncated by that
2. claude has no memory of any past converations, in other words it cannot store any context
3. We can use system prompt system = ' predefined role for llm" to regulate the llm behaviour
4. Temperature (0-1): Controls output variance; lower values force convergent, analytical outputs (ideal for coding or data analysis), whereas higher values produce divergent, creative responses.

# Tips Learning pytest
1.  Exception must be triggered in test phase, not in importing phase. in other words, you have func A, and test_A, you need to make sure A cannot throw error while importing it. for example, you cannot have 1/0 like this will throw zero division error. 









