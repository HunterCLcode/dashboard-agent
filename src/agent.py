from pocketflow import Node, Flow
from services.llm_services import get_response

class basicLLM(Node):
    def prep(self, shared):
        return shared["query"]
    
    def exec(self, query):
        return get_response(query)
    
    def post(self, shared, prep_res, exec_res):
        shared["response"] = exec_res
        print(exec_res)

basic = basicLLM()
flow = Flow(start=basic)
flow.run({"query":input("Say something: ")})

