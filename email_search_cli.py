import sys
from commands.gmail_bot import GmailBot

def main():
    gmail_bot = GmailBot()
    gmail_bot.start()
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    results = gmail_bot.search_emails(query)
    if not results:
        print("No emails found.")
        return
    for i, email in enumerate(results, 1):
        print(f"{i}. From: {email.get('from_full','Unknown')}")
        print(f"   Subject: {email.get('subject','(No Subject)')}")
        print(f"   ID: {email.get('id','-')}\n")

if __name__ == "__main__":
    main()
