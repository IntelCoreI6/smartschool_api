from datetime import date

from smartschool import FutureTasks


def test_future_tasks_normal_flow():
    """Note to self: for the "text": enclose the XHR with single quotes, and make it a raw string. No further processing needed."""
    x: FutureTasks = FutureTasks()

    assert x.days[0].date == date(2023, 11, 16)
    assert x.days[0].courses[0].course_title == "2 - AAR1, Lotte Peeters"
    assert x.days[0].courses[0].items.materials == []
    assert x.days[0].courses[0].items.tasks[0].assignmentID == "549556"
    assert x.days[0].courses[0].items.tasks[0].description == "Toets 3. De koolstofcyclus in het systeem aarde pagina 42 - 47"
