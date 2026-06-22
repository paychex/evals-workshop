"""Tools for the HR Onboarding agent.

These are intentionally simple and deterministic. They read from the static
data in ``knowledge.py`` and derive IDs from their inputs, so the same call
always returns the same result. That reproducibility is what makes the
agent's *trajectory* (the sequence of tool calls) something we can evaluate.
"""

from __future__ import annotations

from langchain_core.tools import tool

from hr_agent.knowledge import (
    BENEFITS_PLANS,
    EMPLOYEES,
    HR_POLICIES,
    VALID_EQUIPMENT,
    VALID_IT_SYSTEMS,
)


@tool
def lookup_employee(name: str) -> dict:
    """Look up a new hire's record by full name.

    Returns the employee's id, title, department, start date, manager, and
    benefits plan. Call this first when you need an employee_id for other
    onboarding actions.
    """
    record = EMPLOYEES.get(name.strip().lower())
    if record is None:
        return {"error": f"No employee found with name '{name}'."}
    return record


@tool
def lookup_hr_policy(topic: str) -> str:
    """Look up official HR policy text for a topic.

    Valid topics: vacation, sick_leave, remote_work, health_insurance, 401k,
    parental_leave, expenses. Use the returned text to ground your answer —
    do not invent policy details.
    """
    key = topic.strip().lower().replace(" ", "_").replace("-", "_")
    policy = HR_POLICIES.get(key)
    if policy is None:
        return (
            f"No policy found for '{topic}'. Available topics: "
            + ", ".join(sorted(HR_POLICIES))
        )
    return policy


@tool
def get_benefits_info(plan: str) -> dict:
    """Get the benefits details for a plan ('standard' or 'executive')."""
    info = BENEFITS_PLANS.get(plan.strip().lower())
    if info is None:
        return {"error": f"Unknown plan '{plan}'. Choose 'standard' or 'executive'."}
    return info


@tool
def create_it_account(employee_id: str, system: str) -> dict:
    """Provision an IT account for an employee on a given system.

    Valid systems: email, slack, github, vpn, hris. Requires a valid
    employee_id (get it from lookup_employee first).
    """
    system = system.strip().lower()
    if system not in VALID_IT_SYSTEMS:
        return {"error": f"Invalid system '{system}'. Valid: {sorted(VALID_IT_SYSTEMS)}"}
    # Deterministic, human-readable confirmation id derived from the inputs.
    account_id = f"ACCT-{employee_id}-{system.upper()}"
    return {
        "status": "created",
        "account_id": account_id,
        "employee_id": employee_id,
        "system": system,
    }


@tool
def provision_equipment(employee_id: str, equipment_type: str) -> dict:
    """Request standard equipment for a new hire.

    Valid equipment_type: laptop, monitor, keyboard, headset, phone.
    """
    equipment_type = equipment_type.strip().lower()
    if equipment_type not in VALID_EQUIPMENT:
        return {
            "error": f"Invalid equipment '{equipment_type}'. Valid: {sorted(VALID_EQUIPMENT)}"
        }
    ticket_id = f"EQ-{employee_id}-{equipment_type.upper()}"
    return {
        "status": "ordered",
        "ticket_id": ticket_id,
        "employee_id": employee_id,
        "equipment_type": equipment_type,
    }


@tool
def schedule_orientation(employee_id: str, date: str) -> dict:
    """Schedule a new-hire orientation session for an employee on a date (YYYY-MM-DD)."""
    confirmation = f"ORI-{employee_id}-{date.replace('-', '')}"
    return {
        "status": "scheduled",
        "confirmation_id": confirmation,
        "employee_id": employee_id,
        "date": date,
    }


# The full toolset exposed to the agent. Import this in agent.py.
HR_TOOLS = [
    lookup_employee,
    lookup_hr_policy,
    get_benefits_info,
    create_it_account,
    provision_equipment,
    schedule_orientation,
]
