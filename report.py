"""
Ticket Report for tdxplot
by Eric Edwards, Alex JPS
2023-06-30

Report class and methods for parsing and populating tickets
from the information in a given report.
"""

# Packages
import sys
import csv
import typing

# Files
from organization import *
from ticketclasses import *


# Constants
STANDARD_FIELDS = ["ID", "Title", "Resp Group", "Requestor", "Requestor Email", "Requestor Phone", "Acct/Dept",
                   "Class Support Building", "Room number", "Classroom Problem Types", "Created", "Modified", "Status"]
TIME_FORMATS: list[str] = [
    # 12 hour
    "%Y-%m-%d %H:%M", "%m/%d/%Y %H:%M", "%m/%d/%y %H:%M", "%d.%m.%Y %H:%M", "%d.%m.%y %H:%M",
    # 24 hour
    "%Y-%m-%d %I:%M %p", "%m/%d/%Y %I:%M %p", "%m/%d/%y %I:%M %p", "%d.%m.%Y %I:%M %p", "%d.%m.%y %I:%M %p"
]

class BadReportError(ValueError):
    """
    Exception class for errors from bad report.
    Currently extends ValueError.
    """
    pass


class Report:
    """
    Class for the given report and its properties.
    Deals with file I/O and reading CSV.
    """
    time_format: str
    fields_present: list[str]
    filename = str

    def __init__(self, filename: str):
        self.filename = filename
        # set fields present and time format
        csv_file: typing.TextIO = open(self.filename, mode="r", encoding="utf-8-sig")
        any_ticket: dict = next(csv.DictReader(csv_file))
        self.fields_present = get_fields_present(any_ticket)
        self.time_format = get_time_format(any_ticket)
        csv_file.close()

    def populate(self, org: Organization) -> None:
        """
        Given filename, read CSV.
        Populate buildings, rooms, tickets, etc. of given Organization.
        """
        csv_file: typing.TextIO = open(self.filename, mode="r", encoding="utf-8-sig")
        csv_tickets: csv.DictReader = csv.DictReader(csv_file)
        count: int = 0
        for row in csv_tickets:
            # fix row to be a valid, clean ticket dict
            self.clean_ticket_dict(row)
            org.add_new_ticket(row)
            count += 1
        csv_file.close()
        if not count:
            raise BadReportError("Ticket report is empty, exiting...")

    def clean_ticket_dict(self, csv_ticket: dict) -> None:
        """
        Given a dict representing a CSV row, convert to valid ticket dict.
        A valid ticket dict contains appropriate objects instead of strings
        (e.g. datetime for "Created" and "Modified", int for "ID")
        Except when those objects are specific to on-campus entities
        (e.g. Buildings, Users, and Groups are kept as strings)
        """
        # ID should be an int
        csv_ticket["ID"] = int(csv_ticket["ID"]) if csv_ticket.get("ID") else 0
        # Created and Modified should be datetime objects
        if csv_ticket.get("Created"):
            csv_ticket["Created"] = datetime.strptime(csv_ticket["Created"], self.time_format)
        if csv_ticket.get("Modified"):
            csv_ticket["Modified"] = datetime.strptime(csv_ticket["Modified"], self.time_format)
        # Classroom Problem Types should be Diagnosis Enums
        if csv_ticket.get("Classroom Problem Types"):
            diagnoses: list[Diagnosis] = []
            problem_types: list[str] = csv_ticket["Classroom Problem Types"].split(", ")
            for type in problem_types:
                valid: bool = True
                try:
                    diagnoses.append(Diagnosis(type))
                except ValueError:
                    valid = False
                if not valid:
                    raise BadReportError(f"Unknown Classroom Problem Type {type}")
            csv_ticket["Classroom Problem Types"] = diagnoses
        else:
            csv_ticket["Classroom Problem Types"] = []


# Helper functions
def get_fields_present(csv_ticket: dict) -> Union[list[str], None]:
    """
    Given an arbitrary csv_ticket dict from report,
    Check which of STANDARD_FIELDS are present in report.
    Set self.fields_present accordingly.
    """
    fields_present: list[str] = []
    for field in STANDARD_FIELDS:
        if csv_ticket.get(field) is not None:
            fields_present.append(field)
    if len(STANDARD_FIELDS) != len(fields_present):
        print("""Given report does not follow tdxplot Standard Report guidelines
Expect limited functionality due to missing ticket information""", file=sys.stderr)
    return fields_present


def get_time_format(csv_ticket: dict) -> Union[str, None]:
    """
    Given an arbitrary csv_ticket dict from report,
    Check that time adheres to one of TIME_FORMATS.
    Returns format string or throws error if no match.
    """
    # check whether a time attribute is present
    if csv_ticket.get("Created"):
        time_text: str = csv_ticket["Created"]
    elif csv_ticket.get("Modified"):
        time_text: str = csv_ticket["Modified"]
    else:
        # no date attributes, so no time format to set
        return None
    for try_format in TIME_FORMATS:
        try:
            datetime.strptime(time_text, try_format)
            return try_format
        except ValueError:
            continue
    raise BadReportError(f"Time {time_text} in report is not a valid time format")
