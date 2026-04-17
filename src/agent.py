import asyncio
from enum import Enum
from pocketflow import Node, Flow
from pydantic import BaseModel, Field
from services.mcp_adapter import MCPClient
from services.llm_services import get_response, get_response_structured
from prompts import DECIDE_NODE_PROMPT, RESPONSE_NODE_PROMPT

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

class SQLAgent():
    def __init__(self):
        # Nodes
        self.decide = decideAction()
        self.respond = responseAction()

        # Node connections
        self.decide - "respond" >> self.respond

        # Flow
        self.flow = Flow(start=self.decide)

    def run(self, query: str):
        res = self.flow.run({"input": query, "scratchpad": []})
        return res

async def main():
    agent = SQLAgent()

    async with MCPClient() as client:
        # get tools
        tools = await client.get_tools()
        for t in tools:
            print(t.name, t.description)

        # call a tool
        result = await client.call_tool("get_schema", {})
        print("tool call: ", result)

        print(agent.run(input("What would you like to ask: ")))

asyncio.run(main())