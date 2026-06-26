import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AgentContext:
    query: str
    user_role: str = "analyst"
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)
    intermediate_results: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    agent_name: str
    success: bool
    output: Any
    confidence: float = 1.0
    latency_ms: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    def __init__(self, name: str, config: Optional[Dict] = None):
        self.name = name
        self.config = config or {}

    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResult:
        ...

    async def run(self, context: AgentContext) -> AgentResult:
        start = time.time()
        try:
            result = await self.execute(context)
            result.latency_ms = round((time.time() - start) * 1000, 2)
            result.agent_name = self.name
            return result
        except Exception as e:
            elapsed = round((time.time() - start) * 1000, 2)
            return AgentResult(
                agent_name=self.name,
                success=False,
                output=None,
                error=str(e),
                latency_ms=elapsed,
            )
