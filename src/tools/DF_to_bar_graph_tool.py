import json
from pydantic import BaseModel, Field

class DFToPlotlyBarArgs(BaseModel):
    df_list: list = Field(..., description="A list of dictionaries representing the DataFrame rows. Each dictionary should have keys for x and y axes.")
    x_column_name: str = Field(..., description="The column name to use for the x-axis.")
    y_column_name: str = Field(..., description="The column name to use for the y-axis.")
    title: str = Field("", description="Title for the bar graph.")

def DFToBarTool(args: DFToPlotlyBarArgs) -> str:
    """Formats data as a bar chart response for the dashboard frontend."""
    return json.dumps({
        "chart_type": "bar",
        "data": args.df_list,
        "x_key": args.x_column_name,
        "y_key": args.y_column_name,
        "title": args.title
    })