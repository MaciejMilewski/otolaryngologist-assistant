from datetime import datetime
from sqlalchemy import and_, or_

from app.models import Schedule


def validate_event_collision(user_id, start_date, end_date, exclude_event_id=None):
    if isinstance(start_date, str):
        start_date = datetime.fromisoformat(start_date)
    if isinstance(end_date, str):
        end_date = datetime.fromisoformat(end_date)

    if end_date <= start_date:
        return False, "Data zakończenia musi być po dacie rozpoczęcia."

    if start_date < datetime.now():
        return False, "Nie można ustawić wydarzenia w przeszłości."

    overlapping_events = Schedule.query.filter(
        Schedule.user_id == user_id,
        Schedule.id != exclude_event_id,  # Wyklucza edytowany event
        Schedule.start_date <= end_date.date(),
        Schedule.end_date >= start_date.date(),
        (Schedule.start_time <= end_date.time()) & (Schedule.end_time >= start_date.time())
    ).all()

    if overlapping_events:
        return False, "Kolizja czasowa z innym wydarzeniem."

    return True, None
