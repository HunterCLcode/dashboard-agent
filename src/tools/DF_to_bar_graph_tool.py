import logging
from typing import Type
from pydantic import BaseModel, Field

#import plotly.express as px
import pandas as pd
import tempfile
import os

class DFToPlotlyBarInput(BaseModel):
    df_list: list = Field(..., description="A list of dictionaries representing the DataFrame rows. Each dictionary should have keys for x and y axes.")
    x_column_name: str = Field(..., description="The column name to use for the x-axis.")
    y_column_name: str = Field(..., description="The column name to use for the y-axis.")
    title: str = Field("", description="Title for the bar graph.")

class DFToPlotlyBarTool():
    name: str = "DataFrame to Plotly Bar Graph Tool"
    description: str = (
        "A tool to create a Plotly bar graph from a DataFrame-like list of dictionaries. Specify the x and y columns and an optional title."
    )
    args_schema: Type[BaseModel] = DFToPlotlyBarInput

    def _run(self, df_list: list, x_column_name: str, y_column_name: str, title: str = "") -> str:
        try:
            df = pd.DataFrame(df_list)
            #fig = px.bar(df, x=x_column_name, y=y_column_name, title=title)
            logging.info("Plotly bar graph created successfully.")
            image_path = ""
            #fig.write_image(image_path)
            
            return image_path  # Return the file path for gr.Image
        except Exception as e:
            logging.error(f"Error creating Plotly bar graph: {e}")
            return f"Error creating Plotly bar graph: {e}"