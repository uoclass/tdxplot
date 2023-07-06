"""
Command-line interface for tdxplot
by Eric Edwards, Alex JPS
2023-06-06

The primary .py file form which the program should run.
Parses user input via command-line arguments.
Also performs basic input validation (e.g. formatting, valid files, etc.)
Passes a dictionary with info to appropriate files or functions.
"""

# import libraries
import argparse
import sys
import os
import datetime

# import files
from report import *
from organization import *
from visual import *

# constants
COLORS: list[str] = ["white", "black", "gray", "yellow", "red", "blue", "green", "brown", "pink", "orange", "purple"] 
DATE_FORMATS: list[str] = ["%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%d.%m.%Y", "%d.%m.%Y"]

def check_file(filename: str):
    """
    Check that the given filename exists and is a CSV file.
    """
    if not filename:
        print("No file input provided", file=sys.stderr)
        exit(1)
    filename.strip()
    if not (os.path.exists(filename)):
        print("Always include filename as the last argument")
        print(f"File {filename} not found", file=sys.stderr)
        exit(1)
    if (os.path.splitext(filename)[-1].lower()) != ".csv":
            print("Always include filename as the last argument")
            print(f"File {filename} is not a CSV file", file=sys.stderr)
            exit(1)

def check_date(date_text: str):
    """
    Checks that given string adheres to one of DATE_FORMATS.
    Returns datetime object.
    """
    date = None
    for date_format in DATE_FORMATS:
        try:
            date: datetime = datetime.strptime(date_text, date_format)
            break
        except:
            continue
    if not date:
        print(f"Date {date_text} not recognized, try yyyy-mm-dd", file=sys.stderr)
        exit(1)
    return date

def check_options(args: dict) -> None:
    """
    Halt program if conflicting or missing flags given.
    """
    # Allow only one query type
    count: int = 0
    for key in args:
        if key in ["perweek", "perbuilding", "perroom"] and args[key]:
            count += 1
        if count > 1:
            print("Pass exactly one query preset argument (e.g. --perweek)", file=sys.stderr)
            exit(1)
    if not count:
        print("No query preset argument passed (e.g. --perweek)", file=sys.stderr)
        exit(1)

    # Stipulations for --perroom
    if args.get("perroom") and not args.get("building"):
        print("No building specified, please specify a building for --perroom using --building [BUILDING_NAME].", file=sys.stderr)
        exit(1)

    # Stipulations for --perbuilding
    if args.get("perbuilding") and args.get("building"):
        print("Cannot filter to a single building in in a --perbuilding query", file=sys.stderr)
        exit(1)

    # Stipulations for --perweek
    if not args.get("perweek") and args.get("weeks") != None:
        print("Cannot pass --weeks without --perweek", file=sys.stderr)
        exit(1)
    if args.get("weeks") and args.get("termend"):
        print("Cannot pass --weeks and --termend simultaneously", file=sys.stderr)
        exit(1)

def parser_setup():
    """
    Set up argument parser with needed arguments.
    Return the parser.
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    # display customization
    parser.add_argument("-n", "--name", type=str, help="Set the name of the plot.")
    parser.add_argument("-c", "--color", choices=COLORS, help="Set the color of the plot.")
    # filters
    parser.add_argument("-t", "--termstart", type=str, help="Exclude tickets before this date (calendar week for --perweek)")
    parser.add_argument("-e", "--termend", type=str, help="Exclude tickets after this date (calendar week for --perweek)")
    parser.add_argument("-w", "--weeks", type=int, help="Set number of weeks in the term for --perweek")
    parser.add_argument("-b", "--building", type=str, help="Specify building filter.")
    # query presets
    parser.add_argument("--perweek", action="store_true", help="Show tickets per week")
    parser.add_argument("--perbuilding", action="store_true", help="Show tickets per building")
    parser.add_argument("--perroom", action="store_true", help="Show tickets per room in a specified building.")
    
    return parser

def main():
    """
    Parse arguments, call basic input validation.
    Call plot.py with args.
    """
    # Check last arg is a valid filename
    filename: str = sys.argv.pop()
    filename.strip()
    check_file(filename)
    
    # set up parsers and parse into dict
    parser: argparse.ArgumentParser = parser_setup()
    args: dict = vars(parser.parse_args())

    # set filename of arg dict
    args["filename"] = filename

    # halt if conflicting flags given
    check_options(args)

    # initialize report and organization
    report = Report(args["filename"])
    org = Organization()
    report.populate(org)
    
    # ensure valid date formats
    if args.get("termstart"):
        args["termstart"] = check_date(args["termstart"])
    if args.get("termend"):
        args["termend"] = check_date(args["termend"])
    
    if args.get("building"):
        args["building"] = org.find_building(args["building"])
        if not args["building"]:
            print("No such building found in report", file=sys.stderr)
            exit(1)
    
    # ensure report matches requirements for query
    if args.get("perweek"):
        if "Created" in report.fields_present:
            tickets_per_week = org.per_week(args)
            view_per_week(tickets_per_week, args)
        else:
            print("Cannot run a tickets-per-week query without Created field present in report", file=sys.stderr)
            exit(1)
    if args.get("perbuilding"):
        if "Class Support Building" in report.fields_present:
            tickets_per_building = org.per_building(args)
            # FIXME
            print(tickets_per_building)
        else:
            print("Cannot run a tickets-per-building query without Class Support Building field present in report", file=sys.stderr)
            exit(1)
    if args.get("perroom"):
        if "Class Support Building" in report.fields_present and "Room number" in report.fields_present:
            tickets_per_room = org.per_room(args)
            # FIXME
            print(tickets_per_room)
        else:
            print("Cannot run a tickets-per-room query without Class Support Building and Room number field present in report", file=sys.stderr)
            exit(1)
            
if __name__ == "__main__":
    main()
