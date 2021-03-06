"""Get information about movies from IMDB vua omdbapi."""

import plumeria.util.http as http
import re
from plumeria.command import commands, CommandError
from plumeria.util.ratelimit import rate_limit

URL = "http://www.omdbapi.com/"
NAME_PATTERN = re.compile("^(.+?)(?:\\( *([0-9]{4}) *\\))?$")


@commands.create("imdb", category="Search")
@rate_limit()
async def imdb(message):
    """
    Look for information about a movie.

    Example::

        /imdb LA Confidential

    Response::

        L.A. Confidential (1997)
        138 min (R)
        Metascore: 90 / IMDB: 8.3
        Genre: Crime, Drama, Mystery

        As corruption grows in 1950s LA, three policemen[...]
    """
    m = NAME_PATTERN.match(message.content.strip())
    data = (await http.get(URL, params={
        "t": m.group(1),
        "y": m.group(2) or "",
        "plot": "full",
        "r": "json",
    })).json()
    if 'Title' in data:
        return "**{Title} ({Year})**\n" \
               "{Runtime} ({Rated})\n" \
               "Metascore: {Metascore} / IMDB: {imdbRating}\n" \
               "Genre: {Genre}\n" \
               "\n{Plot}\n".format(**data)
    else:
        raise CommandError("No movie found with that name.")


def setup():
    commands.add(imdb)
