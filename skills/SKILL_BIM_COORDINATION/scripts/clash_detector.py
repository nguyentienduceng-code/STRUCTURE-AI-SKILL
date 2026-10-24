#!/usr/bin/env python3
"""
clash_detector.py — BIM Clash Detection Engine

Detects spatial conflicts between BIM elements from IFC data.

Usage:
    python clash_detector.py --ifc model.ifc [--tolerance 50] [--output clashes.json]

Output: JSON with clash results
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import json
import math
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Optional
from datetime import datetime


@dataclass
class ClashResult:
    clash_id: str
    clash_type: str  # HARD | SOFT | CLEARANCE
    severity: str     # CRITICAL | HIGH | MEDIUM | LOW

    element1: Dict
    element2: Dict

    location: Dict  # x, y, z coordinates
    distance_mm: float  # negative if hard clash
    tolerance_mm: float

    description: str
    recommendation: str


class BoundingBox:
    """Axis-aligned bounding box for clash detection"""

    def __init__(self, min_x: float, min_y: float, min_z: float,
                 max_x: float, max_y: float, max_z: float):
        self.min = (min_x, min_y, min_z)
        self.max = (max_x, max_y, max_z)

    def overlaps(self, other: 'BoundingBox', tolerance: float = 0) -> bool:
        """Check if two bounding boxes overlap (with tolerance)"""
        tolerance_mm = tolerance

        return (
            self.min[0] - tolerance_mm <= other.max[0] and
            self.max[0] + tolerance_mm >= other.min[0] and
            self.min[1] - tolerance_mm <= other.max[1] and
            self.max[1] + tolerance_mm >= other.min[1] and
            self.min[2] - tolerance_mm <= other.max[2] and
            self.max[2] + tolerance_mm >= other.min[2]
        )

    def distance_to(self, other: 'BoundingBox') -> float:
        """Calculate minimum distance between two bounding boxes"""
        dx = max(0, max(self.min[0] - other.max[0], other.min[0] - self.max[0]))
        dy = max(0, max(self.min[1] - other.max[1], other.min[1] - self.max[1]))
        dz = max(0, max(self.min[2] - other.max[2], other.min[2] - self.max[2]))
        return math.sqrt(dx**2 + dy**2 + dz**2)

    def center(self) -> Tuple[float, float, float]:
        """Get center point of bounding box"""
        return (
            (self.min[0] + self.max[0]) / 2,
            (self.min[1] + self.max[1]) / 2,
            (self.min[2] + self.max[2]) / 2
        )

    def to_dict(self) -> dict:
        return {
            "min": list(self.min),
            "max": list(self.max),
            "center": list(self.center())
        }


class ClashDetector:
    """BIM Clash Detection Engine"""

    # Clash type classifications
    DISCIPLINES = {
        "STRUCTURE": ["Beam", "Column", "Slab", "Wall", "Foundation", "Stair", "Ramp"],
        "ARCHITECTURE": ["Door", "Window", "CurtainWall", "Space", "Stair", "Railing"],
        "HVAC": ["Duct", "Pipe", "Fitting", "Equipment", "AirTerminal", "Boiler", "Chiller"],
        "PLUMBING": ["Pipe", "Fitting", "Equipment", "WaterHeater", "Tank", "Pump"],
        "ELECTRICAL": ["CableTray", "Conduit", "Busbar", "Equipment", "LightFixture", "Panel"],
        "FIRE_PROTECTION": ["Pipe", "Sprinkler", "Fitting", "Equipment", "Valve"],
    }

    # Clearance requirements (mm)
    CLEARANCE_REQUIREMENTS = {
        ("ELECTRICAL", "HVAC"): 100,
        ("ELECTRICAL", "PLUMBING"): 100,
        ("HVAC", "PLUMBING"): 50,
        ("FIRE_PROTECTION", "HVAC"): 100,
        ("FIRE_PROTECTION", "ELECTRICAL"): 50,
        ("STRUCTURE", "HVAC"): 50,
        ("STRUCTURE", "ELECTRICAL"): 25,
        ("STRUCTURE", "PLUMBING"): 25,
    }

    def __init__(self, tolerance_mm: float = 50):
        """
        Initialize clash detector.

        Args:
            tolerance_mm: Clash detection tolerance
        """
        self.tolerance = tolerance_mm
        self.elements: Dict[str, List[Dict]] = {
            "STRUCTURE": [],
            "ARCHITECTURE": [],
            "HVAC": [],
            "PLUMBING": [],
            "ELECTRICAL": [],
            "FIRE_PROTECTION": [],
        }
        self.clashes: List[ClashResult] = []

    def add_element(self, element_type: str, name: str, bbox: BoundingBox,
                   properties: Optional[Dict] = None) -> None:
        """Add an element for clash detection"""
        discipline = self._get_discipline(element_type)
        if discipline:
            self.elements[discipline].append({
                "type": element_type,
                "name": name,
                "bbox": bbox,
                "properties": properties or {}
            })

    def _get_discipline(self, element_type: str) -> Optional[str]:
        """Determine discipline from element type"""
        element_type_upper = element_type.upper()
        for discipline, types in self.DISCIPLINES.items():
            if any(t.upper() in element_type_upper for t in types):
                return discipline
        return None

    def detect_clashes(self) -> List[ClashResult]:
        """Run clash detection on all elements"""
        self.clashes = []
        clash_id = 1

        disciplines = list(self.elements.keys())

        # Check all discipline pairs
        for i, disc1 in enumerate(disciplines):
            for disc2 in disciplines[i+1:]:
                clashes = self._check_discipline_pair(disc1, disc2)
                for elem1, elem2, distance, clash_type, severity in clashes:
                    center = elem1["bbox"].center()

                    # Generate recommendation
                    recommendation = self._generate_recommendation(
                        disc1, disc2, elem1, elem2, clash_type
                    )

                    self.clashes.append(ClashResult(
                        clash_id=f"CL{clash_id:04d}",
                        clash_type=clash_type,
                        severity=severity,
                        element1=self._element_to_dict(elem1),
                        element2=self._element_to_dict(elem2),
                        location={"x": center[0], "y": center[1], "z": center[2]},
                        distance_mm=distance,
                        tolerance_mm=self.tolerance,
                        description=f"{elem1['name']} vs {elem2['name']}",
                        recommendation=recommendation
                    ))
                    clash_id += 1

        return self.clashes

    def _check_discipline_pair(self, disc1: str, disc2: str) -> List[Tuple]:
        """Check for clashes between two disciplines"""
        clashes = []

        clearance = self.CLEARANCE_REQUIREMENTS.get(
            (disc1, disc2), self.CLEARANCE_REQUIREMENTS.get((disc2, disc1), 50)
        )

        for elem1 in self.elements[disc1]:
            for elem2 in self.elements[disc2]:
                bbox1, bbox2 = elem1["bbox"], elem2["bbox"]

                # Check for hard clash
                if bbox1.overlaps(bbox2, tolerance=self.tolerance):
                    clashes.append((
                        elem1, elem2, -10, "HARD", "CRITICAL"
                    ))
                else:
                    # Check for clearance clash
                    distance = bbox1.distance_to(bbox2)
                    if distance < clearance:
                        clashes.append((
                            elem1, elem2, distance, "CLEARANCE", "MEDIUM"
                        ))

        return clashes

    def _element_to_dict(self, elem: Dict) -> Dict:
        """Convert element to dictionary"""
        return {
            "type": elem["type"],
            "name": elem["name"],
            "bbox": elem["bbox"].to_dict(),
            "properties": elem.get("properties", {})
        }

    def _generate_recommendation(self, disc1: str, disc2: str,
                                  elem1: Dict, elem2: Dict,
                                  clash_type: str) -> str:
        """Generate clash resolution recommendation"""

        if clash_type == "HARD":
            if disc1 == "STRUCTURE" or disc2 == "STRUCTURE":
                return (
                    f"REVIEW REQUIRED: Structure involved. "
                    f"Consider relocating {elem1['type'] if disc1 != 'STRUCTURE' else elem2['type']}. "
                    f"Coordinated with {elem2['name'] if disc1 != 'STRUCTURE' else elem1['name']}."
                )
            else:
                return (
                    f"RELOCATE: Move {elem2['type'] if disc1 != 'HVAC' else elem1['type']} "
                    f"to avoid conflict with {elem1['name'] if disc1 != 'HVAC' else elem2['name']}."
                )
        else:
            return (
                f"VERIFY CLEARANCE: Ensure minimum {self.CLEARANCE_REQUIREMENTS.get((disc1, disc2), 50)}mm "
                f"clearance between {elem1['name']} and {elem2['name']}."
            )

    def get_summary(self) -> Dict:
        """Get clash summary statistics"""
        summary = {
            "total_clashes": len(self.clashes),
            "by_type": {},
            "by_severity": {},
            "by_discipline_pair": {},
        }

        for clash in self.clashes:
            # By type
            clash_type = clash.clash_type
            summary["by_type"][clash_type] = summary["by_type"].get(clash_type, 0) + 1

            # By severity
            severity = clash.severity
            summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1

            # By discipline pair
            disc1 = self._element_discipline(clash.element1)
            disc2 = self._element_discipline(clash.element2)
            pair = tuple(sorted([disc1, disc2]))
            pair_key = f"{pair[0]}-{pair[1]}"
            summary["by_discipline_pair"][pair_key] = summary["by_discipline_pair"].get(pair_key, 0) + 1

        return summary

    def _element_discipline(self, elem: Dict) -> str:
        """Get discipline from element"""
        elem_type = elem.get("type", "")
        for disc, types in self.DISCIPLINES.items():
            if any(t.upper() in elem_type.upper() for t in types):
                return disc
        return "UNKNOWN"

    def to_json(self) -> Dict:
        """Export to JSON"""
        return {
            "summary": self.get_summary(),
            "clashes": [asdict(c) for c in self.clashes],
            "metadata": {
                "tolerance_mm": self.tolerance,
                "timestamp": datetime.now().isoformat(),
                "element_count": sum(len(elems) for elems in self.elements.values())
            }
        }


def demo():
    """Demo with sample elements"""
    detector = ClashDetector(tolerance_mm=50)

    # Add structure elements
    detector.add_element("Beam", "B1-200x400",
        BoundingBox(0, 0, 2800, 6000, 200, 3200))
    detector.add_element("Column", "C1-400x400",
        BoundingBox(0, 0, 0, 400, 400, 3200))

    # Add MEP elements that clash
    detector.add_element("Duct", "DUCT-HVAC-01",
        BoundingBox(100, 50, 2700, 5100, 300, 3100))  # Clashes with beam

    detector.add_element("Pipe", "PIPE-DN100",
        BoundingBox(200, 100, 0, 300, 200, 3200))  # Near column

    detector.add_element("CableTray", "TRAY-ELEC-01",
        BoundingBox(500, 80, 2950, 5500, 150, 3050))  # Clearance issue

    # Run detection
    clashes = detector.detect_clashes()

    # Print summary
    print("\n" + "="*60)
    print("CLASH DETECTION RESULTS")
    print("="*60)

    summary = detector.get_summary()
    print(f"\nTotal clashes: {summary['total_clashes']}")

    print("\nBy Type:")
    for t, count in summary["by_type"].items():
        print(f"  {t}: {count}")

    print("\nBy Severity:")
    for s, count in summary["by_severity"].items():
        print(f"  {s}: {count}")

    print("\nBy Discipline Pair:")
    for p, count in summary["by_discipline_pair"].items():
        print(f"  {p}: {count}")

    print("\nDetailed Clashes:")
    for clash in clashes:
        print(f"\n  [{clash.clash_id}] {clash.clash_type} - {clash.severity}")
        print(f"    {clash.description}")
        print(f"    Distance: {clash.distance_mm:.1f} mm")
        print(f"    Recommendation: {clash.recommendation}")

    return detector


def main():
    import argparse

    parser = argparse.ArgumentParser(description="BIM Clash Detection")
    parser.add_argument("--ifc", help="IFC file path (not implemented - use demo)")
    parser.add_argument("--tolerance", type=float, default=50,
                       help="Clash tolerance in mm")
    parser.add_argument("--output", "-o", help="Output JSON file")

    args = parser.parse_args()

    # For demo purposes, use built-in sample data
    detector = demo()

    # Output JSON
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(detector.to_json(), f, indent=2, ensure_ascii=False)
        print(f"\n✓ Results written to {args.output}")

    # Exit code based on clash severity
    summary = detector.get_summary()
    if summary["by_severity"].get("CRITICAL", 0) > 0:
        sys.exit(2)  # Critical clashes
    elif summary["total_clashes"] > 0:
        sys.exit(1)  # Has clashes
    else:
        sys.exit(0)  # Clean


if __name__ == "__main__":
    main()
