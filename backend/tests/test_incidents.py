"""test_incidents.py — Deterministic incident grouping rules (Phase 3, PRD §14).

Unit-testing the pure grouping engine (no DB, no predictor, no threads).
Windows are in seconds; replay_time = deterministic synthetic epoch datetimes
(datetime.fromtimestamp) so tests never touch real time.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from backend.app.services.incidents import (
    BENIGN,
    IncidentGrouper,
    SCAN_FAMILIES,
)

T0 = datetime.fromtimestamp(1_700_000_000, tz=timezone.utc)


def _dt(offset: float) -> datetime:
    return T0 + timedelta(seconds=offset)


def _flow(grouper, *, seq_ts, cls="KNOWN_ATTACK", family="Denial of Service",
          label="DoS Hulk", source="10.0.0.5", destination="10.0.0.9",
          port=80, risk=90.0, level="CRITICAL"):
    return grouper.assign(
        classification=cls, family=family, label=label,
        source=source, destination=destination, service_port=port,
        replay_time=_dt(seq_ts), risk_score=risk, risk_level=level,
    )


def test_scan_families_excludes_port_from_key():
    """service_port must NOT be a discriminator for scanning families, so a
    PortScan across many ports stays ONE incident (the 'where meaningful' rule)."""
    assert "Reconnaissance" in SCAN_FAMILIES
    g = IncidentGrouper(window_seconds=60)
    a = g.grouping_key(classification="KNOWN_ATTACK", family="Reconnaissance",
                       source="s", destination="d", service_port=443)
    b = g.grouping_key(classification="KNOWN_ATTACK", family="Reconnaissance",
                       source="s", destination="d", service_port=22)
    assert a == b


def test_service_port_in_key_for_non_scanning_family():
    """For a non-scanning family, different service ports ARE separate
    (distinct services on distinct ports)."""
    g = IncidentGrouper(window_seconds=60)
    a = g.grouping_key(classification="KNOWN_ATTACK", family="Brute Force",
                       source="s", destination="d", service_port=22)
    b = g.grouping_key(classification="KNOWN_ATTACK", family="Brute Force",
                       source="s", destination="d", service_port=80)
    assert a != b


def test_benign_flows_never_create_an_incident():
    g = IncidentGrouper(window_seconds=60)
    assign = g.assign(
        classification=BENIGN, family=BENIGN, label=BENIGN,
        source="10.0.0.8", destination="10.0.0.9", service_port=443,
        replay_time=_dt(0), risk_score=5.0, risk_level="LOW",
    )
    assert assign.incident is None
    assert not assign.is_new
    assert g.open_count == 0


def test_unknown_suspicious_starts_an_incident():
    g = IncidentGrouper(window_seconds=60)
    assign = _flow(g, seq_ts=0, cls="UNKNOWN_SUSPICIOUS", family=BENIGN,
                   label=BENIGN, port=53, risk=72.9, level="HIGH")
    assert assign.incident is not None
    assert assign.is_new
    assert assign.incident.classification == "UNKNOWN_SUSPICIOUS"


def test_related_flows_within_window_join_same_incident():
    g = IncidentGrouper(window_seconds=30)
    first = _flow(g, seq_ts=0)
    second = _flow(g, seq_ts=10)
    assert first.is_new
    assert not second.is_new
    assert second.incident.group_id == first.incident.group_id
    assert second.incident.flow_count == 2


def test_flow_outside_window_opens_new_incident():
    g = IncidentGrouper(window_seconds=30)
    first = _flow(g, seq_ts=0)
    late = _flow(g, seq_ts=60)
    assert late.is_new
    assert late.incident.group_id != first.incident.group_id


def test_window_boundary_delta_equals_window_still_joins():
    """delta == grouping_window_seconds is INCLUSIVE: a flow arriving exactly
    at the boundary joins the same incident (only delta > window supersedes)."""
    g = IncidentGrouper(window_seconds=30)
    first = _flow(g, seq_ts=0)
    boundary = _flow(g, seq_ts=30)  # delta == window -> joins
    assert not boundary.is_new
    assert boundary.incident.group_id == first.incident.group_id
    assert boundary.incident.flow_count == 2

    beyond = _flow(g, seq_ts=30.000001)  # delta just over -> supersedes
    assert beyond.is_new
    assert beyond.incident.group_id != first.incident.group_id
    assert beyond.superseded is not None
    assert beyond.superseded.group_id == first.incident.group_id


def test_different_family_is_separate_incident():
    g = IncidentGrouper(window_seconds=60)
    a = _flow(g, seq_ts=0, family="Denial of Service", label="DoS Hulk")
    b = _flow(g, seq_ts=1, family="Brute Force", label="SSH-Patator", port=22)
    assert a.incident.group_id != b.incident.group_id


def test_different_source_is_separate_incident():
    g = IncidentGrouper(window_seconds=60)
    a = _flow(g, seq_ts=0, source="10.0.0.5")
    b = _flow(g, seq_ts=1, source="10.0.0.6")
    assert a.incident.group_id != b.incident.group_id


def test_different_destination_is_separate_incident():
    g = IncidentGrouper(window_seconds=60)
    a = _flow(g, seq_ts=0, destination="10.0.0.9")
    b = _flow(g, seq_ts=1, destination="10.0.0.10")
    assert a.incident.group_id != b.incident.group_id


def test_portscan_many_ports_single_incident():
    g = IncidentGrouper(window_seconds=60)
    first = None
    for i, port in enumerate((20, 21, 22, 23, 80, 443, 3389, 8080)):
        assign = _flow(g, seq_ts=float(i), family="Reconnaissance", label="PortScan",
                       port=port, risk=50.0, level="MEDIUM")
        if first is None:
            first = assign
        assert assign.incident is not None
    assert g.open_count == 1
    assert first.incident.flow_count == 8


def test_incident_aggregates_flow_count_first_last_max_risk():
    g = IncidentGrouper(window_seconds=60)
    _flow(g, seq_ts=0, risk=40.0, level="MEDIUM")
    _flow(g, seq_ts=5, risk=65.0, level="HIGH")
    _flow(g, seq_ts=10, risk=92.0, level="CRITICAL")
    inc = g.snapshot()[0]
    assert inc.flow_count == 3
    assert inc.started_at == _dt(0)
    assert inc.last_activity_at == _dt(10)
    assert inc.max_risk_score == 92.0
    assert inc.max_risk_level == "CRITICAL"


def test_superseded_incident_is_closed_and_reported():
    g = IncidentGrouper(window_seconds=30)
    first = _flow(g, seq_ts=0)
    late = _flow(g, seq_ts=60)
    assert late.is_new
    assert late.superseded is not None
    assert late.superseded.group_id == first.incident.group_id


def test_close_all_empties_open_groups():
    g = IncidentGrouper(window_seconds=60)
    _flow(g, seq_ts=0)
    _flow(g, seq_ts=1)
    closed = g.close_all()
    assert len(closed) == 1
    assert g.open_count == 0


def test_deterministic_group_ids_for_same_input_sequence():
    def run():
        g = IncidentGrouper(window_seconds=30)
        ids = []
        for ts, port in ((0, 80), (1, 80), (2, 80)):
            a = _flow(g, seq_ts=ts, port=port)
            ids.append(a.incident.group_id if a.incident else None)
        return ids
    assert run() == run()


def test_zero_window_never_expires():
    """window=0 means 'no time expiry' — same key keeps joining."""
    g = IncidentGrouper(window_seconds=0)
    first = _flow(g, seq_ts=0)
    late = _flow(g, seq_ts=10_000)
    assert not late.is_new
    assert late.incident.group_id == first.incident.group_id


def test_negative_window_rejected():
    with pytest.raises(ValueError):
        IncidentGrouper(window_seconds=-1)