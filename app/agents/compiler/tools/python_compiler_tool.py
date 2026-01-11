"""Python compiler tools."""

import py_compile
import sys
from pathlib import Path
from typing import Optional, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from app.utils.agent_utils import resolve_output_path
from app.utils.logger import logger


class PythonCompileInput(BaseModel):
    """Input for Python compiler tool."""

    path: str = Field(..., description="Path to a Python file or directory containing Python files to compile")
    recursive: bool = Field(
        default=True,
        description="If path is a directory, whether to compile files in subdirectories recursively"
    )
    output_filename: Optional[str] = Field(
        default=None,
        description="Optional custom filename for the compilation summary. If not provided, will use a summary name based on the input path."
    )


class PythonCompilerTool(BaseTool):
    """Tool for compiling Python files and generating compilation summaries."""

    name: str = "compile_python"
    description: str = (
        "Compile Python file(s) from a given path and generate a comprehensive compilation summary. "
        "Can compile single files or all Python files in a directory (recursively). "
        "The summary includes compilation status for each file, any errors found, and metadata. "
        "Summary is saved to the output/compilation directory."
    )
    args_schema: Type[BaseModel] = PythonCompileInput

    def _run(self, path: str, recursive: bool = True, output_filename: Optional[str] = None) -> str:
        """Compile Python file(s) and generate summary."""
        try:
            logger.info(f"Compiler tool called with path: {path}")

            # Resolve the path - if relative, look in output directory
            if not Path(path).is_absolute():
                source_path = resolve_output_path(path)
                logger.info(f"Resolved relative path '{path}' to: {source_path}")
            else:
                source_path = Path(path)
                logger.info(f"Using absolute path: {source_path}")

            # Check if source path exists
            if not source_path.exists():
                # Try alternative locations
                alternatives = [
                    Path("output") / path,  # Direct output path
                    Path(path),  # Current directory
                    resolve_output_path(path),  # Try resolve again
                ]

                for alt_path in alternatives:
                    if alt_path.exists():
                        logger.info(f"Found file at alternative path: {alt_path}")
                        source_path = alt_path
                        break
                else:
                    # None of the alternatives exist
                    logger.error(f"Path {source_path} does not exist. Tried alternatives: {alternatives}")
                    error_msg = f"Error: File not found at {source_path} or alternative locations"
                    logger.error(error_msg)
                    return error_msg

            # Collect all Python files to compile
            python_files = []
            if source_path.is_file():
                if source_path.suffix.lower() == '.py':
                    python_files = [source_path]
                else:
                    error_msg = f"Error: {source_path} is not a Python file (.py extension required)"
                    logger.error(error_msg)
                    return error_msg
            elif source_path.is_dir():
                if recursive:
                    python_files = list(source_path.rglob("*.py"))
                else:
                    python_files = list(source_path.glob("*.py"))

                if not python_files:
                    return f"No Python files found in {source_path}"

                logger.info(f"Found {len(python_files)} Python files to compile in {source_path}")
            else:
                error_msg = f"Error: {source_path} is neither a file nor a directory"
                logger.error(error_msg)
                return error_msg

            # Compile all Python files
            compilation_results = []
            total_files = len(python_files)
            successful_compilations = 0

            for file_path in python_files:
                logger.info(f"Starting compilation of Python file: {file_path}")

                file_errors = []
                file_successful = False

                try:
                    # Use py_compile to compile the file
                    py_compile.compile(
                        str(file_path),
                        doraise=True  # Raise exceptions on compilation errors
                    )
                    file_successful = True
                    successful_compilations += 1
                    logger.info(f"Successfully compiled Python file: {file_path}")

                except py_compile.PyCompileError as e:
                    file_errors.append(f"Compilation error: {str(e)}")
                    logger.warning(f"Compilation failed for {file_path}: {str(e)}")

                except SyntaxError as e:
                    file_errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
                    if e.text:
                        file_errors.append(f"  {e.text.rstrip()}")
                    logger.warning(f"Syntax error in {file_path}: {e}")

                except Exception as e:
                    file_errors.append(f"Unexpected compilation error: {str(e)}")
                    logger.error(f"Unexpected error compiling {file_path}: {e}")

                compilation_results.append({
                    'file': file_path,
                    'successful': file_successful,
                    'errors': file_errors
                })

            # Generate compilation summary
            summary_lines = []
            summary_lines.append("# Python Compilation Summary")
            summary_lines.append("")
            summary_lines.append(f"**Source Path:** {source_path}")
            summary_lines.append(f"**Total Files Processed:** {total_files}")
            summary_lines.append(f"**Successful Compilations:** {successful_compilations}")
            summary_lines.append(f"**Failed Compilations:** {total_files - successful_compilations}")
            summary_lines.append(f"**Compilation Time:** {Path(__file__).stat().st_mtime}")  # Using file mtime as timestamp
            summary_lines.append(f"**Python Version:** {sys.version}")
            summary_lines.append("")

            if successful_compilations == total_files:
                summary_lines.append("## ✅ Overall Compilation Status: SUCCESS")
                summary_lines.append("")
                summary_lines.append("All Python files compiled successfully without errors.")
            elif successful_compilations > 0:
                summary_lines.append("## ⚠️  Overall Compilation Status: PARTIAL SUCCESS")
                summary_lines.append("")
                summary_lines.append(f"{successful_compilations} out of {total_files} files compiled successfully.")
            else:
                summary_lines.append("## ❌ Overall Compilation Status: FAILED")
                summary_lines.append("")
                summary_lines.append("None of the Python files compiled successfully.")

            # File-by-file results
            summary_lines.append("")
            summary_lines.append("## File Compilation Results")
            summary_lines.append("")

            for result in compilation_results:
                file_path = result['file']
                successful = result['successful']
                errors = result['errors']

                relative_path = file_path.relative_to(source_path) if source_path.is_dir() else file_path.name
                status = "✅ SUCCESS" if successful else "❌ FAILED"
                summary_lines.append(f"### {relative_path} - {status}")

                if not successful and errors:
                    summary_lines.append("")
                    for error in errors:
                        summary_lines.append(f"- {error}")
                summary_lines.append("")

            # Additional metadata
            summary_lines.append("## Additional Information")
            summary_lines.append("")
            summary_lines.append(f"- **Compiled by:** Python Compiler Agent")
            summary_lines.append(f"- **Compilation Method:** py_compile module")
            summary_lines.append(f"- **Recursive Compilation:** {'Yes' if recursive and source_path.is_dir() else 'No'}")

            # Try to get some basic statistics across all files
            total_lines = 0
            total_functions = 0
            total_classes = 0
            total_imports = 0

            for result in compilation_results:
                file_path = result['file']
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    lines = content.splitlines()
                    total_lines += len(lines)

                    # Count constructs
                    total_imports += content.count('import ') + content.count('from ')
                    total_functions += content.count('def ')
                    total_classes += content.count('class ')

                except Exception as e:
                    logger.warning(f"Could not analyze {file_path}: {e}")

            if total_lines > 0:
                summary_lines.append(f"- **Total Lines Across All Files:** {total_lines}")
                summary_lines.append(f"- **Total Import Statements:** {total_imports}")
                summary_lines.append(f"- **Total Function Definitions:** {total_functions}")
                summary_lines.append(f"- **Total Class Definitions:** {total_classes}")
            else:
                summary_lines.append("- **Code Analysis:** Could not analyze file contents")

            # Create output directory if it doesn't exist
            compilation_dir = resolve_output_path("compilation")
            compilation_dir.mkdir(parents=True, exist_ok=True)

            # Generate output filename
            if output_filename:
                output_name = output_filename
            else:
                # Use source filename with compilation suffix
                base_name = source_path.stem
                output_name = f"{base_name}_compilation.md"

            # Ensure .md extension
            if not output_name.endswith('.md'):
                output_name += '.md'

            # Save summary to file
            output_path = compilation_dir / output_name
            summary_content = '\n'.join(summary_lines)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(summary_content)

            logger.info(f"Compilation summary saved to: {output_path}")

            # Return result
            status = "successful" if successful_compilations == total_files else "failed"
            return f"Python compilation {status}. Summary saved to {output_path}"

        except Exception as e:
            error_msg = f"Error during Python compilation process: {str(e)}"
            logger.error(error_msg)
            return error_msg


# Export tool instance
python_compiler_tool = PythonCompilerTool()