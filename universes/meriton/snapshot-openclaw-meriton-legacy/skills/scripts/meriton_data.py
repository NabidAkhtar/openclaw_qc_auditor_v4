#!/usr/bin/env python3
"""
Meriton Operations CLI Tool
Christine Zhao — Meriton Financial, Raleigh, NC

Usage:
    python meriton_data.py calendar [--search QUERY] [--date DATE]
    python meriton_data.py contacts [--search QUERY]
    python meriton_data.py emails [--search QUERY]
    python meriton_data.py email --id ID
    python meriton_data.py fintrack [--type TYPE]
    python meriton_data.py messaging
    python meriton_data.py conversation --id ID
    python meriton_data.py quickbooks [--type TYPE]
    python meriton_data.py reminders
    python meriton_data.py sonos [--type TYPE]
    python meriton_data.py strava [--type TYPE]
    python meriton_data.py ticketmaster [--type TYPE]
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


def _load(filename: str) -> Any:
    path = DATA_DIR / filename
    if not path.exists():
        print(f"Error: {path} not found", file=sys.stderr)
        sys.exit(1)
    with open(path) as f:
        return json.load(f)


def _print(data: Any):
    print(json.dumps(data, indent=2))


def _ts_to_date(ts):
    """Convert a Unix timestamp to YYYY-MM-DD string."""
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
    return str(ts)


def cmd_calendar(args):
    """List calendar events with optional filters."""
    data = _load("calendar.json")
    events = data.get("events", data if isinstance(data, list) else [])

    if args.search:
        q = args.search.lower()
        events = [e for e in events if q in json.dumps(e).lower()]
    if args.date:
        events = [e for e in events
                  if args.date in _ts_to_date(e.get("start_datetime", ""))
                  or args.date in _ts_to_date(e.get("end_datetime", ""))
                  or args.date in json.dumps(e)]

    print(f"Found {len(events)} events")
    _print(events)


def cmd_contacts(args):
    """List contacts with optional search."""
    data = _load("contacts.json")
    contacts = data.get("contacts", data if isinstance(data, list) else [])

    if args.search:
        q = args.search.lower()
        contacts = [c for c in contacts if q in json.dumps(c).lower()]

    print(f"Found {len(contacts)} contacts")
    _print(contacts)


def cmd_emails(args):
    """List emails with optional search."""
    data = _load("email.json")
    emails = data.get("emails", data if isinstance(data, list) else [])

    if args.search:
        q = args.search.lower()
        emails = [e for e in emails if q in json.dumps(e).lower()]

    print(f"Found {len(emails)} emails")
    _print(emails)


def cmd_email(args):
    """Get a specific email by ID."""
    data = _load("email.json")
    emails = data.get("emails", data if isinstance(data, list) else [])

    for e in emails:
        eid = e.get("id") or e.get("email_id") or e.get("messageId")
        if str(eid) == str(args.id):
            _print(e)
            return

    print(f"Email {args.id} not found", file=sys.stderr)
    sys.exit(1)


def cmd_fintrack(args):
    """List fintrack records by type."""
    data = _load("fintrack.json")

    if args.type:
        if args.type in data:
            records = data[args.type]
            print(f"Found {len(records)} {args.type} records")
            _print(records)
        else:
            print(f"Unknown type: {args.type}. Available: {', '.join(data.keys())}", file=sys.stderr)
            sys.exit(1)
    else:
        summary = {k: len(v) if isinstance(v, list) else type(v).__name__ for k, v in data.items()}
        print("FinTrack summary:")
        _print(summary)


def cmd_messaging(args):
    """List messaging conversations."""
    data = _load("messaging.json")
    conversations = data.get("conversations", data if isinstance(data, list) else [])

    print(f"Found {len(conversations)} conversations")
    for conv in conversations:
        cid = conv.get("id") or conv.get("conversation_id", "?")
        participants = conv.get("participants", conv.get("members", []))
        msg_count = len(conv.get("messages", []))
        print(f"  {cid}: {participants} ({msg_count} messages)")


def cmd_conversation(args):
    """Get a specific conversation by ID."""
    data = _load("messaging.json")
    conversations = data.get("conversations", data if isinstance(data, list) else [])

    for conv in conversations:
        cid = str(conv.get("id") or conv.get("conversation_id", ""))
        if cid == str(args.id):
            _print(conv)
            return

    print(f"Conversation {args.id} not found", file=sys.stderr)
    sys.exit(1)


def cmd_quickbooks(args):
    """List QuickBooks records by type."""
    data = _load("quickbooks.json")

    if args.type:
        if args.type in data:
            records = data[args.type]
            print(f"Found {len(records)} {args.type} records")
            _print(records)
        else:
            print(f"Unknown type: {args.type}. Available: {', '.join(data.keys())}", file=sys.stderr)
            sys.exit(1)
    else:
        summary = {k: len(v) if isinstance(v, list) else type(v).__name__ for k, v in data.items()}
        print("QuickBooks summary:")
        _print(summary)


def cmd_reminders(args):
    """List all reminders."""
    data = _load("reminder.json")
    reminders = data.get("reminders", data if isinstance(data, list) else [])

    print(f"Found {len(reminders)} reminders")
    _print(reminders)


def cmd_sonos(args):
    """List Sonos records by type."""
    data = _load("sonos.json")

    if args.type:
        if args.type in data:
            records = data[args.type]
            print(f"Found {len(records)} {args.type} records")
            _print(records)
        else:
            print(f"Unknown type: {args.type}. Available: {', '.join(data.keys())}", file=sys.stderr)
            sys.exit(1)
    else:
        summary = {k: len(v) if isinstance(v, list) else type(v).__name__ for k, v in data.items()}
        print("Sonos summary:")
        _print(summary)


def cmd_strava(args):
    """List Strava records by type."""
    data = _load("strava.json")

    if args.type:
        if args.type in data:
            records = data[args.type]
            print(f"Found {len(records)} {args.type} records")
            _print(records)
        else:
            print(f"Unknown type: {args.type}. Available: {', '.join(data.keys())}", file=sys.stderr)
            sys.exit(1)
    else:
        summary = {k: len(v) if isinstance(v, list) else type(v).__name__ for k, v in data.items()}
        print("Strava summary:")
        _print(summary)


def cmd_ticketmaster(args):
    """List Ticketmaster records by type."""
    data = _load("ticketmaster.json")

    if args.type:
        if args.type in data:
            records = data[args.type]
            print(f"Found {len(records)} {args.type} records")
            _print(records)
        else:
            print(f"Unknown type: {args.type}. Available: {', '.join(data.keys())}", file=sys.stderr)
            sys.exit(1)
    else:
        summary = {k: len(v) if isinstance(v, list) else type(v).__name__ for k, v in data.items()}
        print("Ticketmaster summary:")
        _print(summary)


def main():
    parser = argparse.ArgumentParser(
        description="Meriton Operations CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    p_cal = subparsers.add_parser("calendar", help="List calendar events")
    p_cal.add_argument("--search", help="Search events by keyword")
    p_cal.add_argument("--date", help="Filter by date (YYYY-MM-DD)")
    p_cal.set_defaults(func=cmd_calendar)

    p_contacts = subparsers.add_parser("contacts", help="List contacts")
    p_contacts.add_argument("--search", help="Search contacts by name or keyword")
    p_contacts.set_defaults(func=cmd_contacts)

    p_emails = subparsers.add_parser("emails", help="List emails")
    p_emails.add_argument("--search", help="Search emails by keyword")
    p_emails.set_defaults(func=cmd_emails)

    p_email = subparsers.add_parser("email", help="Get specific email")
    p_email.add_argument("--id", required=True, help="Email ID")
    p_email.set_defaults(func=cmd_email)

    p_fin = subparsers.add_parser("fintrack", help="List fintrack records")
    p_fin.add_argument("--type", choices=["users", "accounts", "subscriptions", "transactions"],
                       help="Record type to list")
    p_fin.set_defaults(func=cmd_fintrack)

    p_msg = subparsers.add_parser("messaging", help="List messaging conversations")
    p_msg.set_defaults(func=cmd_messaging)

    p_conv = subparsers.add_parser("conversation", help="Get specific conversation")
    p_conv.add_argument("--id", required=True, help="Conversation ID")
    p_conv.set_defaults(func=cmd_conversation)

    p_qb = subparsers.add_parser("quickbooks", help="List QuickBooks records")
    p_qb.add_argument("--type", choices=["customers", "vendors", "accounts", "invoices", "bills", "items"],
                      help="Record type to list")
    p_qb.set_defaults(func=cmd_quickbooks)

    p_rem = subparsers.add_parser("reminders", help="List reminders")
    p_rem.set_defaults(func=cmd_reminders)

    p_sonos = subparsers.add_parser("sonos", help="List Sonos records")
    p_sonos.add_argument("--type", choices=["users", "speakers", "speaker_groups", "group_members",
                                            "favorites", "favorite_tracks"],
                         help="Record type to list")
    p_sonos.set_defaults(func=cmd_sonos)

    p_strava = subparsers.add_parser("strava", help="List Strava records")
    p_strava.add_argument("--type", choices=["activities", "athletes", "athlete_stats", "clubs",
                                             "club_memberships", "activity_photos"],
                          help="Record type to list")
    p_strava.set_defaults(func=cmd_strava)

    p_tm = subparsers.add_parser("ticketmaster", help="List Ticketmaster records")
    p_tm.add_argument("--type", choices=["users", "venues", "events", "orders",
                                         "attractions", "event_attractions"],
                      help="Record type to list")
    p_tm.set_defaults(func=cmd_ticketmaster)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
