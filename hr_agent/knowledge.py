"""Mock HR data and policy knowledge base.

Everything here is static and deterministic on purpose: the agent's tools read
from these dicts so that, given the same inputs, the agent produces the same
tool outputs every run. Deterministic tools make evaluations reproducible —
you're measuring the *model's* behavior, not flaky downstream systems.
"""

from __future__ import annotations

# --- Employee directory --------------------------------------------------

# Keyed by lowercase full name for simple lookups.
EMPLOYEES: dict[str, dict] = {
    "jordan lee": {
        "employee_id": "E1007",
        "full_name": "Jordan Lee",
        "title": "Software Engineer",
        "department": "Engineering",
        "start_date": "2026-06-15",
        "manager": "Priya Anand",
        "benefits_plan": "standard",
    },
    "sam rivera": {
        "employee_id": "E1008",
        "full_name": "Sam Rivera",
        "title": "Product Designer",
        "department": "Design",
        "start_date": "2026-06-22",
        "manager": "Dana Kim",
        "benefits_plan": "standard",
    },
    "alex chen": {
        "employee_id": "E1009",
        "full_name": "Alex Chen",
        "title": "Engineering Manager",
        "department": "Engineering",
        "start_date": "2026-07-01",
        "manager": "Morgan Doyle",
        "benefits_plan": "executive",
    },
}


# --- HR policy knowledge base -------------------------------------------

# Keyed by topic. These are the "ground truth" facts the agent should cite
# when answering policy questions. Single-turn evals check the agent's answer
# against these.
HR_POLICIES: dict[str, str] = {
    "vacation": (
        "New full-time employees accrue 15 paid vacation days (PTO) per year, "
        "accruing at 1.25 days per month. PTO begins accruing on the employee's "
        "start date and can be used after the 90-day probationary period."
    ),
    "sick_leave": (
        "Employees receive 10 paid sick days per calendar year. Sick days do "
        "not roll over to the following year and cannot be cashed out."
    ),
    "remote_work": (
        "The company follows a hybrid policy: employees are expected on-site "
        "Tuesday, Wednesday, and Thursday, and may work remotely on Monday and "
        "Friday. Fully-remote arrangements require VP approval."
    ),
    "health_insurance": (
        "Health, dental, and vision coverage begin on the first day of the "
        "month following the start date. Employees have 30 days from their "
        "start date to enroll or make changes."
    ),
    "401k": (
        "The company offers a 401(k) with a 4% match. Employees are eligible "
        "to enroll after 60 days of employment. The company match vests "
        "immediately."
    ),
    "parental_leave": (
        "Parental leave provides 12 weeks of paid leave for the primary "
        "caregiver and 6 weeks for the secondary caregiver, available after "
        "6 months of employment."
    ),
    "expenses": (
        "Business expenses must be submitted within 30 days via the expense "
        "portal. Receipts are required for any expense over $25. Reimbursement "
        "is issued in the next payroll cycle after approval."
    ),
}


# --- Benefits plans ------------------------------------------------------

BENEFITS_PLANS: dict[str, dict] = {
    "standard": {
        "health": "PPO medical, dental, vision",
        "401k_match": "4%",
        "pto_days": 15,
        "equity": "RSU grant per offer letter",
    },
    "executive": {
        "health": "PPO medical, dental, vision + executive health program",
        "401k_match": "6%",
        "pto_days": 20,
        "equity": "RSU grant + annual refresh",
    },
}


# Systems an IT account can be created for. Used to validate tool arguments.
VALID_IT_SYSTEMS = {"email", "slack", "github", "vpn", "hris"}

# Equipment the company provisions.
VALID_EQUIPMENT = {"laptop", "monitor", "keyboard", "headset", "phone"}
