from pydantic import BaseModel, Field

class ReflectArgs(BaseModel):
    message: str = Field(..., description="A message to reflect back.")

def reflect(args: ReflectArgs) -> str:
    """Returns whatever message you pass in."""
    return args.message