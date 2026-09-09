"""Agent-independent request/result contract and an offline dummy implementation."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class PlannerRequest:
    repository: str
    issue_number: int
    policy_path: str


@dataclass(frozen=True)
class Plan:
    summary: str
    steps: tuple[str, ...]


@dataclass(frozen=True)
class PlannerResult:
    schema_version: int
    status: str
    request: PlannerRequest
    plan: Plan


class Planner(Protocol):
    def plan(self, request: PlannerRequest) -> PlannerResult: ...


class DummyPlanner:
    def plan(self, request: PlannerRequest) -> PlannerResult:
        return PlannerResult(
            schema_version=1,
            status="dummy",
            request=request,
            plan=Plan(
                summary=f"Dummy plan for {request.repository}#{request.issue_number}",
                steps=("Placeholder only: no context collected or implementation performed.",),
            ),
        )
