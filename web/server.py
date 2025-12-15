"""Web Server - FastAPI endpoints for HTTP access."""

import json
from contextlib import asynccontextmanager
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel
import uvicorn

from fccs_agent.config import config
from fccs_agent.agent import (
    initialize_agent,
    close_agent,
    execute_tool,
    get_tool_definitions,
)
from fccs_agent.services.feedback_service import get_feedback_service
from fccs_agent.services.rl_service import get_rl_service
from fccs_agent.agent import execute_tool_with_rl, finalize_session


# Request/Response models
class ToolCallRequest(BaseModel):
    """Request to call a tool."""
    tool_name: str
    arguments: dict[str, Any] = {}
    session_id: str = "default"


class ToolCallResponse(BaseModel):
    """Response from a tool call."""
    status: str
    data: Optional[Any] = None
    error: Optional[str] = None


class ChatRequest(BaseModel):
    """Chat request (for future ADK integration)."""
    message: str
    session_id: str = "default"
    user_id: str = "default"


class FeedbackRequest(BaseModel):
    """User feedback for a tool execution."""
    execution_id: int
    rating: int  # 1-5
    feedback: Optional[str] = None


# Lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    await initialize_agent()
    yield
    # Shutdown
    await close_agent()


# Create FastAPI app
app = FastAPI(
    title="FCCS Agent API",
    description="Oracle FCCS Agentic MCP Server API",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "name": "FCCS Agent API",
        "version": "0.1.0",
        "status": "healthy",
        "mock_mode": config.fccs_mock_mode
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "mock_mode": config.fccs_mock_mode}


@app.get("/tools")
async def list_tools():
    """List available FCCS tools."""
    return {"tools": get_tool_definitions()}


@app.post("/tools/{tool_name}", response_model=ToolCallResponse)
async def call_tool(tool_name: str, request: ToolCallRequest):
    """Call a specific tool."""
    try:
        result = await execute_tool(
            tool_name,
            request.arguments,
            request.session_id
        )
        return ToolCallResponse(
            status=result.get("status", "success"),
            data=result.get("data"),
            error=result.get("error")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/execute", response_model=ToolCallResponse)
async def execute(request: ToolCallRequest):
    """Execute a tool by name."""
    try:
        result = await execute_tool(
            request.tool_name,
            request.arguments,
            request.session_id
        )
        return ToolCallResponse(
            status=result.get("status", "success"),
            data=result.get("data"),
            error=result.get("error")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """Submit user feedback for a tool execution."""
    feedback_service = get_feedback_service()
    if not feedback_service:
        raise HTTPException(status_code=503, detail="Feedback service not available")

    feedback_service.add_user_feedback(
        execution_id=request.execution_id,
        rating=request.rating,
        feedback=request.feedback
    )
    return {"status": "success"}


@app.get("/metrics")
async def get_metrics(tool_name: Optional[str] = None):
    """Get tool execution metrics."""
    feedback_service = get_feedback_service()
    if not feedback_service:
        return {"metrics": [], "note": "Feedback service not available"}

    return {"metrics": feedback_service.get_tool_metrics(tool_name)}


@app.get("/executions")
async def get_executions(tool_name: Optional[str] = None, limit: int = 50):
    """Get recent tool executions."""
    feedback_service = get_feedback_service()
    if not feedback_service:
        return {"executions": [], "note": "Feedback service not available"}

    return {"executions": feedback_service.get_recent_executions(tool_name, limit)}


# RL Endpoints
@app.get("/rl/metrics")
async def get_rl_metrics():
    """Get overall RL performance metrics."""
    rl_service = get_rl_service()
    if not rl_service:
        return {"metrics": {}, "note": "RL service not available"}

    feedback_service = get_feedback_service()
    if not feedback_service:
        return {"metrics": {}, "note": "Feedback service not available"}

    # Get tool metrics
    tool_metrics = feedback_service.get_tool_metrics()
    
    # Calculate aggregate statistics
    total_tools = len(tool_metrics)
    avg_success_rate = sum(m.get("success_rate", 0) for m in tool_metrics) / total_tools if total_tools > 0 else 0
    avg_rating = sum(m.get("avg_user_rating", 0) or 0 for m in tool_metrics) / total_tools if total_tools > 0 else 0
    
    # Get policy statistics
    policy_dict = rl_service._get_policy_dict()
    total_policies = len(policy_dict)
    avg_action_value = sum(policy_dict.values()) / total_policies if total_policies > 0 else 0

    return {
        "rl_enabled": True,
        "tool_metrics": {
            "total_tools": total_tools,
            "avg_success_rate": round(avg_success_rate, 3),
            "avg_user_rating": round(avg_rating, 2)
        },
        "policy_metrics": {
            "total_policies": total_policies,
            "avg_action_value": round(avg_action_value, 3)
        },
        "config": {
            "exploration_rate": config.rl_exploration_rate,
            "learning_rate": config.rl_learning_rate,
            "discount_factor": config.rl_discount_factor,
            "min_samples": config.rl_min_samples
        }
    }


@app.get("/rl/policy/{tool_name}")
async def get_rl_policy(tool_name: str):
    """Get current RL policy for a specific tool."""
    rl_service = get_rl_service()
    if not rl_service:
        return {"policy": {}, "note": "RL service not available"}

    # Get all policies for this tool
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from fccs_agent.services.rl_service import RLPolicy
    from fccs_agent.config import config

    engine = create_engine(config.database_url)
    Session = sessionmaker(bind=engine)
    
    with Session() as session:
        policies = session.query(RLPolicy).filter_by(tool_name=tool_name).all()
        
        policy_data = [
            {
                "context_hash": p.context_hash,
                "action_value": p.action_value,
                "visit_count": p.visit_count,
                "last_updated": p.last_updated.isoformat() if p.last_updated else None
            }
            for p in policies
        ]
    
    return {
        "tool_name": tool_name,
        "policies": policy_data,
        "total_contexts": len(policy_data)
    }


@app.post("/rl/recommendations")
async def get_rl_recommendations(request: dict):
    """Get RL-based tool recommendations for a query."""
    rl_service = get_rl_service()
    if not rl_service:
        return {"recommendations": [], "note": "RL service not available"}

    user_query = request.get("query", "")
    session_id = request.get("session_id", "default")
    previous_tool = request.get("previous_tool")
    session_length = request.get("session_length", 0)

    recommendations = rl_service.get_tool_recommendations(
        user_query=user_query,
        previous_tool=previous_tool,
        session_length=session_length
    )

    return {
        "query": user_query,
        "recommendations": recommendations[:10]  # Top 10
    }


@app.get("/rl/episodes")
async def get_rl_episodes(tool_name: Optional[str] = None, limit: int = 20):
    """Get successful tool sequences (episodes) for pattern learning."""
    rl_service = get_rl_service()
    if not rl_service:
        return {"episodes": [], "note": "RL service not available"}

    episodes = rl_service.get_successful_sequences(tool_name=tool_name, limit=limit)
    return {"episodes": episodes}


@app.post("/execute/rl", response_model=ToolCallResponse)
async def execute_with_rl(request: ToolCallRequest):
    """Execute a tool with RL-enhanced recommendations."""
    try:
        user_query = request.arguments.pop("user_query", "") if isinstance(request.arguments, dict) else ""
        result = await execute_tool_with_rl(
            request.tool_name,
            request.arguments,
            request.session_id,
            user_query
        )
        return ToolCallResponse(
            status=result.get("status", "success"),
            data=result.get("data"),
            error=result.get("error")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sessions/{session_id}/finalize")
async def finalize_rl_session(session_id: str, outcome: str = "success"):
    """Finalize a session and log episode for RL learning."""
    finalize_session(session_id, outcome)
    return {"status": "success", "session_id": session_id, "outcome": outcome}


@app.get("/openapi.json")
async def openapi():
    """OpenAPI schema for ChatGPT Custom GPT."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="FCCS Agent API",
        version="0.1.0",
        description="Oracle FCCS Agentic MCP Server API for ChatGPT Custom GPT",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


# MCP-compatible endpoints for ChatGPT Custom GPT
@app.post("/message")
async def mcp_message(request: dict):
    """Handle MCP-style JSON-RPC messages."""
    method = request.get("method")
    params = request.get("params", {})

    if method == "tools/list":
        return {"tools": get_tool_definitions()}

    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        result = await execute_tool(tool_name, arguments)
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, indent=2, ensure_ascii=False)
                }
            ]
        }

    else:
        raise HTTPException(status_code=400, detail=f"Unknown method: {method}")


def main():
    """Entry point for web server."""
    import os
    # Cloud Run sets PORT environment variable
    port = int(os.environ.get("PORT", config.port))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
