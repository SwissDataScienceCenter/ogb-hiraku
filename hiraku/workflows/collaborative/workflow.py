"""Collaborative research as a checkpointed LangGraph workflow."""

from __future__ import annotations

import shlex
from functools import reduce
from operator import or_
from pathlib import Path
from typing import Annotated, Any, Literal, TypedDict

import frontmatter
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, create_model
from pydantic import ValidationError as PydanticValidationError

from hiraku.errors import HirakuError, ValidationError
from hiraku.git import GitRepository
from hiraku.job import validate_command
from hiraku.markdown import Markdown, render
from hiraku.project import Project
from hiraku.record import Record
from hiraku.tracking import Leaderboard

Verdict = Literal["supports", "refutes", "inconclusive"]
STEPS = ("draft", "implement", "launch", "analyze")


class ResearchState(TypedDict, total=False):
    arguments: dict[str, Any]
    task: str
    leaderboard: str | None
    command: list[str]
    rounds: int
    step: str
    experiment: str
    feedback: str
    results: list[dict[str, Any]]
    final: str


class CollaborativeInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    task: str | None = Field(
        default=None, description="Task record ID; defaults to active context."
    )
    command: list[str] = Field(min_length=1)
    rounds: int = Field(default=3, ge=1)
    leaderboard: str | None = Field(default=None, description="Leaderboard name.")


class DraftedArguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    name: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    hypothesis: str = Field(min_length=1)
    change: str = Field(min_length=1)


class FeedbackArguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    feedback: str = Field(min_length=1)


class ImplementedArguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    commit: str = Field(min_length=1)


class AnalyzedArguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    verdict: Verdict
    conclusion: str = Field(min_length=1)


class EmptyArguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


def input_schema() -> dict[str, Any]:
    """Return the JSON Schema for starting collaborative research."""
    return CollaborativeInput.model_json_schema()


def build_graph(checkpointer: BaseCheckpointSaver[Any], *, project: Project) -> Any:
    """Build the collaborative research graph from its Markdown instructions."""
    path = Path(__file__).with_name("workflow.md")
    post = frontmatter.load(path)
    fields = post.metadata
    if fields.get("id") != "collaborative":
        raise ValueError("workflow.md must declare id: collaborative")
    markdown = Markdown(post.content)
    rules = str(fields.get("rules", "")).strip()

    def initialize(state: ResearchState) -> Command[Literal["draft"]]:
        try:
            arguments = CollaborativeInput.model_validate(state.get("arguments", {}))
        except PydanticValidationError as exc:
            raise ValidationError(str(exc)) from exc
        task = arguments.task or project.active_record_id
        command = arguments.command
        rounds = arguments.rounds
        if not isinstance(task, str) or not task:
            raise ValidationError("Pass task or set an active Hiraku record")
        if not isinstance(command, list):
            raise ValidationError("command must be an argv list")
        command = validate_command(command)
        if type(rounds) is not int or rounds < 1:
            raise ValidationError("rounds must be a positive integer")
        try:
            project.vault.load(task)
        except HirakuError as exc:
            raise ValidationError(str(exc)) from exc
        return Command(
            update={
                "task": task,
                "leaderboard": arguments.leaderboard,
                "command": command,
                "rounds": rounds,
                "step": "draft",
                "results": [],
            },
            goto="draft",
        )

    def prompt(state: ResearchState, step: str, data: dict[str, Any]) -> dict[str, Any]:
        text = markdown.section(f"## {step.title()}")
        if rules:
            text = f"{text}\n\n{rules}"
        payload: dict[str, Any] = {
            "step": step,
            "instruction": text,
            "data": data,
            "approval": {
                "message": f"Approve the proposed {step} step?",
                "schema": WorkflowApproval.model_json_schema(),
            },
            "required_capabilities": {
                "draft": ["record.read", "workflow.user_input"],
                "implement": [
                    "filesystem.read",
                    "filesystem.write",
                    "shell.execute",
                    "git.commit",
                    "workflow.user_input",
                ],
                "launch": [
                    "experiment.launch",
                    "tracking.run.read",
                    "workflow.user_input",
                ],
                "analyze": ["tracking.run.read", "workflow.user_input"],
            }[step],
        }
        if state.get("feedback"):
            payload["feedback"] = state["feedback"]
        return payload

    def response_for(
        state: ResearchState, step: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        payload = prompt(state, step, data)
        direct_adapter, approval_adapter, response_schema = _step_response_contract(
            step
        )
        payload["response_schema"] = response_schema
        while True:
            response = interrupt(payload)
            if not isinstance(response, dict) or "approval" not in response:
                payload = {
                    **payload,
                    "error": "A valid approval decision is required.",
                }
                continue
            try:
                approved = approval_adapter.validate_python(response)
            except PydanticValidationError as exc:
                approval_error = any(
                    error["loc"][:2] == ("approval", "decision")
                    for error in exc.errors()
                )
                message = (
                    "A valid approval decision is required."
                    if approval_error
                    else str(exc)
                )
                payload = {**payload, "error": message}
                continue
            decision = approved.approval.decision
            if decision == "stop":
                return {"event": "finish", "arguments": {}}
            if approved.response is None and decision != "revise":
                payload = {
                    **payload,
                    "error": "An approved workflow response is required.",
                }
                continue
            submitted = (
                approved.response.model_dump() if approved.response is not None else {}
            )
            if decision == "revise":
                feedback = approved.approval.feedback or submitted.get(
                    "arguments", {}
                ).get("feedback")
                if not feedback:
                    feedback = "Please revise this proposal."
                revise_event = {
                    "draft": "revise_draft",
                    "implement": "revise_implementation",
                    "launch": "revise_launch",
                    "analyze": "revise_analysis",
                }[step]
                submitted = {
                    "event": revise_event,
                    "arguments": {"feedback": feedback},
                }
            try:
                action = direct_adapter.validate_python(submitted)
            except PydanticValidationError as exc:
                payload = {**payload, "error": str(exc)}
                continue
            return action.model_dump()

    def finish(state: ResearchState) -> Command[Literal["done"]]:
        return Command(update={"step": "done"}, goto="done")

    def draft(state: ResearchState) -> Command[Literal["draft", "implement", "done"]]:
        data = {"task": state["task"], "previous": state.get("results", [])}
        response = response_for(state, "draft", data)
        event, arguments = response["event"], response["arguments"]
        if event == "finish":
            return finish(state)
        if event == "revise_draft":
            feedback = arguments.get("feedback")
            if not isinstance(feedback, str):
                return Command(
                    update={"feedback": "Feedback must be a string."}, goto="draft"
                )
            return Command(update={"feedback": feedback}, goto="draft")
        required = ("name", "summary", "hypothesis", "change")
        if any(
            not isinstance(arguments.get(key), str) or not arguments[key].strip()
            for key in required
        ):
            return Command(
                update={
                    "feedback": (
                        "Provide non-empty name, summary, hypothesis, and change."
                    )
                },
                goto="draft",
            )
        try:
            record = project.vault.create(
                f"{state['task']}/{arguments['name']}",
                title=arguments["name"],
                parent_id=state["task"],
                type="experiment",
                state="drafted",
                summary=arguments["summary"],
                hypothesis=arguments["hypothesis"],
                markdown=f"## Change\n\n{arguments['change'].strip()}\n",
            )
        except HirakuError as exc:
            return Command(update={"feedback": str(exc)}, goto="draft")
        return Command(
            update={
                "experiment": record.id,
                "feedback": "",
                "step": "implement",
            },
            goto="implement",
        )

    def experiment(state: ResearchState) -> Record:
        identifier = state.get("experiment")
        if not identifier:
            raise ValidationError("No experiment has been drafted")
        return project.vault.load(identifier)

    def experiment_context(state: ResearchState) -> dict[str, Any]:
        record = experiment(state)
        return {
            "task": state["task"],
            "experiment": {
                "record_id": record.id,
                "summary": getattr(record, "summary", None),
                "hypothesis": getattr(record, "hypothesis", None),
                "change": record.markdown.strip(),
                "commit": record.commit,
            },
        }

    def implement(
        state: ResearchState,
    ) -> Command[Literal["implement", "launch", "done"]]:
        response = response_for(state, "implement", experiment_context(state))
        event, arguments = response["event"], response["arguments"]
        if event == "finish":
            return finish(state)
        if event == "revise_implementation":
            feedback = arguments.get("feedback")
            return Command(
                update={
                    "feedback": feedback
                    if isinstance(feedback, str)
                    else "Feedback must be a string."
                },
                goto="implement",
            )
        commit = arguments.get("commit")
        if not isinstance(commit, str):
            return Command(
                update={"feedback": "commit must be a Git commit reference."},
                goto="implement",
            )
        try:
            sha = GitRepository(project.root).resolve(commit)
            record = experiment(state)
            record.commit = sha
            record.state = "implemented"
            project.vault.save(record, overwrite=True)
        except HirakuError as exc:
            return Command(update={"feedback": str(exc)}, goto="implement")
        return Command(update={"feedback": "", "step": "launch"}, goto="launch")

    def launch(state: ResearchState) -> Command[Literal["launch", "analyze", "done"]]:
        record = experiment(state)
        data = experiment_context(state)
        data["command"] = shlex.join(
            ["hiraku", "run", "--record", record.id, "--", *state["command"]]
        )
        response = response_for(state, "launch", data)
        event, arguments = response["event"], response["arguments"]
        if event == "finish":
            return finish(state)
        if event == "revise_launch":
            feedback = arguments.get("feedback")
            return Command(
                update={
                    "feedback": feedback
                    if isinstance(feedback, str)
                    else "Feedback must be a string."
                },
                goto="launch",
            )
        runs = Leaderboard.load(project, state.get("leaderboard")).list_runs(
            project, record_id=record.id
        )
        if not runs:
            return Command(
                update={"feedback": f"No run is attributed to {record.id!r} yet."},
                goto="launch",
            )
        if any(run.commit not in (None, record.commit) for run in runs):
            return Command(
                update={
                    "feedback": "A run used a different commit than this experiment."
                },
                goto="launch",
            )
        record.state = "launched"
        project.vault.save(record, overwrite=True)
        return Command(update={"feedback": "", "step": "analyze"}, goto="analyze")

    def analyze(state: ResearchState) -> Command[Literal["analyze", "draft", "done"]]:
        record = experiment(state)
        leaderboard = Leaderboard.load(project, state.get("leaderboard"))
        runs = leaderboard.list_runs(project, record_id=record.id)
        data = {
            **experiment_context(state),
            "metrics": [metric.model_dump() for metric in leaderboard.metrics or ()],
            "runs": [{"run_id": run.id, "metrics": dict(run.metrics)} for run in runs],
            "previous": state.get("results", []),
        }
        if not any(run.metrics for run in runs):
            data["metrics_pending"] = True
            state = {**state, "feedback": "The attributed runs have no metrics yet."}
        response = response_for(state, "analyze", data)
        event, arguments = response["event"], response["arguments"]
        if event == "finish":
            return finish(state)
        if not any(run.metrics for run in runs) and event == "analyzed":
            return Command(
                update={"feedback": "The attributed runs have no metrics yet."},
                goto="analyze",
            )
        if event == "revise_analysis":
            feedback = arguments.get("feedback")
            return Command(
                update={
                    "feedback": feedback
                    if isinstance(feedback, str)
                    else "Feedback must be a string."
                },
                goto="analyze",
            )
        verdict, conclusion = arguments.get("verdict"), arguments.get("conclusion")
        if (
            verdict not in {"supports", "refutes", "inconclusive"}
            or not isinstance(conclusion, str)
            or not conclusion.strip()
        ):
            return Command(
                update={"feedback": "Provide a verdict and non-empty conclusion."},
                goto="analyze",
            )
        record.state = "analyzed"
        record.verdict = verdict
        record.conclusion = conclusion
        project.vault.save(record, overwrite=True)
        results = [
            *state.get("results", []),
            {"record_id": record.id, "verdict": verdict},
        ]
        next_step = "draft" if len(results) < state["rounds"] else "done"
        return Command(
            update={
                "results": results,
                "experiment": "",
                "feedback": "",
                "step": next_step,
            },
            goto=next_step,
        )

    def done(state: ResearchState) -> dict[str, str]:
        return {
            "final": render(
                markdown.section("## Done"), {"results": state.get("results", [])}
            )
        }

    builder = StateGraph(ResearchState)
    builder.add_node("initialize", initialize)
    builder.add_node("draft", draft)
    builder.add_node("implement", implement)
    builder.add_node("launch", launch)
    builder.add_node("analyze", analyze)
    builder.add_node("done", done)
    builder.add_edge(START, "initialize")
    builder.add_edge("done", END)
    return builder.compile(checkpointer=checkpointer)


class WorkflowApproval(BaseModel):
    """Decision required before a collaborative workflow step can proceed."""

    model_config = ConfigDict(
        json_schema_extra=lambda schema: schema.pop("title", None)
    )

    decision: Literal["approve", "revise", "stop"] = Field(
        description="Whether to approve, request a revision, or stop."
    )
    feedback: str | None = Field(
        default=None, description="Required guidance when requesting a revision."
    )


def _step_response_contract(
    step: str,
) -> tuple[TypeAdapter[Any], TypeAdapter[Any], dict[str, Any]]:
    arguments_by_event: dict[str, type[BaseModel]] = {
        "drafted": DraftedArguments,
        "implemented": ImplementedArguments,
        "analyzed": AnalyzedArguments,
        "revise_draft": FeedbackArguments,
        "revise_implementation": FeedbackArguments,
        "revise_launch": FeedbackArguments,
        "revise_analysis": FeedbackArguments,
        "launched": EmptyArguments,
        "finish": EmptyArguments,
    }
    events_by_step = {
        "draft": ("drafted", "revise_draft", "finish"),
        "implement": ("implemented", "revise_implementation", "finish"),
        "launch": ("launched", "revise_launch", "finish"),
        "analyze": ("analyzed", "revise_analysis", "finish"),
    }
    events = events_by_step[step]
    event_models = []
    for event in events:
        arguments_model = arguments_by_event[event]
        fields: dict[str, Any] = {"event": (Literal[event], ...)}
        if arguments_model is EmptyArguments:
            fields["arguments"] = (
                arguments_model,
                Field(default_factory=arguments_model),
            )
        else:
            fields["arguments"] = (arguments_model, ...)
        event_models.append(
            create_model(
                f"{step.title()}{event.title().replace('_', '')}Response",
                __config__=ConfigDict(extra="forbid", strict=True),
                **fields,
            )
        )
    action_type = Annotated[reduce(or_, event_models), Field(discriminator="event")]
    action_adapter = TypeAdapter(action_type)
    approval_model = create_model(
        f"{step.title()}ApprovalResponse",
        __config__=ConfigDict(extra="forbid", strict=True),
        approval=(WorkflowApproval, ...),
        response=(action_type | None, None),
    )
    approval_adapter = TypeAdapter(approval_model)
    schema = approval_adapter.json_schema()
    return action_adapter, approval_adapter, schema
