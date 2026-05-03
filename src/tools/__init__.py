from .reflect_tool import reflect, ReflectArgs

LOCAL_TOOLS = [
    {
        "name": "reflect",
        "description": reflect.__doc__,
        "input_schema": ReflectArgs.model_json_schema(),
        "fn": reflect,
    }
]