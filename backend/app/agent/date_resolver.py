from datetime import date, timedelta


def resolve_tomorrow(reference_date: date) -> date:
    return reference_date + timedelta(days=1)