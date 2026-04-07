from pocketflow import Node, Flow
from pydantic import BaseModel
from services.llm_services import get_response, get_response_structured
from prompts import DECIDE_NODE_PROMPT
from enum import Enum

decisions = ["get_schema", "generate_sql", "execute_sql", "respond"]

Action = Enum("Action", {d: d for d in decisions}, type=str)

class AgentAction(BaseModel):
    action: Action

class decideAction(Node):
    def prep(self, shared):
        return shared["context"]
    
    def exec(self, prep_res):
        prompt = DECIDE_NODE_PROMPT.format(TOOLS=str(decisions), CONTEXT=str(prep_res))
        return get_response_structured(prompt, AgentAction)
    
    def post(self, shared, prep_res, exec_res):
        shared["response"] = exec_res
        if hasattr(exec_res, "action") and exec_res.action == Action.respond:
            return "respond"

class responseAction(Node):
    def prep(self, shared):
        print("hi")
        return shared["response"]

decide = decideAction()
respond = responseAction()

decide - "respond" >> respond

flow = Flow(start=decide)
flow.run({"context":input("Say something: ")})
#print(Action.respond == "respond")