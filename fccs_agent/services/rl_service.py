"""Reinforcement Learning Service for tool selection and optimization."""

import hashlib
import json
import random
from datetime import datetime
from typing import Any, Optional, dict, list
from collections import defaultdict

import numpy as np
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, create_engine, func, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker

from fccs_agent.services.feedback_service import FeedbackService, ToolExecution, ToolMetrics

Base = declarative_base()


class RLPolicy(Base):
    """RL Policy table for storing Q-values and action values."""

    __tablename__ = "rl_policy"

    id = Column(Integer, primary_key=True)
    tool_name = Column(String(255), nullable=False, index=True)
    context_hash = Column(String(64), nullable=False, index=True)
    action_value = Column(Float, default=0.0)  # Q-value or expected reward
    visit_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('tool_name', 'context_hash', name='uq_tool_context'),
    )



class RLEpisode(Base):
    """RL Episode table for tracking complete sessions."""

    __tablename__ = "rl_episodes"

    id = Column(Integer, primary_key=True)
    session_id = Column(String(255), nullable=False, index=True)
    episode_reward = Column(Float, default=0.0)
    tool_sequence = Column(JSON)  # List of tool names used in sequence
    outcome = Column(String(50))  # 'success', 'partial', 'failure'
    created_at = Column(DateTime, default=datetime.utcnow)


class RewardCalculator:
    """Calculate rewards from tool execution results."""

    @staticmethod
    def calculate_reward(
        execution: ToolExecution,
        avg_execution_time: Optional[float] = None
    ) -> float:
        """Calculate reward for a tool execution.
        
        Reward Components:
        - Success: +10 if succeeded, -5 if failed
        - User Rating: (rating - 3) * 2 (normalized to -4 to +4)
        - Performance: -0.1 * (execution_time_ms / 1000) (penalize slow)
        - Efficiency Bonus: +2 if execution_time < avg * 0.8
        
        Returns:
            float: Total reward in range approximately -9 to +16
        """
        reward = 0.0
        
        # Success reward
        if execution.success:
            reward += 10.0
        else:
            reward -= 5.0
        
        # User rating reward (if available)
        if execution.user_rating is not None:
            rating_reward = (execution.user_rating - 3) * 2.0
            reward += rating_reward
        
        # Performance penalty (normalize execution time)
        if execution.execution_time_ms:
            time_penalty = -0.1 * (execution.execution_time_ms / 1000.0)
            reward += time_penalty
            
            # Efficiency bonus
            if avg_execution_time and execution.execution_time_ms < avg_execution_time * 0.8:
                reward += 2.0
        
        return reward


class ToolSelector:
    """Intelligent tool selection based on RL policy and context."""

    def __init__(
        self,
        feedback_service: FeedbackService,
        exploration_rate: float = 0.1,
        min_samples: int = 5
    ):
        self.feedback_service = feedback_service
        self.exploration_rate = exploration_rate
        self.min_samples = min_samples
        self._tool_metadata_cache: Optional[dict] = None

    def create_context_hash(
        self,
        user_query: str = "",
        previous_tool: Optional[str] = None,
        session_length: int = 0
    ) -> str:
        """Create a hash representing the current state/context.
        
        Args:
            user_query: User's query or intent
            previous_tool: Previously executed tool name
            session_length: Number of tools executed in this session
            
        Returns:
            str: SHA256 hash of the context
        """
        # Extract keywords from query (simple approach)
        keywords = self._extract_keywords(user_query)
        
        context = {
            "keywords": sorted(keywords),
            "previous_tool": previous_tool or "",
            "session_length": session_length
        }
        
        context_str = json.dumps(context, sort_keys=True)
        return hashlib.sha256(context_str.encode()).hexdigest()

    def _extract_keywords(self, query: str) -> list[str]:
        """Extract relevant keywords from user query."""
        if not query:
            return []
        
        # Common FCCS-related keywords
        fccs_keywords = [
            "dimension", "member", "account", "entity", "period", "scenario",
            "journal", "consolidation", "report", "data", "retrieve", "export",
            "import", "rule", "job", "status", "hierarchy", "balance", "currency"
        ]
        
        query_lower = query.lower()
        found_keywords = [kw for kw in fccs_keywords if kw in query_lower]
        
        # Also include first few words as keywords
        words = query_lower.split()[:5]
        found_keywords.extend(words)
        
        return list(set(found_keywords))  # Remove duplicates

    def get_tool_recommendations(
        self,
        context_hash: str,
        available_tools: list[str],
        rl_policy: Optional[dict] = None
    ) -> list[dict]:
        """Get ranked list of recommended tools with confidence scores.
        
        Args:
            context_hash: Current context hash
            available_tools: List of available tool names
            rl_policy: Optional dict mapping (tool_name, context_hash) -> action_value
            
        Returns:
            List of dicts with tool_name, confidence, and reason
        """
        recommendations = []
        
        # Get tool metrics from feedback service
        all_metrics = self.feedback_service.get_tool_metrics()
        metrics_dict = {m["tool_name"]: m for m in all_metrics}
        
        for tool_name in available_tools:
            confidence = 0.5  # Default confidence
            reason = "Baseline recommendation"
            
            # Get metrics for this tool
            tool_metrics = metrics_dict.get(tool_name, {})
            
            # Calculate confidence based on multiple factors
            factors = []
            
            # Factor 1: Success rate
            success_rate = tool_metrics.get("success_rate", 0.5)
            if success_rate > 0.8:
                confidence += 0.2
                factors.append("high success rate")
            elif success_rate < 0.5:
                confidence -= 0.2
                factors.append("low success rate")
            
            # Factor 2: User ratings
            avg_rating = tool_metrics.get("avg_user_rating")
            if avg_rating:
                if avg_rating >= 4.0:
                    confidence += 0.15
                    factors.append("high user rating")
                elif avg_rating < 3.0:
                    confidence -= 0.15
                    factors.append("low user rating")
            
            # Factor 3: Execution time (faster is better)
            avg_time = tool_metrics.get("avg_execution_time_ms", 0)
            if avg_time > 0 and avg_time < 1000:  # Less than 1 second
                confidence += 0.1
                factors.append("fast execution")
            
            # Factor 4: RL policy value (if available)
            if rl_policy:
                policy_key = f"{tool_name}:{context_hash}"
                action_value = rl_policy.get(policy_key, 0.0)
                if action_value > 0:
                    confidence += min(0.2, action_value / 10.0)  # Normalize
                    factors.append("RL policy favor")
            
            # Factor 5: Sample size (more samples = more reliable)
            total_calls = tool_metrics.get("total_calls", 0)
            if total_calls >= self.min_samples:
                confidence += 0.05
                factors.append("sufficient samples")
            
            # Clamp confidence to [0, 1]
            confidence = max(0.0, min(1.0, confidence))
            
            if factors:
                reason = ", ".join(factors)
            
            recommendations.append({
                "tool_name": tool_name,
                "confidence": round(confidence, 3),
                "reason": reason,
                "metrics": {
                    "success_rate": success_rate,
                    "avg_rating": avg_rating,
                    "total_calls": total_calls
                }
            })
        
        # Sort by confidence (descending)
        recommendations.sort(key=lambda x: x["confidence"], reverse=True)
        
        return recommendations

    def select_tool(
        self,
        context_hash: str,
        available_tools: list[str],
        rl_policy: Optional[dict] = None
    ) -> tuple[str, bool]:
        """Select a tool using epsilon-greedy strategy.
        
        Args:
            context_hash: Current context hash
            available_tools: List of available tool names
            rl_policy: Optional dict mapping (tool_name, context_hash) -> action_value
            
        Returns:
            Tuple of (selected_tool_name, was_exploration)
        """
        if not available_tools:
            raise ValueError("No available tools provided")
        
        # Epsilon-greedy: explore with probability exploration_rate
        if random.random() < self.exploration_rate:
            # Exploration: random selection
            return random.choice(available_tools), True
        
        # Exploitation: select best tool based on recommendations
        recommendations = self.get_tool_recommendations(
            context_hash, available_tools, rl_policy
        )
        
        if recommendations:
            return recommendations[0]["tool_name"], False
        
        # Fallback to random
        return random.choice(available_tools), False


class ParameterOptimizer:
    """Learn optimal parameter patterns from successful executions."""

    def __init__(self, feedback_service: FeedbackService):
        self.feedback_service = feedback_service

    def suggest_parameters(
        self,
        tool_name: str,
        partial_args: dict,
        limit: int = 10
    ) -> dict:
        """Suggest optimal parameters based on historical successful executions.
        
        Args:
            tool_name: Name of the tool
            partial_args: Partial arguments provided by user
            limit: Number of historical executions to analyze
            
        Returns:
            Dict with suggested parameters and confidence
        """
        # Get recent successful executions for this tool
        recent_executions = self.feedback_service.get_recent_executions(
            tool_name=tool_name,
            limit=limit * 2  # Get more to filter for success
        )
        
        # Filter for successful executions with high ratings
        successful = [
            e for e in recent_executions
            if e.get("success") and e.get("user_rating", 0) >= 4
        ][:limit]
        
        if not successful:
            return {
                "suggested_params": partial_args,
                "confidence": 0.0,
                "reason": "No successful historical data"
            }
        
        # Get full execution details to extract arguments
        # Note: This would require extending feedback_service to return full execution details
        # For now, return partial args with confidence based on success rate
        success_rate = len(successful) / len(recent_executions) if recent_executions else 0
        
        return {
            "suggested_params": partial_args,
            "confidence": min(1.0, success_rate),
            "reason": f"Based on {len(successful)} successful executions",
            "sample_size": len(successful)
        }


class RLService:
    """Main RL service coordinating all RL components."""

    def __init__(
        self,
        feedback_service: FeedbackService,
        db_url: str,
        exploration_rate: float = 0.1,
        learning_rate: float = 0.1,
        discount_factor: float = 0.9,
        min_samples: int = 5
    ):
        self.feedback_service = feedback_service
        self.exploration_rate = exploration_rate
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.min_samples = min_samples
        
        # Initialize database for RL tables
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
        # Initialize components
        self.reward_calculator = RewardCalculator()
        self.tool_selector = ToolSelector(
            feedback_service,
            exploration_rate=exploration_rate,
            min_samples=min_samples
        )
        self.parameter_optimizer = ParameterOptimizer(feedback_service)
        
        # Cache for policy values (in-memory for performance)
        self._policy_cache: dict[str, float] = {}
        self._cache_updated = False

    def calculate_reward(self, execution: ToolExecution) -> float:
        """Calculate reward for a tool execution."""
        # Get average execution time for this tool
        metrics = self.feedback_service.get_tool_metrics(execution.tool_name)
        avg_time = metrics[0].get("avg_execution_time_ms") if metrics else None
        
        return self.reward_calculator.calculate_reward(execution, avg_time)

    def get_tool_recommendations(
        self,
        user_query: str = "",
        previous_tool: Optional[str] = None,
        session_length: int = 0,
        available_tools: Optional[list[str]] = None
    ) -> list[dict]:
        """Get tool recommendations for current context.
        
        Args:
            user_query: User's query or intent
            previous_tool: Previously executed tool
            session_length: Number of tools in current session
            available_tools: Optional list of available tools (if None, uses all)
            
        Returns:
            List of recommended tools with confidence scores
        """
        # Create context hash
        context_hash = self.tool_selector.create_context_hash(
            user_query, previous_tool, session_length
        )
        
        # Get available tools
        if available_tools is None:
            # Get all tools from feedback service metrics
            all_metrics = self.feedback_service.get_tool_metrics()
            available_tools = [m["tool_name"] for m in all_metrics]
        
        # Get RL policy
        rl_policy = self._get_policy_dict()
        
        return self.tool_selector.get_tool_recommendations(
            context_hash, available_tools, rl_policy
        )

    def optimize_parameters(
        self,
        tool_name: str,
        context: dict,
        partial_args: dict
    ) -> dict:
        """Optimize parameters for a tool based on context."""
        return self.parameter_optimizer.suggest_parameters(
            tool_name, partial_args
        )

    def update_policy(
        self,
        session_id: str,
        tool_name: str,
        context_hash: str,
        reward: float
    ):
        """Update RL policy using Q-learning update rule.
        
        Q(s,a) = Q(s,a) + alpha * [reward + gamma * max(Q(s',a')) - Q(s,a)]
        
        For simplicity, we use a simpler update:
        Q(s,a) = Q(s,a) + alpha * [reward - Q(s,a)]
        """
        with self.Session() as session:
            # Get or create policy entry
            policy = session.query(RLPolicy).filter_by(
                tool_name=tool_name,
                context_hash=context_hash
            ).first()
            
            if not policy:
                policy = RLPolicy(
                    tool_name=tool_name,
                    context_hash=context_hash,
                    action_value=0.0,
                    visit_count=0
                )
                session.add(policy)
                session.flush()
            
            # Q-learning update
            old_value = policy.action_value
            new_value = old_value + self.learning_rate * (reward - old_value)
            
            policy.action_value = new_value
            policy.visit_count += 1
            policy.last_updated = datetime.utcnow()
            
            session.commit()
            
            # Update cache
            cache_key = f"{tool_name}:{context_hash}"
            self._policy_cache[cache_key] = new_value
            self._cache_updated = True

    def _get_policy_dict(self) -> dict[str, float]:
        """Get policy as dictionary for fast lookup."""
        if not self._cache_updated:
            # Load from database
            with self.Session() as session:
                policies = session.query(RLPolicy).all()
                for policy in policies:
                    key = f"{policy.tool_name}:{policy.context_hash}"
                    self._policy_cache[key] = policy.action_value
                self._cache_updated = True
        
        return self._policy_cache

    def get_tool_confidence(
        self,
        tool_name: str,
        context_hash: str
    ) -> float:
        """Get confidence score for a tool in given context."""
        policy_dict = self._get_policy_dict()
        key = f"{tool_name}:{context_hash}"
        action_value = policy_dict.get(key, 0.0)
        
        # Normalize to [0, 1] range (assuming rewards are in [-10, 20] range)
        # Map to [0, 1] using sigmoid-like function
        confidence = 1.0 / (1.0 + np.exp(-action_value / 5.0))
        return float(confidence)

    def log_episode(
        self,
        session_id: str,
        tool_sequence: list[str],
        episode_reward: float,
        outcome: str = "success"
    ):
        """Log a complete episode (session) for sequence learning."""
        with self.Session() as session:
            episode = RLEpisode(
                session_id=session_id,
                episode_reward=episode_reward,
                tool_sequence=tool_sequence,
                outcome=outcome,
                created_at=datetime.utcnow()
            )
            session.add(episode)
            session.commit()

    def get_successful_sequences(
        self,
        tool_name: Optional[str] = None,
        limit: int = 10
    ) -> list[dict]:
        """Get successful tool sequences for pattern learning."""
        with self.Session() as session:
            query = session.query(RLEpisode).filter_by(outcome="success")
            if tool_name:
                # Filter sequences that contain this tool
                query = query.filter(
                    RLEpisode.tool_sequence.contains([tool_name])
                )
            
            episodes = query.order_by(
                RLEpisode.episode_reward.desc()
            ).limit(limit).all()
            
            return [
                {
                    "session_id": e.session_id,
                    "tool_sequence": e.tool_sequence,
                    "episode_reward": e.episode_reward,
                    "created_at": e.created_at.isoformat() if e.created_at else None
                }
                for e in episodes
            ]


# Global RL service instance
_rl_service: Optional[RLService] = None


def init_rl_service(
    feedback_service: FeedbackService,
    db_url: str,
    exploration_rate: float = 0.1,
    learning_rate: float = 0.1,
    discount_factor: float = 0.9,
    min_samples: int = 5
) -> RLService:
    """Initialize the global RL service."""
    global _rl_service
    _rl_service = RLService(
        feedback_service,
        db_url,
        exploration_rate=exploration_rate,
        learning_rate=learning_rate,
        discount_factor=discount_factor,
        min_samples=min_samples
    )
    return _rl_service


def get_rl_service() -> Optional[RLService]:
    """Get the global RL service instance."""
    return _rl_service

