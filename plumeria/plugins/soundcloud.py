from plumeria import config
from plumeria.command import commands, CommandError
from plumeria.util import http
from plumeria.util.ratelimit import rate_limit

RESULT_LIMIT = 5

client_id = config.create("soundcloud", "client_id",
                          fallback="",
                          comment="A client ID registered on soundcloud.com")


@commands.register("soundcloud", category="Search")
@rate_limit()
async def soundcloud(message):
    """
    Search SoundCloud for tracks.

    """
    q = message.content.strip()
    if not len(q):
        raise CommandError("Search term required!")
    r = await http.get("https://api.soundcloud.com/tracks/", params=[
        ('q', q),
        ('client_id', client_id())
    ])
    data = r.json()
    if len(data):
        results = map(lambda item: "\u2022 **{}** <{}>".format(
            item['title'],
            item['permalink_url']), data[:RESULT_LIMIT])
        return "SoundCloud track search:\n{}".format("\n".join(results))
    else:
        raise CommandError("no results found")