from __future__ import annotations

import time
from typing import TYPE_CHECKING, ClassVar

from ._xml_interface import SmartschoolXML
from .objects import AgendaHour, AgendaLesson, AgendaMomentInfo

if TYPE_CHECKING:
    from datetime import date


class SmartschoolLessons(SmartschoolXML):
    """
    Interface to the retrieval of lessons for a certain date.

    To reproduce: open the agenda, one of the XHR calls is this one.

    This includes (for an example check the tests):
    - momentID: a unique identifier for this specific lesson
    - lessonID: a group id
    - hourID: link to `AgendaHours`
    - date: YYYY-mm-dd
    - subject: explanation by the teacher
    - course
    - courseTitle
    - classroom: what classroom this is in
    - classroomTitle: same as `classroom`?
    - teacher: name of the teacher (Lastname + initial of firstname)
    - teacherTitle:
    - klassen
    - klassenTitle
    - classIDs
    - bothStartStatus
    - assignmentEndStatus
    - testDeadlineStatus
    - noteStatus
    - note
    - date_listview
    - hour
    - activity
    - activityID
    - color
    - hourValue
    - components_hidden
    - freedayIcon
    - someSubjectsEmpty
    """

    cache: ClassVar[dict[str, list[SmartschoolLessons]]] = {}

    @property
    def _xpath(self) -> str:
        return ".//lesson"

    @property
    def _object_to_instantiate(self) -> type[AgendaLesson]:
        return AgendaLesson

    @property
    def _subsystem(self) -> str:
        return "agenda"

    @property
    def _action(self) -> str:
        return "get lessons"

    @property
    def _params(self) -> dict:
        now = int(time.time())
        in_5_days = now + 5 * 24 * 3600

        return {
            "startDateTimestamp": now,  # 1700045313
            "endDateTimestamp": in_5_days,  # 1700477313
            "filterType": "false",
            "filterID": "false",
            "gridType": "1",
            "classID": "0",
            "endDateTimestampOld": in_5_days,  # 1700477313
            "forcedTeacher": "0",
            "forcedClass": "0",
            "forcedClassroom": "0",
            "assignmentTypeID": "1",
        }


class SmartschoolHours(SmartschoolXML):
    """
    Interface to the retrieval of periods (called Hours in smartschool).

    To reproduce: open the agenda, one of the XHR calls is this one.

    This includes (for an example check the tests):
    - hourID: unique identifier for this period
    - start: HH:MM starting time
    - end: HH:MM ending time
    - title: how it is called in the agenda
    """

    cache: ClassVar[dict[str, list[SmartschoolHours]]] = {}

    @property
    def _xpath(self) -> str:
        return ".//hour"

    @property
    def _object_to_instantiate(self) -> type[AgendaHour]:
        return AgendaHour

    @property
    def _subsystem(self) -> str:
        return "grid"

    @property
    def _action(self) -> str:
        return "get hours"

    @property
    def _params(self) -> dict:
        return {"date": int(time.time())}

    def search_by_hourId(self, hourId: str, *, date_to_use: date | None = None):
        for hour in self._xml(date_to_use):
            if hour.hourID == hourId:
                return hour

        raise ValueError(f"Couldn't find {hourId}")


class SmartschoolMomentInfos(SmartschoolXML):
    """
    Interface to the retrieval of one particular moment (a book-symbol in smartschool).

    To reproduce: open the agenda, click on a yellow/red book. This is the XHR call that appears.

    This includes (for an example check the tests):
    - hourID: unique identifier for this period
    - start: HH:MM starting time
    - end: HH:MM ending time
    - title: how it is called in the agenda
    """

    cache: ClassVar[dict[str, list[AgendaMomentInfo]]] = {}

    def __init__(self, moment_id: str):
        moment_id = str(moment_id).strip()
        if not moment_id:
            raise ValueError("Please provide a valid MomentID")

        self._moment_id = moment_id

    @property
    def _xpath(self) -> str:
        return ".//class"

    @property
    def _object_to_instantiate(self) -> type[AgendaMomentInfo]:
        return AgendaMomentInfo

    @property
    def _subsystem(self) -> str:
        return "agenda"

    @property
    def _action(self) -> str:
        return "get moment info"

    @property
    def _params(self) -> dict:
        return {
            "momentID": self._moment_id,
            "dateID": "",
            "assignmentIDs": "",
            "activityID": "0",
        }

    def _post_process_element(self, element: dict) -> None:
        """In this XML we have `assignments.assignment`, but I don't need that `assignment` tag."""
        if element["assignments"] is None:
            element["assignments"] = []
            return

        if isinstance(element["assignments"]["assignment"], list):
            element["assignments"] = element["assignments"]["assignment"]
        else:
            element["assignments"] = [element["assignments"]["assignment"]]
