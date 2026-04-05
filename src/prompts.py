DECIDE_NODE_PROMPT = """
You are an expert data consultant. You will be given context of a user query.
Route to the correct tool or route to respond.

Here are the following tools:
{TOOLS}

User query:
{CONTEXT}

Give your response as JUST which tool you would use:"""