import json
from pydantic import BaseModel, Field

class DFToBarArgs(BaseModel):
    df_list: list = Field(..., description="A list of dictionaries representing the DataFrame rows. Each dictionary should have keys for x and y axes.")
    x_column_name: str = Field(..., description="The column name to use for the x-axis.")
    y_column_name: str = Field(..., description="The column name to use for the y-axis.")
    title: str = Field("", description="Title for the bar graph.")

def DFToBarTool(args: DFToBarArgs) -> str:
    """
    DF to Bar Graph Tool
    
    This took takes in:
    - a list of dictionaries representing the DF rows, where each dictionary
    should have keys for both x and y axis.
    - column name for x-axis
    - column name for y-axis
    - graph title

    THEN it will return in JSON formatting which will attach the graph to your
    response. This means all you have to do is call this tool, and then respond to the user
    """
    return json.dumps({
        "chart_type": "bar",
        "data": args.df_list,
        "x_key": args.x_column_name,
        "y_key": args.y_column_name,
        "title": args.title
    })