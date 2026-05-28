#!/usr/bin/env python3
"""
Bella Notte Operations CLI Tool
Victor Reyes — Bella Notte Ristorante, Milwaukee, WI

Usage:
    python bellanotte_data.py airtable [--table TABLE] [--status STATUS] [--search QUERY]
    python bellanotte_data.py airtable-get --id ID [--table TABLE]
    python bellanotte_data.py quickbooks [--entity-type TYPE] [--status STATUS] [--search QUERY]
    python bellanotte_data.py stripe [--status STATUS]
    python bellanotte_data.py fintrack [--category CAT] [--start-date D] [--end-date D]
    python bellanotte_data.py calendar [--start-date D] [--end-date D] [--search QUERY]
    python bellanotte_data.py contacts [--search QUERY] [--tag TAG]
    python bellanotte_data.py emails [--unread] [--folder FOLDER] [--search QUERY]
    python bellanotte_data.py email --id ID
    python bellanotte_data.py messaging [--search QUERY] [--contact CONTACT]
    python bellanotte_data.py message --id ID [--thread-id TID]
    python bellanotte_data.py slack [--channel CH] [--search QUERY]
    python bellanotte_data.py notion [--workspace WS] [--search QUERY]
    python bellanotte_data.py notion-get --id ID
    python bellanotte_data.py health [--metric M] [--start-date D] [--end-date D]
    python bellanotte_data.py crm [--type TYPE] [--status STATUS] [--search QUERY]
    python bellanotte_data.py instacart [--status STATUS] [--start-date D] [--end-date D]
    python bellanotte_data.py shopping [--status STATUS] [--start-date D] [--end-date D]
    python bellanotte_data.py amazon-fresh [--status STATUS] [--start-date D] [--end-date D]
    python bellanotte_data.py reminders [--completed BOOL] [--search QUERY]
    python bellanotte_data.py scenarios [--category CAT] [--tension T]
    python bellanotte_data.py prompts [--category CAT] [--tension T] [--difficulty D]
"""

import argparse
import json
import sys
from typing import Any, Dict
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


MCP_BASE_URL = "http://localhost:8080/mcp"


def _call_tool(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    payload = {
        "tool": tool_name,
        "params": params
    }

    try:
        req = Request(
            f"{MCP_BASE_URL}/call",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except (URLError, HTTPError) as e:
        return {"error": str(e)}


def cmd_airtable(args):
    params = {}
    if args.table:
        params["table"] = args.table
    if args.status:
        params["status"] = args.status
    if args.search:
        params["search"] = args.search

    result = _call_tool("bellanotte_airtable_list", params)
    print(json.dumps(result, indent=2))


def cmd_airtable_get(args):
    params = {"record_id": args.id}
    if args.table:
        params["table"] = args.table

    result = _call_tool("bellanotte_airtable_get", params)
    print(json.dumps(result, indent=2))


def cmd_quickbooks(args):
    params = {}
    if args.entity_type:
        params["entity_type"] = args.entity_type
    if args.status:
        params["status"] = args.status
    if args.search:
        params["search"] = args.search

    result = _call_tool("bellanotte_quickbooks_list", params)
    print(json.dumps(result, indent=2))


def cmd_stripe(args):
    params = {}
    if args.status:
        params["status"] = args.status

    result = _call_tool("bellanotte_stripe_list", params)
    print(json.dumps(result, indent=2))


def cmd_fintrack(args):
    params = {}
    if args.category:
        params["category"] = args.category
    if args.start_date:
        params["start_date"] = args.start_date
    if args.end_date:
        params["end_date"] = args.end_date

    result = _call_tool("bellanotte_fintrack_list", params)
    print(json.dumps(result, indent=2))


def cmd_calendar(args):
    params = {}
    if args.start_date:
        params["start_date"] = args.start_date
    if args.end_date:
        params["end_date"] = args.end_date
    if args.search:
        params["search"] = args.search

    result = _call_tool("bellanotte_calendar_list", params)
    print(json.dumps(result, indent=2))


def cmd_contacts(args):
    params = {}
    if args.search:
        params["search"] = args.search
    if args.tag:
        params["tag"] = args.tag

    result = _call_tool("bellanotte_contacts_list", params)
    print(json.dumps(result, indent=2))


def cmd_emails(args):
    params = {}
    if args.unread:
        params["unread"] = True
    if args.folder:
        params["folder"] = args.folder
    if args.search:
        params["search"] = args.search

    result = _call_tool("bellanotte_email_list", params)
    print(json.dumps(result, indent=2))


def cmd_email(args):
    result = _call_tool("bellanotte_email_get", {"email_id": args.id})
    print(json.dumps(result, indent=2))


def cmd_messaging(args):
    params = {}
    if args.search:
        params["search"] = args.search
    if args.contact:
        params["contact"] = args.contact

    result = _call_tool("bellanotte_messaging_list", params)
    print(json.dumps(result, indent=2))


def cmd_message(args):
    params = {"message_id": args.id}
    if args.thread_id:
        params["thread_id"] = args.thread_id

    result = _call_tool("bellanotte_messaging_get", params)
    print(json.dumps(result, indent=2))


def cmd_slack(args):
    params = {}
    if args.channel:
        params["channel"] = args.channel
    if args.search:
        params["search"] = args.search

    result = _call_tool("bellanotte_slack_list", params)
    print(json.dumps(result, indent=2))


def cmd_notion(args):
    params = {}
    if args.workspace:
        params["workspace"] = args.workspace
    if args.search:
        params["search"] = args.search

    result = _call_tool("bellanotte_notion_list", params)
    print(json.dumps(result, indent=2))


def cmd_notion_get(args):
    result = _call_tool("bellanotte_notion_get", {"page_id": args.id})
    print(json.dumps(result, indent=2))


def cmd_health(args):
    params = {}
    if args.metric:
        params["metric"] = args.metric
    if args.start_date:
        params["start_date"] = args.start_date
    if args.end_date:
        params["end_date"] = args.end_date

    result = _call_tool("bellanotte_health_get", params)
    print(json.dumps(result, indent=2))


def cmd_crm(args):
    params = {}
    if args.engagement_type:
        params["type"] = args.engagement_type
    if args.status:
        params["status"] = args.status
    if args.search:
        params["search"] = args.search

    result = _call_tool("bellanotte_crm_list", params)
    print(json.dumps(result, indent=2))


def cmd_instacart(args):
    params = {}
    if args.status:
        params["status"] = args.status
    if args.start_date:
        params["start_date"] = args.start_date
    if args.end_date:
        params["end_date"] = args.end_date

    result = _call_tool("bellanotte_instacart_list", params)
    print(json.dumps(result, indent=2))


def cmd_shopping(args):
    params = {}
    if args.status:
        params["status"] = args.status
    if args.start_date:
        params["start_date"] = args.start_date
    if args.end_date:
        params["end_date"] = args.end_date

    result = _call_tool("bellanotte_shopping_list", params)
    print(json.dumps(result, indent=2))


def cmd_amazon_fresh(args):
    params = {}
    if args.status:
        params["status"] = args.status
    if args.start_date:
        params["start_date"] = args.start_date
    if args.end_date:
        params["end_date"] = args.end_date

    result = _call_tool("bellanotte_amazon_fresh_list", params)
    print(json.dumps(result, indent=2))


def cmd_reminders(args):
    params = {}
    if args.completed is not None:
        params["completed"] = args.completed == "true"
    if args.search:
        params["search"] = args.search

    result = _call_tool("bellanotte_reminder_list", params)
    print(json.dumps(result, indent=2))


def cmd_scenarios(args):
    params = {}
    if args.category:
        params["category"] = args.category
    if args.tension:
        params["tension"] = args.tension

    result = _call_tool("bellanotte_scenarios_list", params)
    print(json.dumps(result, indent=2))


def cmd_prompts(args):
    params = {}
    if args.category:
        params["category"] = args.category
    if args.tension:
        params["tension"] = args.tension
    if args.difficulty:
        params["difficulty"] = args.difficulty

    result = _call_tool("bellanotte_prompts_list", params)
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="Bella Notte Operations CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    p_airtable = subparsers.add_parser("airtable", help="List Airtable records")
    p_airtable.add_argument("--table", help="Table name (Staff Schedule, Inventory, Daily Sales, Reservations)")
    p_airtable.add_argument("--status", help="Filter by status")
    p_airtable.add_argument("--search", help="Search query")
    p_airtable.set_defaults(func=cmd_airtable)

    p_airtable_get = subparsers.add_parser("airtable-get", help="Get Airtable record")
    p_airtable_get.add_argument("--id", required=True, help="Record id")
    p_airtable_get.add_argument("--table", help="Table name")
    p_airtable_get.set_defaults(func=cmd_airtable_get)

    p_qb = subparsers.add_parser("quickbooks", help="List QuickBooks records")
    p_qb.add_argument("--entity-type", help="Entity type (account, invoice, bill, vendor, payroll, etc.)")
    p_qb.add_argument("--status", help="Filter by status")
    p_qb.add_argument("--search", help="Search query")
    p_qb.set_defaults(func=cmd_quickbooks)

    p_stripe = subparsers.add_parser("stripe", help="List Stripe deposits")
    p_stripe.add_argument("--status", help="Payment status")
    p_stripe.set_defaults(func=cmd_stripe)

    p_ft = subparsers.add_parser("fintrack", help="List personal transactions")
    p_ft.add_argument("--category", help="Transaction category")
    p_ft.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    p_ft.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    p_ft.set_defaults(func=cmd_fintrack)

    p_cal = subparsers.add_parser("calendar", help="List calendar events")
    p_cal.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    p_cal.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    p_cal.add_argument("--search", help="Search query")
    p_cal.set_defaults(func=cmd_calendar)

    p_ct = subparsers.add_parser("contacts", help="List contacts")
    p_ct.add_argument("--search", help="Search query")
    p_ct.add_argument("--tag", help="Tag filter")
    p_ct.set_defaults(func=cmd_contacts)

    p_emails = subparsers.add_parser("emails", help="List emails")
    p_emails.add_argument("--unread", action="store_true", help="Unread only")
    p_emails.add_argument("--folder", help="Folder name")
    p_emails.add_argument("--search", help="Search query")
    p_emails.set_defaults(func=cmd_emails)

    p_email = subparsers.add_parser("email", help="Get email by id")
    p_email.add_argument("--id", required=True, help="Email id")
    p_email.set_defaults(func=cmd_email)

    p_msg = subparsers.add_parser("messaging", help="List messaging threads")
    p_msg.add_argument("--search", help="Search query")
    p_msg.add_argument("--contact", help="Filter by contact name")
    p_msg.set_defaults(func=cmd_messaging)

    p_msg_get = subparsers.add_parser("message", help="Get message or thread")
    p_msg_get.add_argument("--id", required=True, help="Message or thread id")
    p_msg_get.add_argument("--thread-id", help="Thread id")
    p_msg_get.set_defaults(func=cmd_message)

    p_slack = subparsers.add_parser("slack", help="List Slack messages")
    p_slack.add_argument("--channel", help="Channel name or id")
    p_slack.add_argument("--search", help="Search query")
    p_slack.set_defaults(func=cmd_slack)

    p_notion = subparsers.add_parser("notion", help="List Notion pages")
    p_notion.add_argument("--workspace", help="Workspace name")
    p_notion.add_argument("--search", help="Search query")
    p_notion.set_defaults(func=cmd_notion)

    p_notion_get = subparsers.add_parser("notion-get", help="Get Notion page")
    p_notion_get.add_argument("--id", required=True, help="Page id")
    p_notion_get.set_defaults(func=cmd_notion_get)

    p_health = subparsers.add_parser("health", help="Get Apple Health data")
    p_health.add_argument("--metric", help="Metric (sleep, heart_rate, steps, etc.)")
    p_health.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    p_health.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    p_health.set_defaults(func=cmd_health)

    p_crm = subparsers.add_parser("crm", help="List CRM engagements")
    p_crm.add_argument("--type", dest="engagement_type", help="Engagement type")
    p_crm.add_argument("--status", help="Status filter")
    p_crm.add_argument("--search", help="Search query")
    p_crm.set_defaults(func=cmd_crm)

    p_ic = subparsers.add_parser("instacart", help="List Instacart orders")
    p_ic.add_argument("--status", help="Order status")
    p_ic.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    p_ic.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    p_ic.set_defaults(func=cmd_instacart)

    p_shop = subparsers.add_parser("shopping", help="List shopping orders")
    p_shop.add_argument("--status", help="Order status")
    p_shop.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    p_shop.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    p_shop.set_defaults(func=cmd_shopping)

    p_af = subparsers.add_parser("amazon-fresh", help="List Amazon Fresh orders")
    p_af.add_argument("--status", help="Order status")
    p_af.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    p_af.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    p_af.set_defaults(func=cmd_amazon_fresh)

    p_rem = subparsers.add_parser("reminders", help="List reminders")
    p_rem.add_argument(
        "--completed",
        choices=["true", "false"],
        help="Filter by completed (true or false)",
    )
    p_rem.add_argument("--search", help="Search query")
    p_rem.set_defaults(func=cmd_reminders)

    p_sc = subparsers.add_parser("scenarios", help="List evaluation scenarios")
    p_sc.add_argument("--category", help="Evaluation category")
    p_sc.add_argument("--tension", help="Tension id or label")
    p_sc.set_defaults(func=cmd_scenarios)

    p_pr = subparsers.add_parser("prompts", help="List evaluation prompts")
    p_pr.add_argument("--category", help="Evaluation category")
    p_pr.add_argument("--tension", help="Tension id or label")
    p_pr.add_argument("--difficulty", help="Difficulty level")
    p_pr.set_defaults(func=cmd_prompts)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
