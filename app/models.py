from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: str = "gpt-4o-mini"  # gpt-4o-mini | claude-3.5 | dummy
    cb_context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    reply: str
    usage: Dict[str, int]
    trace_id: str

class RAGQueryRequest(BaseModel):
    panel: str  # user | business | agency | dev
    q: str
    k: int = 5

class RAGQueryResponse(BaseModel):
    answers: List[Dict[str, Any]]
    trace_id: str

class NHAInvokeRequest(BaseModel):
    post: Dict[str, Any]  # {panel, text, author}

class NHAInvokeResponse(BaseModel):
    post_id: str
    invocations: List[Dict[str, Any]]
    ledger_delta: float
    trace_id: str

class InvocationStatus(BaseModel):
    id: str
    agent_id: str
    status: str  # queued, running, done, error
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    cost_cbT: float = 0
    trace_id: Optional[str] = None

class InvocationsResponse(BaseModel):
    invocations: List[InvocationStatus]

class LedgerBalance(BaseModel):
    balance: float
    last_activity: Optional[datetime] = None

class MetricsSnapshot(BaseModel):
    chat_p50_ms: float
    chat_p95_ms: float
    rag_p50_ms: float
    rag_p95_ms: float
    ws_connects_per_min: int
    invocations_success_rate: float
    ledger_delta_session: float
    nha_queue_pending: int
    nha_p95_ms: Dict[str, float]
    orchestrator_active_runs: int
    orchestrator_queue_pending: int
    orchestrator_p95_ms: Dict[str, float]
    timestamp: datetime

# Orchestrator models
class FlowSpec(BaseModel):
    id: str
    panel: str
    version: int
    trigger: Dict[str, Any]
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, str]]

class FlowCreate(BaseModel):
    name: str
    panel: str
    spec: FlowSpec

class FlowResponse(BaseModel):
    id: str
    name: str
    panel: str
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    spec: FlowSpec

class FlowRunRequest(BaseModel):
    input: Optional[Dict[str, Any]] = None
    mode: str = "live"  # live|dry

class FlowRunResponse(BaseModel):
    run_id: str
    flow_id: str
    status: str
    trace_id: str

class RunEventResponse(BaseModel):
    id: str
    ts: datetime
    level: str
    node_id: Optional[str] = None
    message: str
    data: Optional[Dict[str, Any]] = None

class NodeStatus(BaseModel):
    node_id: str
    status: str
    output: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    took_ms: Optional[int] = None

class FlowRunDetails(BaseModel):
    id: str
    flow_id: str
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    trigger_ref: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = None
    nodes: List[NodeStatus] = []
