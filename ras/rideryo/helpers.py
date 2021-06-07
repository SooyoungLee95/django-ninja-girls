from uuid import uuid4


def generate_event_id():
    return f"ras:{uuid4()}"
