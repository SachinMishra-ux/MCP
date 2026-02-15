from typing import List
import os
#from mcp.server.fastmcp import FastMCP
from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("filesystem")

@mcp.tool()
def list_directory(path: str) -> str:
    """
    List files and directories at the specified path.
    
    Args:
        path: The absolute path to list contents of.
    """
    if not os.path.isabs(path):
        return "Error: Path must be absolute."
    
    if not os.path.exists(path):
        return f"Error: Path '{path}' does not exist."
        
    try:
        items = os.listdir(path)
        return "\n".join(items)
    except Exception as e:
        return f"Error listing directory: {str(e)}"

@mcp.tool()
def read_file(path: str) -> str:
    """
    Read the contents of a file at the specified path.
    
    Args:
        path: The absolute path of the file to read.
    """
    if not os.path.isabs(path):
        return "Error: Path must be absolute."
        
    if not os.path.exists(path):
        return f"Error: Path '{path}' does not exist."
    
    if not os.path.isfile(path):
        return f"Error: '{path}' is not a file."
        
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

if __name__ == "__main__":
    mcp.run()
