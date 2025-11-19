@eel.expose
def search_my_emails(query: str, max_results: int = 25):
    """
    Exposed Eel tool to retrieve/search user emails using a keyword or Gmail search query.
    Returns a list of emails (dicts with id, from_full, subject).
    """
    if gmail_bot:
        return gmail_bot.search_emails(query, max_results)
    return []
