import asyncio
import logging
from enum import Enum
from pocketflow import Node, Flow
from pydantic import BaseModel, Field
from types import SimpleNamespace
from mcp.types import Tool
from services.mcp_adapter import MCPClient
from services.llm_services import get_response, get_response_structured
from prompts import DECIDE_NODE_PROMPT, RESPONSE_NODE_PROMPT

def build_action_model(tools: list[Tool]):
    Action = Enum("Action", {t.name: t.name for t in tools}, type=str)

    class AgentAction(BaseModel):
        action: Action
        reasoning : str = Field("", description="Short reason why you chose this route, should be 1-2 sentences")
        #args: dict= Field({}, description= "Arugments for chosen tool")

    return AgentAction

class decideAction(Node):
    def prep(self, shared):
        return {"input": shared["input"], "tool_context": shared["tool_context"], "scratchpad": shared["scratchpad"], "history": shared["history"]}
    
    def exec(self, prep_res):
        prompt = DECIDE_NODE_PROMPT.format(TOOLS=prep_res["tool_context"]["tools_str"], CONTEXT=str(prep_res["tool_context"]), HISTORY=str(prep_res["history"]), SCRATCHPAD=prep_res["scratchpad"])
        return get_response_structured(prompt, prep_res["tool_context"]["action_model"])
    
    def post(self, shared, prep_res, exec_res):
        shared["response"] = exec_res
        if not hasattr(exec_res, "action") or not "scratchpad" in shared:
            return "Error: Attribute error during decision node"
        shared["scratchpad"].append(f"Decision Node Route: [{exec_res.action}] Reason: [{exec_res.reasoning}]")
        if exec_res.action.value == "respond":
            return "respond"
        return "execute"

class responseAction(Node):
    def prep(self, shared):
        return {"context": shared["input"], "scratchpad": shared["scratchpad"], "history": shared["history"]}
    
    def exec(self, prep_res):
        prompt = RESPONSE_NODE_PROMPT.format(CONTEXT=str(prep_res["context"]), SCRATCHPAD=str(prep_res["scratchpad"]), HISTORY=str(prep_res["history"]))
        return get_response(prompt)
    
    def post(self, shared, prep_res, exec_res):
        return exec_res

class executeTool(Node):
    def prep(self, shared):
        return {
          **shared["tool_context"],
          "action": shared["response"].action,
          "args": {}
      }
    
    def exec(self, prep_res):
        future = asyncio.run_coroutine_threadsafe(
            prep_res["client"].call_tool(prep_res["action"].value, prep_res["args"]),
            prep_res["loop"]
        )
        return future.result(timeout=30)
    
    def post(self, shared, prep_res, exec_res):
        shared["scratchpad"].append(f"Tool executed: [{shared['response'].action.value}] Output: [{exec_res}]")
        return "default"

class SQLAgent():
    def __init__(self, tools: list[Tool], client, loop):
        all_tools = (tools +
                     [SimpleNamespace(name="respond", description="Use when you have enough information to answer the user")])

        self.tool_context = {
            "tools": all_tools,
            "action_model": build_action_model(all_tools),
            "tools_str": "\n".join(f"- {t.name}: {t.description}" for t in tools),
            "client": client,
            "loop": loop
        }

        # Nodes
        self.decide = decideAction()
        self.respond = responseAction()
        self.execute = executeTool()

        # Node connections
        self.decide - "respond" >> self.respond
        self.decide - "execute" >> self.execute
        self.execute >> self.decide

        # Flow
        self.flow = Flow(start=self.decide)

    def run(self, query: str, history: list):
        res = self.flow.run({"input": query, "history": history, "scratchpad": [], "tool_context": self.tool_context})
        return res

async def main():
    async with MCPClient() as client:
        loop = asyncio.get_event_loop()
        tools = await client.get_tools()
        agent = SQLAgent(tools, client, loop)
        history = []

        while True:
            query = await loop.run_in_executor(None, input, "\nWhat would you like to ask: ")
            if query in ("q", "quit"): break
            result = await loop.run_in_executor(None, agent.run, query, history)
            print('\nOutput: ' + result)
            history.append({"role": "user", "message": query})
            history.append({"role": "agent", "message": result})

asyncio.run(main())