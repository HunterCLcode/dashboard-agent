from .reflect_tool import reflect, ReflectArgs
from .DF_to_bar_graph_tool import DFToPlotlyBarTool, DFToPlotlyBarArgs

LOCAL_TOOLS = [
    {
        "name": "reflect",
        "description": reflect.__doc__,
        "args_model": ReflectArgs,
        "fn": reflect,
    },
    {
        "name": "dataframe to graph",
        "description": DFToPlotlyBarTool.__doc__,
        "args_model": DFToPlotlyBarArgs,
        "fn": DFToPlotlyBarTool,
    }
]