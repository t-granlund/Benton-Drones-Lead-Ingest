from __future__ import annotations

from dataclasses import dataclass

from lead_ingest.geo import haversine_miles
from lead_ingest.models import LeadPoint


@dataclass(frozen=True)
class ClusterResult:
    center: LeadPoint
    members: tuple[LeadPoint, ...]
    radius_miles: float


def cluster_by_radius(points: list[LeadPoint], radius_miles: float) -> list[ClusterResult]:
    remaining = points[:]
    clusters: list[ClusterResult] = []

    while remaining:
        center = remaining.pop(0)
        members = [center]
        still_remaining: list[LeadPoint] = []

        for candidate in remaining:
            distance = haversine_miles(
                center.latitude,
                center.longitude,
                candidate.latitude,
                candidate.longitude,
            )
            if distance <= radius_miles:
                members.append(candidate)
            else:
                still_remaining.append(candidate)

        clusters.append(ClusterResult(center=center, members=tuple(members), radius_miles=radius_miles))
        remaining = still_remaining

    return clusters
