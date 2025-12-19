"""Feedback tools for rating tool executions and improving RL learning."""

from typing import Any, Optional

from fccs_agent.config import config
from fccs_agent.services.feedback_service import get_feedback_service


async def submit_feedback(
    execution_id: int,
    rating: int,
    feedback: Optional[str] = None
) -> dict[str, Any]:
    """Submit user feedback for a tool execution to improve RL learning.
    
    This tool allows you to rate a tool execution (1-5 stars) and provide
    optional feedback. This helps the RL system learn which tools work best
    for your use cases and improves future recommendations.
    
    Args:
        execution_id: The ID of the tool execution to rate (from tool result)
        rating: Rating from 1-5 stars (5 = excellent, 1 = poor)
        feedback: Optional text feedback about the execution
    
    Returns:
        dict: Status of feedback submission
    """
    if rating < 1 or rating > 5:
        return {
            "status": "error",
            "error": f"Rating must be between 1 and 5, got {rating}"
        }
    
    feedback_service = get_feedback_service()
    if not feedback_service:
        return {
            "status": "error",
            "error": "Feedback service not available"
        }
    
    try:
        feedback_service.add_user_feedback(
            execution_id=execution_id,
            rating=rating,
            feedback=feedback
        )
        
        return {
            "status": "success",
            "message": f"Feedback submitted: {rating} stars",
            "execution_id": execution_id,
            "rating": rating,
            "feedback": feedback
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to submit feedback: {str(e)}"
        }


async def get_recent_executions(
    tool_name: Optional[str] = None,
    limit: int = 10
) -> dict[str, Any]:
    """Get recent tool executions that can be rated.
    
    Use this to find execution IDs for tools you want to provide feedback on.
    
    Args:
        tool_name: Optional filter by specific tool name
        limit: Maximum number of executions to return (default: 10)
    
    Returns:
        dict: List of recent executions with their IDs and status
    """
    feedback_service = get_feedback_service()
    if not feedback_service:
        return {
            "status": "error",
            "error": "Feedback service not available"
        }
    
    try:
        executions = feedback_service.get_recent_executions(
            tool_name=tool_name,
            limit=limit
        )
        
        return {
            "status": "success",
            "executions": executions,
            "count": len(executions)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to get executions: {str(e)}"
        }


# Tool definitions for MCP server
TOOL_DEFINITIONS = [
    {
        "name": "submit_feedback",
        "description": "Submit user feedback (rating 1-5 stars) for a tool execution to improve RL learning / Enviar feedback do usuario para melhorar aprendizado RL",
        "inputSchema": {
            "type": "object",
            "properties": {
                "execution_id": {
                    "type": "integer",
                    "description": "The ID of the tool execution to rate (found in tool result or from get_recent_executions)",
                },
                "rating": {
                    "type": "integer",
                    "description": "Rating from 1-5 stars (5 = excellent, 4 = good, 3 = average, 2 = poor, 1 = bad)",
                    "minimum": 1,
                    "maximum": 5,
                },
                "feedback": {
                    "type": "string",
                    "description": "Optional text feedback about the execution",
                },
            },
            "required": ["execution_id", "rating"],
        },
    },
    {
        "name": "get_recent_executions",
        "description": "Get recent tool executions that can be rated / Obter execucoes recentes que podem ser avaliadas",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": "string",
                    "description": "Optional filter by specific tool name",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of executions to return (default: 10)",
                    "default": 10,
                },
            },
        },
    },
]


