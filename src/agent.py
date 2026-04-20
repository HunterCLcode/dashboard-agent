import asyncio
import logging
from enum import Enum
from pocketflow import Node, Flow
from pydantic import BaseModel, Field
from mcp.types import Tool
from services.mcp_adapter import MCPClient
from services.llm_services import get_response, get_response_structured
from prompts import DECIDE_NODE_PROMPT, RESPONSE_NODE_PROMPT

def build_action_model(tools: list[Tool]):
    print(tools)
    Action = Enum("Action", {t.name: t.name for t in tools}, type=str)

    class AgentAction(BaseModel):
        action: Action
        reasoning : str = Field("", description="Short reason why you chose this route, should be 1-2 sentences")
        #args: dict= Field({}, description= "Arugments for chosen tool")

    return AgentAction

class decideAction(Node):
    def prep(self, shared):
        return {"input": shared["input"], "action_model": shared["action_model"], "tool_context": shared["tool_context"]}
    
    def exec(self, prep_res):
        prompt = DECIDE_NODE_PROMPT.format(TOOLS=prep_res["tool_context"], CONTEXT=str(prep_res), HISTORY="")
        return get_response_structured(prompt, prep_res["action_model"])
    
    def post(self, shared, prep_res, exec_res):
        print("SHARED:", shared)
        print("RESPONSE:", exec_res)
        shared["response"] = exec_res
        if not hasattr(exec_res, "action") or not "scratchpad" in shared:
            return "Error: Attribute error during decision node"
        shared["scratchpad"].append(f"Decision Node Route: [{exec_res.action}] Reason: [{exec_res.reasoning}]")
        # if hasattr(exec_res, "action") and exec_res.action == shared["action_model"].respond:
        #     return "respond"
        return ""

class responseAction(Node):
    def prep(self, shared):
        return {"context": shared["input"], "scratchpad": shared["scratchpad"]}
    
    def exec(self, prep_res):
        prompt = RESPONSE_NODE_PROMPT.format(CONTEXT=str(prep_res["context"]), SCRATCHPAD=str("scratchpad"), HISTORY="")
        return get_response(prompt)
    
    def post(self, shared, prep_res, exec_res):
        return exec_res

class SQLAgent():
    def __init__(self, tools: list[Tool]):
        self.action_model = build_action_model(tools)
        self.tool_context = "\n".join(f"- {t.name}: {t.description}" for t in tools)

        # Nodes
        self.decide = decideAction()
        self.respond = responseAction()

        # Node connections
        self.decide - "respond" >> self.respond

        # Flow
        self.flow = Flow(start=self.decide)

    def run(self, query: str):
        res = self.flow.run({"input": query, "scratchpad": [], "action_model": self.action_model, "tool_context": self.tool_context})
        return res

async def main():
    async with MCPClient() as client:
        # get tools
        tools = await client.get_tools()
        agent = SQLAgent(tools)
        for t in tools:
            print(t.name, t.description)

        # call a tool
        result = await client.call_tool("get_schema", {})
        print("tool call: ", result)

        while True:
            print('\n' + '=' * 100 + '\n')
            query = input("What would you like to ask (reply \"quit\" to exit): ")

            if query == "q" or query == "quit": break
            
            print('\nOutput: ' + agent.run(query))

asyncio.run(main())