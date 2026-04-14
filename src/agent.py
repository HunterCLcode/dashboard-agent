import asyncio
from enum import Enum
from pocketflow import Node, Flow
from pydantic import BaseModel, Field
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from services.llm_services import get_response, get_response_structured
from prompts import DECIDE_NODE_PROMPT, RESPONSE_NODE_PROMPT

# SERVER = StdioServerParameters(
#     command="python",
#     args=["-m", "etl.mcp_server"],
#     cwd="C:/Users/Hunter Lee/Documents/HunterCode/dashboard-agent-etl",
# )

# async def main():
#     async with stdio_client(SERVER) as (read, write):
#         async with ClientSession(read, write) as session:
#             await session.initialize()
#             result = await session.list_tools()
#             for tool in result.tools:
#                 print(tool.name)
#                 print(tool.description)
#                 print()

# asyncio.run(main()) 

decisions = ["get_schema", "generate_sql", "execute_sql", "respond"]

Action = Enum("Action", {d: d for d in decisions}, type=str)

class AgentAction(BaseModel):
    action: Action
    reasoning : str = Field("", description="Short reason why you chose this route, should be 1-2 sentences")

class decideAction(Node):
    def prep(self, shared):
        return shared["input"]
    
    def exec(self, prep_res):
        prompt = DECIDE_NODE_PROMPT.format(TOOLS=str(decisions), CONTEXT=str(prep_res), HISTORY="")
        return get_response_structured(prompt, AgentAction)
    
    def post(self, shared, prep_res, exec_res):
        shared["response"] = exec_res
        if not hasattr(exec_res, "action") or not "scratchpad" in shared:
            return "Error: Attribute error during decision node"
        shared["scratchpad"].append(f"Decision Node Route: [{exec_res.action}] Reason: [{exec_res.reasoning}]")
        if hasattr(exec_res, "action") and exec_res.action == Action.respond:
            return "respond"
        return ""

class responseAction(Node):
    def prep(self, shared):
        return {"context": shared["input"], "scratchpad": shared["scratchpad"]}
    
    def exec(self, prep_res):
        print("PREP: ", str(prep_res))
        prompt = RESPONSE_NODE_PROMPT.format(CONTEXT=str(prep_res["context"]), SCRATCHPAD=str("scratchpad"), HISTORY="")
        return get_response(prompt)
    
    def post(self, shared, prep_res, exec_res):
        return exec_res

decide = decideAction()
respond = responseAction()

decide - "respond" >> respond

flow = Flow(start=decide)
res = flow.run({"input":input("Say something: "), "scratchpad": []})
print(res)