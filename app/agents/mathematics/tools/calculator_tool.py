"""Calculator tool for mathematical calculations."""

import math
from typing import Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from app.utils.logger import logger


class CalculatorInput(BaseModel):
    """Input for calculator tool."""

    expression: str = Field(
        ...,
        description=(
            "Mathematical expression to evaluate. "
            "Supports basic arithmetic (+, -, *, /), exponents (**), "
            "and common math functions (sqrt, sin, cos, tan, log, exp, etc.). "
            "Example: '2 + 3 * 4', 'sqrt(16)', 'sin(pi/2)'"
        )
    )


class CalculatorTool(BaseTool):
    """Tool for performing mathematical calculations."""

    name: str = "calculator"
    description: str = (
        "Perform mathematical calculations and evaluate mathematical expressions. "
        "Supports arithmetic operations, exponents, roots, trigonometric functions, "
        "logarithms, and other common mathematical operations. "
        "Returns the numerical result of the calculation."
    )
    args_schema: Type[BaseModel] = CalculatorInput

    def _run(self, expression: str) -> str:
        """Evaluate the mathematical expression."""
        try:
            # Create a safe evaluation environment with math functions
            safe_dict = {
                "__builtins__": {},
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
                "sum": sum,
                "pow": pow,
                # Math constants
                "pi": math.pi,
                "e": math.e,
                "tau": math.tau,
                # Math functions
                "sqrt": math.sqrt,
                "exp": math.exp,
                "log": math.log,
                "log10": math.log10,
                "log2": math.log2,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "asin": math.asin,
                "acos": math.acos,
                "atan": math.atan,
                "atan2": math.atan2,
                "sinh": math.sinh,
                "cosh": math.cosh,
                "tanh": math.tanh,
                "degrees": math.degrees,
                "radians": math.radians,
                "ceil": math.ceil,
                "floor": math.floor,
                "fabs": math.fabs,
                "factorial": math.factorial,
                "gcd": math.gcd,
                "lcm": lambda a, b: abs(a * b) // math.gcd(a, b) if a and b else 0,
            }
            
            # Evaluate the expression safely
            result = eval(expression, safe_dict)
            
            # Format the result appropriately
            if isinstance(result, float):
                # Check if it's a whole number
                if result.is_integer():
                    result = int(result)
                else:
                    # Round to reasonable precision
                    result = round(result, 10)
            
            logger.info(f"Calculator evaluated '{expression}' = {result}")
            return f"Result: {result}"
            
        except ZeroDivisionError:
            error_msg = "Error: Division by zero"
            logger.error(f"Calculator error: {error_msg}")
            return error_msg
        except ValueError as e:
            error_msg = f"Error: Invalid mathematical operation - {str(e)}"
            logger.error(f"Calculator error: {error_msg}")
            return error_msg
        except SyntaxError as e:
            error_msg = f"Error: Invalid expression syntax - {str(e)}"
            logger.error(f"Calculator error: {error_msg}")
            return error_msg
        except Exception as e:
            error_msg = f"Error: Could not evaluate expression - {str(e)}"
            logger.error(f"Calculator error: {error_msg}")
            return error_msg


# Export tool instance
calculator_tool = CalculatorTool()

