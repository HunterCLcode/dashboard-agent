import asyncio
import logging
import json
from enum import Enum
from pocketflow import Node, Flow
from pydantic import BaseModel, Field, ConfigDict
from types import SimpleNamespace
from mcp.types import Tool
from services.mcp_adapter import MCPClient
from services.llm_services import get_response, get_response_structured
from prompts import DECIDE_NODE_PROMPT, RESPONSE_NODE_PROMPT
from tools import LOCAL_TOOLS

def build_action_model(tools: list[Tool]):
    """ Builds the decideNode's action args """
    Action = Enum("Action", {t.name: t.name for t in tools}, type=str)

    class AgentAction(BaseModel):
        action: Action
        reasoning : str = Field("", description="Short reason why you chose this route, should be 1-2 sentences")
        args: str = Field("", description="JSON encoded arguments for the chosen tool e.g. '{\"query\": \"SELECT ...\"}' ")
    return AgentAction

class decideAction(Node):
    """ Node responsible for deciding to use which tool or to respond to the user """
    def prep(self, shared):
        return {"input": shared["input"], "tool_context": shared["tool_context"], "scratchpad": shared["scratchpad"], "history": shared["history"]}
    
    def exec(self, prep_res):
        prompt = DECIDE_NODE_PROMPT.format(TOOLS=prep_res["tool_context"]["tools_str"], CONTEXT=str(prep_res["input"]), HISTORY=str(prep_res["history"]), SCRATCHPAD=prep_res["scratchpad"])
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
    """ Node responsible for gathering context from tools/query and constructing final response """

    def prep(self, shared):
        return {"context": shared["input"], "scratchpad": shared["scratchpad"], "history": shared["history"]}
    
    def exec(self, prep_res):
        prompt = RESPONSE_NODE_PROMPT.format(CONTEXT=str(prep_res["context"]), SCRATCHPAD=str(prep_res["scratchpad"]), HISTORY=str(prep_res["history"]))
        return get_response(prompt)
    
    def post(self, shared, prep_res, exec_res):
        result = {"summary": exec_res}
        if "chart" in shared:
            result.update(shared["chart"])
        shared["result"] = result
        return None

class executeTool(Node):
    """ Node responsible for gathering tool and args and executing it """
    def prep(self, shared):
        raw_args = shared["response"].args
        return {
            **shared["tool_context"],
            "action": shared["response"].action,
            "args": json.loads(raw_args) if raw_args else {}
        }
    
    def exec(self, prep_res):
        action_name = prep_res["action"].value
        local_fns = prep_res.get("local_fns", {})

        if action_name in local_fns:
            tool = local_fns[action_name]
            parsed = tool["args_model"](**prep_res["args"])
            return tool["fn"](parsed)
        else:
            future = asyncio.run_coroutine_threadsafe(
            prep_res["client"].call_tool(action_name, prep_res["args"]),
            prep_res["loop"]
        )
        return future.result(timeout=30)
        
    def post(self, shared, prep_res, exec_res):
        try:
            parsed = json.loads(exec_res)
            if "chart_type" in parsed:
                shared["chart"] = parsed
        except (json.JSONDecodeError, TypeError):
            pass
        shared["scratchpad"].append(f"Tool executed: [{shared['response'].action.value}] Output: [{exec_res}]")
        return "default"

class SQLAgent():
    def __init__(self, tools: list[Tool], client, loop):
        local_ns = [
            SimpleNamespace(
                name=t["name"],
                description=t["description"],
                inputSchema=t["args_model"].model_json_schema()  # derived here
            )
            for t in LOCAL_TOOLS
        ]
        local_fns = {t["name"]: t for t in LOCAL_TOOLS}
        all_tools = (tools +
                     local_ns +
                     [SimpleNamespace(name="respond", description="Use when you have enough information to answer the user")])

        def _format_tool(t) -> str:
            line = f"- {t.name}: {t.description}"
            if hasattr(t, "inputSchema") and t.inputSchema:
                props = t.inputSchema.get("properties", {})
                required = t.inputSchema.get("required", [])
                if props:
                    args = ", ".join(
                        f"{k}: {v.get('type', 'any')} ({'required' if k in required else 'optional'}) — {v.get('description', '')}"
                        for k, v in props.items()
                    )
                    line += f" | args: {{{args}}}"
            return line

        self.tool_context = {
            "tools": all_tools,
            "local_fns" : local_fns,
            "action_model": build_action_model(all_tools),
            "tools_str": "\n".join(_format_tool(t) for t in all_tools),
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
      shared = {"input": query, "history": history, "scratchpad": [], "tool_context": self.tool_context}
      self.flow.run(shared)
      return shared.get("result")

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
            print('\nOutput: ' + result["summary"])
            history.append({"role": "user", "message": query})
            history.append({"role": "agent", "message": result})

asyncio.run(main())