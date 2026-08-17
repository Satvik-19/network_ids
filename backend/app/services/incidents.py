"""incidents.py — Deterministic rule-based incident grouping (Phase 3).

The replay engine emits one prediction per flow; this service decides which
flow starts / joins / is excluded from an incident (PRD §14).

Design rules (all deterministic, no randomness):

  * Only flows classified KNOWN_ATTACK or UNKNOWN_SUSPICIOUS can open or
    extend an incident. Pure-BENIGN flows never create an incident.
  * Grouping key = (classification, family, source, destination [, service_port]).
    service_port is included ONLY for non-scanning families — a Reconnaissance /
    PortScan campaign touches many ports and must remain ONE incident (the
    "service/port where meaningful" rule). Port stays stored as per-flow
    evidence either way.
  * A flow whose key matches an open incident joins it when it arrives within
    ``window_seconds`` of that incident start (config: incidents.
    grouping_window_seconds). Arriving outside the window supersedes the old
    incident (old one is ended) and opens a new one.
  * Aggregation: flow_count, first seen (start), last activity, max risk
    score/level. Incident label = the label of the flow with the highest risk
    (ties → earliest seq), so the displayed label is the dominant signal.

The grouper is stateful (tracks open groups) but holds NO database references —
the replay service translates assignments into Incident / IncidentFlow rows.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

# Families whose flows spread across many ports; port must not fragment them.
SCAN_FAMILIES = frozenset({"Reconnaissance"})

SUSPICIOUS = frozenset({"KNOWN_ATTACK", "UNKNOWN_SUSPICIOUS"})
BENIGN = "BENIGN"


@dataclass
class OpenGroup:
    """In-memory state of one open incident (spans one replay run)."""

    group_id: int                    # deterministic per-run unique id
    key: tuple                       # grouping key (see module docstring)
    started_at: datetime
    last_activity_at: datetime
    flow_count: int = 0
    classification: str = ""
    family: str = ""
    label: str = ""
    max_risk_score: float = -1.0
    max_risk_level: str = ""
    # tie-break for "highest risk" label: earliest seq wins.
    _best_seq: int = 10 ** 9
    source: str | None = None
    destination: str | None = None
    service_port: int | None = None

    def observe(self, *, label: str, risk_score: float, risk_level: str,
                seq: int) -> None:
        self.flow_count += 1
        if risk_score > self.max_risk_score or (
            risk_score == self.max_risk_score and seq < self._best_seq
        ):
            self.max_risk_score = risk_score
            self.max_risk_level = risk_level
            self.label = label
            self._best_seq = seq


@dataclass
class Assignment:
    """Result of feeding one flow to the grouper.

    ``incident`` is None for pure-BENIGN flows (no incident involvement).
    ``is_new`` is True when this flow opened a fresh incident (and possibly
    superseded an older one, which is available as ``superseded``).
    """

    incident: OpenGroup | None
    is_new: bool = False
    superseded: OpenGroup | None = None


class IncidentGrouper:
    """Deterministic grouping rules driven by replay-time order (PRD §14)."""

    def __init__(self, window_seconds: float) -> None:
        if window_seconds < 0:
            raise ValueError("grouping window must be >= 0")
        self.window_seconds = float(window_seconds)
        self._open: dict[tuple, OpenGroup] = {}
        self._next_id = 1
        self._run_seq = 0  # ordinal within the run (deterministic tie-break)

    # ------------------------------------------------------------------ #
    # pure helpers (unit-testable without state)
    # ------------------------------------------------------------------ #
    @staticmethod
    def is_suspicious(classification: str) -> bool:
        return classification in SUSPICIOUS

    @staticmethod
    def grouping_key(*, classification: str, family: str,
                     source: str | None, destination: str | None,
                     service_port: int | None) -> tuple | None:
        """Return the grouping key for a flow, or None when never grouped."""
        if classification not in SUSPICIOUS:
            return None
        key = (classification, family, source, destination)
        if family not in SCAN_FAMILIES:
            key = (*key, service_port)
        return key

    # ------------------------------------------------------------------ #
    # stateful API
    # ------------------------------------------------------------------ #
    def assign(
        self,
        *,
        classification: str,
        family: str,
        label: str,
        source: str | None,
        destination: str | None,
        service_port: int | None,
        replay_time: datetime,
        risk_score: float,
        risk_level: str,
    ) -> Assignment:
        """Decide incident membership for one replayed flow (in run order)."""
        self._run_seq += 1
        key = self.grouping_key(
            classification=classification, family=family,
            source=source, destination=destination,
            service_port=service_port,
        )
        if key is None:  # pure BENIGN -> never an incident
            return Assignment(incident=None)

        existing = self._open.get(key)
        if existing is not None and not self._expired(existing, replay_time):
            existing.observe(
                label=label, risk_score=risk_score, risk_level=risk_level,
                seq=self._run_seq,
            )
            existing.last_activity_at = replay_time
            return Assignment(incident=existing, is_new=False)

        # No open group or the window elapsed -> open a new incident.
        superseded = existing if existing is not None else None
        group = OpenGroup(
            group_id=self._next_id,
            key=key,
            started_at=replay_time,
            last_activity_at=replay_time,
            classification=classification,
            family=family,
            label=label,
            source=source,
            destination=destination,
            service_port=service_port,
        )
        group.observe(
            label=label, risk_score=risk_score, risk_level=risk_level,
            seq=self._run_seq,
        )
        self._next_id += 1
        self._open[key] = group
        return Assignment(incident=group, is_new=True, superseded=superseded)

    def _expired(self, group: OpenGroup, now: datetime) -> bool:
        if self.window_seconds == 0:
            return False  # 0 = never expire by time; only superseded on new key
        return (now - group.started_at).total_seconds() > self.window_seconds

    def close_all(self) -> list[OpenGroup]:
        """Close every remaining open group (replay run finished/stopped)."""
        closed = list(self._open.values())
        self._open.clear()
        return closed

    @property
    def open_count(self) -> int:
        return len(self._open)

    def snapshot(self) -> list[OpenGroup]:
        return sorted(self._open.values(), key=lambda g: g.group_id)