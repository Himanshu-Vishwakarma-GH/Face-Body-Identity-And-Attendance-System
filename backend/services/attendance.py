import time
import logging
from typing import List, Dict, Any, Optional

from backend.models import DepartmentAttendance
from backend.database import db

logger = logging.getLogger("ai_access.attendance")

def calculate_department_attendance(day_start_timestamp: Optional[float] = None) -> List[DepartmentAttendance]:
    """Aggregates attendance metrics per department for the current day."""
    now = time.time()
    cutoff = day_start_timestamp or (now - 86400)

    # 1. Total active employees per department
    emp_records = db.get_all_by_pattern("emp:*")
    dept_totals: Dict[str, int] = {}

    for emp in emp_records:
        if emp and emp.get("is_active", True):
            dept = emp.get("department", "General")
            dept_totals[dept] = dept_totals.get(dept, 0) + 1

    # 2. Count distinct present employees today per department
    log_records = db.get_all_by_pattern("log:*")
    dept_present_set: Dict[str, set] = {}

    for entry in log_records:
        if not entry:
            continue
        ts = entry.get("timestamp", 0)
        if ts >= cutoff and entry.get("decision") in ["GRANTED", "WARNING"] and entry.get("employee_id"):
            dept = entry.get("department", "General")
            emp_id = entry.get("employee_id")
            if dept not in dept_present_set:
                dept_present_set[dept] = set()
            dept_present_set[dept].add(emp_id)

    # 3. Form statistics response
    stats: List[DepartmentAttendance] = []
    for dept, total in sorted(dept_totals.items()):
        present_count = len(dept_present_set.get(dept, set()))
        present_count = min(present_count, total)
        pct = round((present_count / total * 100), 1) if total > 0 else 0.0

        stats.append(DepartmentAttendance(
            department=dept,
            present_count=present_count,
            total_count=total,
            percentage=pct
        ))

    return stats
