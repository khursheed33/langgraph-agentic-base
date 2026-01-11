"""File system operation tools."""

from pathlib import Path
from typing import Optional, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from app.utils.agent_utils import resolve_output_path
from app.utils.logger import logger


class ReadFileInput(BaseModel):
    """Input for read file tool."""

    file_path: str = Field(..., description="Path to the file to read")


class WriteFileInput(BaseModel):
    """Input for write file tool."""

    file_path: str = Field(..., description="Path to the file to write. Relative paths are automatically resolved within the output directory.")
    content: str = Field(..., description="Content to write to the file")
    create_dirs: bool = Field(
        default=True, description="Create parent directories if they don't exist"
    )
    use_output_dir: bool = Field(
        default=True, description="Resolve relative paths within the output directory. Set to false for absolute paths."
    )


class FileExistsInput(BaseModel):
    """Input for file exists tool."""

    file_path: str = Field(..., description="Path to check")


class ReadFileTool(BaseTool):
    """Tool for reading files."""

    name: str = "read_file"
    description: str = (
        "Read the contents of a file from the file system. "
        "Returns the file content as a string."
    )
    args_schema: Type[BaseModel] = ReadFileInput

    def _run(self, file_path: str) -> str:
        """Read file contents."""
        try:
            path = Path(file_path)
            if not path.exists():
                logger.warning(f"File not found: {file_path}")
                return f"Error: File not found at {file_path}"
            
            content = path.read_text(encoding="utf-8")
            logger.info(f"Read file: {file_path} ({len(content)} characters)")
            return content
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return f"Error reading file: {str(e)}"


class WriteFileTool(BaseTool):
    """Tool for writing files."""

    name: str = "write_file"
    description: str = (
        "Write content to a file. Creates parent directories if needed. "
        "Returns success message or error."
    )
    args_schema: Type[BaseModel] = WriteFileInput

    def _run(
        self, file_path: str, content: str, create_dirs: bool = True, use_output_dir: bool = True
    ) -> str:
        """Write content to file."""
        try:
            # Resolve the file path
            if use_output_dir:
                path = resolve_output_path(file_path)
            else:
                path = Path(file_path)

            if create_dirs:
                path.parent.mkdir(parents=True, exist_ok=True)

            path.write_text(content, encoding="utf-8")
            logger.info(f"Wrote file: {path} ({len(content)} characters)")
            return f"Successfully wrote {len(content)} characters to {path}"
        except Exception as e:
            logger.error(f"Error writing file {file_path}: {e}")
            return f"Error writing file: {str(e)}"


class FileExistsTool(BaseTool):
    """Tool for checking if file exists."""

    name: str = "file_exists"
    description: str = (
        "Check if a file or directory exists at the given path. "
        "Returns True if exists, False otherwise."
    )
    args_schema: Type[BaseModel] = FileExistsInput

    def _run(self, file_path: str) -> str:
        """Check if file exists."""
        try:
            path = Path(file_path)
            exists = path.exists()
            logger.info(f"Checked file existence: {file_path} = {exists}")
            return f"File exists: {exists}"
        except Exception as e:
            logger.error(f"Error checking file existence {file_path}: {e}")
            return f"Error: {str(e)}"


# Export tool instances
read_file_tool = ReadFileTool()
write_file_tool = WriteFileTool()
file_exists_tool = FileExistsTool()

