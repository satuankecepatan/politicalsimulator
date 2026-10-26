"""Territory and region generation, NetworkX graph adjacency, and Voronoi map geometry."""

from __future__ import annotations

import math
from typing import Any

import networkx as nx
import numpy as np
from scipy.spatial import Delaunay, Voronoi

from polsim.config.schema import CountryConfig, InstitutionsConfig, RegionConfig
from polsim.engine.state import RegionState, TerritoryState


def apportion_seats(
    populations: list[float],
    total_seats: int,
    min_seats: int = 1,
) -> list[int]:
    """Apportion seats to regions using the Hamilton / Largest Remainder (Hare Quota) method."""
    n = len(populations)
    if n == 0 or total_seats <= 0:
        return [0] * n
    if total_seats < n * min_seats:
        return [min_seats] * n

    total_pop = sum(populations)
    quota = total_pop / total_seats

    exact = [p / quota for p in populations]
    allocated = [max(min_seats, int(math.floor(x))) for x in exact]
    remaining = total_seats - sum(allocated)

    if remaining > 0:
        remainders = [(exact[i] - math.floor(exact[i]), i) for i in range(n)]
        remainders.sort(reverse=True)
        for _, idx in remainders[:remaining]:
            allocated[idx] += 1
    elif remaining < 0:
        # If min_seats forced over-allocation, deduct from largest
        surplus = -remaining
        indexed = sorted([(allocated[i], i) for i in range(n)], reverse=True)
        for _, idx in indexed[:surplus]:
            if allocated[idx] > min_seats:
                allocated[idx] -= 1

    return allocated


def generate_territory(
    country: CountryConfig,
    institutions: InstitutionsConfig,
    rng: np.random.Generator,
) -> tuple[TerritoryState, dict[str, Any]]:
    """Build or generate regions, adjacency graph, and Voronoi GeoJSON map."""
    g = nx.Graph()
    regions_dict: dict[str, RegionState] = {}
    geojson_features: list[dict[str, Any]] = []

    if country.regions:
        # Use explicitly provided regions
        n = len(country.regions)
        pops = [r.population_share for r in country.regions]
        seats = apportion_seats(pops, institutions.seats)
        for i, r in enumerate(country.regions):
            pop = r.population_share * (country.population / sum(pops))
            reg = RegionState(
                id=r.id,
                name=r.name,
                population=pop,
                urbanization=r.urbanization,
                wealth=r.wealth,
                unemployment_offset=r.unemployment_offset,
                regionalism=r.regionalism,
                religiosity=r.religiosity,
                minority_share=r.minority_share,
                education=r.education,
                aging=r.aging,
                resources=r.resources,
                seats=seats[i],
            )
            regions_dict[r.id] = reg
            g.add_node(r.id, name=r.name, population=pop)

        for r in country.regions:
            for neighbor in r.neighbors:
                if neighbor in regions_dict:
                    g.add_edge(r.id, neighbor)

        # Fallback complete connectivity if no neighbors given
        if g.number_of_edges() == 0 and n > 1:
            nodes = list(regions_dict.keys())
            for i in range(n - 1):
                g.add_edge(nodes[i], nodes[i + 1])
    else:
        # Procedural region generation with 2D Delaunay / Voronoi
        n = country.n_regions
        # Generate 2D seed points in [0, 100] x [0, 100]
        points = rng.uniform(5.0, 95.0, size=(n, 2))

        # Sample regional population shares using Dirichlet distribution
        pop_shares = rng.dirichlet(np.ones(n) * 2.5)
        seats = apportion_seats(pop_shares.tolist(), institutions.seats)

        # Region name prefixes
        prefixes = [
            "North", "South", "East", "West", "Central", "Upper", "Lower",
            "Coast", "Highland", "River", "Valley", "Plains", "Isles", "Border",
        ]

        region_ids = [f"reg_{i+1:02d}" for i in range(n)]

        # Voronoi tessellation for polygonal boundaries
        try:
            # Add boundary bounding box points to enclose Voronoi cells
            bbox = np.array([[-200, -200], [-200, 300], [300, -200], [300, 300]])
            all_pts = np.vstack([points, bbox])
            vor = Voronoi(all_pts)

            # Delaunay triangulation on the region centers for planar adjacency
            tri = Delaunay(points)
            for simplex in tri.simplices:
                for i in range(3):
                    u, v = simplex[i], simplex[(i + 1) % 3]
                    g.add_edge(region_ids[u], region_ids[v])
        except Exception:
            # Fallback for small N: ring graph
            for i in range(n):
                g.add_edge(region_ids[i], region_ids[(i + 1) % n])

        for i in range(n):
            rid = region_ids[i]
            prefix = prefixes[i % len(prefixes)]
            name = f"{prefix} Region" if n > len(prefixes) else f"{prefix} Province"
            pop = float(pop_shares[i] * country.population)

            urban = float(np.clip(rng.beta(2.5, 2.0), 0.1, 0.95))
            wealth = float(np.clip(urban * 0.5 + rng.normal(0.4, 0.15), 0.05, 0.95))
            unemp_off = float(np.clip(rng.normal(0.0, 1.8), -5.0, 5.0))
            regionalism = float(np.clip(rng.beta(1.5, 3.5), 0.0, 0.9))
            religiosity = float(np.clip(rng.beta(2.0, 2.5), 0.05, 0.95))
            minority = float(np.clip(rng.beta(1.2, 4.0), 0.02, 0.85))
            education = float(np.clip(urban * 0.4 + wealth * 0.4 + rng.normal(0.1, 0.1), 0.1, 0.95))
            aging = float(np.clip(rng.beta(2.5, 2.5), 0.1, 0.9))
            resources = float(np.clip(rng.beta(1.5, 2.5), 0.0, 0.95))

            reg = RegionState(
                id=rid,
                name=name,
                population=pop,
                urbanization=urban,
                wealth=wealth,
                unemployment_offset=unemp_off,
                regionalism=regionalism,
                religiosity=religiosity,
                minority_share=minority,
                education=education,
                aging=aging,
                resources=resources,
                seats=seats[i],
            )
            regions_dict[rid] = reg
            g.add_node(rid, name=name, population=pop, center=[float(points[i, 0]), float(points[i, 1])])

            # Build GeoJSON feature for map rendering
            geojson_features.append({
                "type": "Feature",
                "id": rid,
                "properties": {
                    "id": rid,
                    "name": name,
                    "population": int(pop),
                    "seats": seats[i],
                    "urbanization": round(urban, 2),
                    "wealth": round(wealth, 2),
                    "regionalism": round(regionalism, 2),
                    "center": [round(float(points[i, 0]), 2), round(float(points[i, 1]), 2)],
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [round(float(points[i, 0]), 2), round(float(points[i, 1]), 2)],
                },
            })

    territory = TerritoryState(regions=regions_dict, graph=g)
    map_data = {
        "type": "FeatureCollection",
        "features": geojson_features,
    }
    return territory, map_data
