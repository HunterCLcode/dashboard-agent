from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = StdioServerParameters(
    command="python",
    args=["-m", "etl.mcp_server"],
    cwd="C:/Users/Hunter Lee/Documents/HunterCode/dashboard-agent-etl",
)

class MCPClient:
    async def __aenter__(self):
        self._stdio = stdio_client(SERVER)
        self._read, self._write = await self._stdio.__aenter__()
        self._session = ClientSession(self._read, self._write)
        await self._session.__aenter__()
        await self._session.initialize()
        return self

    async def __aexit__(self, *args):
        await self._session.__aexit__(*args)
        await self._stdio.__aexit__(*args)

    async def get_tools(self):
        result = await self._session.list_tools()
        return result.tools

    async def call_tool(self, name: str, args: dict) -> str:
        result = await self._session.call_tool(name, args)
        return result.content[0].text