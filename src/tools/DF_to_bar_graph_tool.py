import logging
from pydantic import BaseModel, Field
import tempfile, os
import plotly.express as px
import pandas as pd

class DFToPlotlyBarArgs(BaseModel):
    df_list: list = Field(..., description="A list of dictionaries representing the DataFrame rows. Each dictionary should have keys for x and y axes.")
    x_column_name: str = Field(..., description="The column name to use for the x-axis.")
    y_column_name: str = Field(..., description="The column name to use for the y-axis.")
    title: str = Field("", description="Title for the bar graph.")

def DFToPlotlyBarTool(args: DFToPlotlyBarArgs) -> str:
    """Graphing tool that uses plotly"""
    try:
        df = pd.DataFrame(args.df_list)
        fig = px.bar(df, x=args.x_column_name, y=args.y_column_name, title=args.title)
        logging.info("Plotly bar graph created successfully.")
        image_path = os.path.join(tempfile.gettempdir(), "bar_chart.png")
        fig.write_image(image_path)
        
        return image_path  # Return the file path for gr.Image
    except Exception as e:
        logging.error(f"Error creating Plotly bar graph: {e}")
        return f"Error creating Plotly bar graph: {e}"