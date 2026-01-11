"""Python code generation tools."""

import ast
import re
from pathlib import Path
from typing import Optional, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from app.utils.agent_utils import resolve_output_path
from app.utils.logger import logger


class PythonCodeGenerationInput(BaseModel):
    """Input for Python code generation tool."""

    requirements: str = Field(..., description="Requirements or description of the Python code to generate")
    include_docstring: bool = Field(
        default=True,
        description="Whether to include docstrings in the generated code"
    )
    include_imports: bool = Field(
        default=True,
        description="Whether to include necessary imports in the generated code"
    )


class PythonCodeGeneratorTool(BaseTool):
    """Tool for generating Python code based on requirements."""

    name: str = "generate_python_code"
    description: str = (
        "Generate Python code based on requirements and save it to a file. "
        "Creates well-structured, documented Python code with proper imports and error handling."
    )
    args_schema: Type[BaseModel] = PythonCodeGenerationInput

    def _run(
        self,
        requirements: str,
        include_docstring: bool = True,
        include_imports: bool = True
    ) -> str:
        """Generate Python code based on requirements."""
        try:
            logger.info(f"Generating Python code for requirements: {requirements[:100]}...")

            # Generate the Python code
            generated_code = self._generate_code_from_requirements(
                requirements, include_docstring, include_imports
            )

            # Validate the generated code
            validation_result = self._validate_python_code(generated_code)
            if not validation_result["valid"]:
                logger.warning(f"Generated code has validation issues: {validation_result['errors']}")

            # Prepare result message
            result_parts = []
            result_parts.append("Successfully generated Python code:")
            result_parts.append("")
            result_parts.append("```python")
            result_parts.append(generated_code)
            result_parts.append("```")
            result_parts.append("")
            result_parts.append(f"Code length: {len(generated_code)} characters")

            if validation_result["valid"]:
                result_parts.append("✅ Code validation: PASSED")
            else:
                result_parts.append("⚠️  Code validation: ISSUES FOUND")
                result_parts.append(f"Issues: {', '.join(validation_result['errors'])}")

            return "\n".join(result_parts)

        except Exception as e:
            error_msg = f"Error generating Python code: {str(e)}"
            logger.error(error_msg)
            return error_msg

    def _generate_code_from_requirements(
        self, requirements: str, include_docstring: bool, include_imports: bool
    ) -> str:
        """Generate Python code based on natural language requirements."""

        # Analyze requirements to determine code structure
        code_structure = self._analyze_requirements(requirements)

        # Generate code components
        imports = self._generate_imports(code_structure) if include_imports else []
        functions = self._generate_functions(code_structure, include_docstring)
        classes = self._generate_classes(code_structure, include_docstring)
        main_logic = self._generate_main_logic(code_structure, include_docstring)

        # Combine all parts
        code_parts = []

        # Add shebang and encoding
        code_parts.append("#!/usr/bin/env python3")
        code_parts.append("# -*- coding: utf-8 -*-")
        code_parts.append("")

        # Add imports
        if imports:
            code_parts.extend(imports)
            code_parts.append("")

        # Add functions
        if functions:
            code_parts.extend(functions)
            code_parts.append("")

        # Add classes
        if classes:
            code_parts.extend(classes)
            code_parts.append("")

        # Add main logic
        if main_logic:
            code_parts.extend(main_logic)

        # Add main guard
        if code_structure.get("needs_main_guard", True):
            code_parts.append("")
            code_parts.append("if __name__ == '__main__':")
            code_parts.append("    main()")

        return "\n".join(code_parts)

    def _analyze_requirements(self, requirements: str) -> dict:
        """Analyze requirements to determine code structure needed."""

        req_lower = requirements.lower()

        structure = {
            "needs_functions": False,
            "needs_classes": False,
            "needs_main_guard": True,
            "imports_needed": [],
            "function_names": [],
            "class_names": [],
            "data_structures": [],
            "operations": []
        }

        # Detect common patterns
        if any(word in req_lower for word in ["function", "method", "def", "calculate", "compute", "process"]):
            structure["needs_functions"] = True

        if any(word in req_lower for word in ["class", "object", "instance", "inherit"]):
            structure["needs_classes"] = True

        # Detect data structures
        if any(word in req_lower for word in ["list", "array", "collection"]):
            structure["data_structures"].append("list")
        if any(word in req_lower for word in ["dict", "dictionary", "map"]):
            structure["data_structures"].append("dict")
        if any(word in req_lower for word in ["set"]):
            structure["data_structures"].append("set")

        # Detect operations
        if any(word in req_lower for word in ["file", "read", "write", "save", "load"]):
            structure["operations"].append("file_io")
            structure["imports_needed"].extend(["os", "pathlib"])
        if any(word in req_lower for word in ["http", "web", "api", "request"]):
            structure["operations"].append("http")
            structure["imports_needed"].append("requests")
        if any(word in req_lower for word in ["json"]):
            structure["operations"].append("json")
            structure["imports_needed"].append("json")
        if any(word in req_lower for word in ["math", "calculate", "compute"]):
            structure["operations"].append("math")
            structure["imports_needed"].append("math")

        # Basic imports that are commonly needed
        if not structure["imports_needed"]:
            structure["imports_needed"] = ["typing"]  # Basic typing support

        return structure

    def _generate_imports(self, structure: dict) -> list[str]:
        """Generate import statements."""
        imports = []

        for module in set(structure.get("imports_needed", [])):
            if module == "typing":
                imports.append("from typing import List, Dict, Optional, Any")
            else:
                imports.append(f"import {module}")

        return imports

    def _generate_functions(self, structure: dict, include_docstring: bool) -> list[str]:
        """Generate function definitions."""
        if not structure.get("needs_functions", False):
            return []

        functions = []

        # Generate a basic main function
        if structure.get("needs_main_guard", True):
            functions.append("def main() -> None:")
            if include_docstring:
                functions.append('    """Main function to run the program."""')
            functions.append('    print("Hello, World!")')
            functions.append('    # TODO: Implement main logic based on requirements')
            functions.append("")

        # Generate utility functions based on operations
        operations = structure.get("operations", [])
        if "file_io" in operations:
            functions.append("def read_file(file_path: str) -> str:")
            if include_docstring:
                functions.append('    """Read content from a file."""')
            functions.append("    try:")
            functions.append("        with open(file_path, 'r', encoding='utf-8') as f:")
            functions.append("            return f.read()")
            functions.append("    except FileNotFoundError:")
            functions.append("        raise FileNotFoundError(f\"File not found: {file_path}\")")
            functions.append("")

        if "math" in operations:
            functions.append("def calculate_average(numbers: List[float]) -> float:")
            if include_docstring:
                functions.append('    """Calculate the average of a list of numbers."""')
            functions.append("    if not numbers:")
            functions.append("        return 0.0")
            functions.append("    return sum(numbers) / len(numbers)")
            functions.append("")

        return functions

    def _generate_classes(self, structure: dict, include_docstring: bool) -> list[str]:
        """Generate class definitions."""
        if not structure.get("needs_classes", False):
            return []

        classes = []

        # Generate a basic example class
        classes.append("class DataProcessor:")
        if include_docstring:
            classes.append('    """A class for processing data."""')
        classes.append("")
        classes.append("    def __init__(self) -> None:")
        if include_docstring:
            classes.append('        """Initialize the data processor."""')
        classes.append("        self.data: List[Any] = []")
        classes.append("")
        classes.append("    def process(self, input_data: Any) -> Any:")
        if include_docstring:
            classes.append('        """Process the input data."""')
        classes.append("        # TODO: Implement processing logic")
        classes.append("        return input_data")
        classes.append("")

        return classes

    def _generate_main_logic(self, structure: dict, include_docstring: bool) -> list[str]:
        """Generate main logic code."""
        logic = []

        # Add some basic variable declarations based on data structures
        data_structures = structure.get("data_structures", [])
        if data_structures:
            logic.append("# Data structures")
            if "list" in data_structures:
                logic.append("data_list: List[Any] = []")
            if "dict" in data_structures:
                logic.append("data_dict: Dict[str, Any] = {}")
            if "set" in data_structures:
                logic.append("data_set: set = set()")
            logic.append("")

        return logic

    def _validate_python_code(self, code: str) -> dict:
        """Validate the generated Python code."""
        try:
            # Parse the code to check for syntax errors
            ast.parse(code)
            return {"valid": True, "errors": []}
        except SyntaxError as e:
            return {"valid": False, "errors": [f"Syntax error at line {e.lineno}: {e.msg}"]}
        except Exception as e:
            return {"valid": False, "errors": [f"Validation error: {str(e)}"]}


# Export tool instance
python_code_generator_tool = PythonCodeGeneratorTool()