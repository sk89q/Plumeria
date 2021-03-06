"""Query last.fm for information about music."""

import io

import collections

from plumeria import config
from plumeria.command import commands, CommandError
from plumeria.message import Response
from plumeria.plugin import PluginSetupError
from plumeria.util import http
from plumeria.util.http import BaseRestClient, APIError
from plumeria.util.message import strip_html
from plumeria.util.ratelimit import rate_limit

api_key = config.create("lastfm", "key",
                        fallback="",
                        comment="An API key from last.fm")

Track = collections.namedtuple("Track", "artist title url")


class LastFm(BaseRestClient):
    URL = "http://ws.audioscrobbler.com/2.0/"
    _api_key = None

    @property
    def api_key(self):
        return self._api_key or api_key()

    @api_key.setter
    def api_key(self, value):
        self._api_key = value

    def preprocess(self, json):
        if 'error' in json:
            raise APIError(json['message'])
        return json

    async def recent_tracks(self, username):
        json = await self.request("get", self.URL, params={
            'method': "user.getrecenttracks",
            'user': username,
            'format': 'json',
            'api_key': self.api_key,
        })
        return [Track(i['artist']['#text'], i['name'], i['url']) for i in json['recenttracks']['track']]

    async def tag_tracks(self, tag):
        json = await self.request("get", self.URL, params={
            'method': "tag.gettoptracks",
            'tag': tag,
            'format': 'json',
            'api_key': self.api_key,
        })
        return [Track(i['artist']['name'], i['name'], i['url']) for i in json['tracks']['track']]


lastfm = LastFm()


@commands.create('lastfm', 'last scrobble', 'lastscrobble', category='Music')
@rate_limit()
async def lastscrobble(message):
    """
    Gets the last scrobbled song of a user.

    Example::

        /lastfm example

    Response::

        Polar Bear Club - Wlwycd

    """
    if len(message.content):
        tracks = await lastfm.recent_tracks(message.content)
        if len(tracks):
            return Response("{} - {}".format(tracks[0].artist, tracks[0].title))
        else:
            raise CommandError("No tracks have been scrobbled by that user.")


@commands.create('lastfm tag', 'tagtop', category='Music')
@rate_limit()
async def tagtop(message):
    """
    Gets the top track for a music tag using last.fm.

    Example::

        /tagtop indie rock

    Response::

        The Killers - Mr. Brightside
    """
    if len(message.content):
        tracks = await lastfm.tag_tracks(message.content)
        if len(tracks):
            return Response("{} - {}".format(tracks[0].artist, tracks[0].title))
        else:
            raise CommandError("Last.fm doesn't know about that tag.")


@commands.create('lastfm artist', 'artist', category='Music')
@rate_limit()
async def artist(message):
    """
    Gets information about a music artist.

    Example::

        /artist the dear hunter
    """
    query = message.content.strip()

    if not len(query):
        raise CommandError("Provide an artist name to lookup.")

    r = await http.get("http://ws.audioscrobbler.com/2.0/", params=[
        ('method', 'artist.getinfo'),
        ('api_key', api_key()),
        ('format', 'json'),
        ('artist', query),
    ])
    data = r.json()

    if 'error' in data:
        raise CommandError(data['message'])

    artist = data['artist']
    vars = {}
    vars['name'] = artist['name']
    vars['url'] = artist['url']
    vars['image'] = None
    vars['on_tour'] = artist['ontour'] != "0"
    vars['listeners'] = int(artist['stats']['listeners'])
    vars['play_count'] = int(artist['stats']['playcount'])
    vars['similar'] = [e['name'] for e in artist['similar']['artist']]
    vars['tags'] = [e['name'] for e in artist['tags']['tag']]
    vars['bio'] = strip_html(artist['bio']['summary'])

    for i in artist['image']:
        if i['size'] == 'large':
            vars['image'] = i['#text']

    buffer = io.StringIO()
    buffer.write("{image}\n\n".format(**vars))
    buffer.write("**{name}**".format(**vars))
    if vars['on_tour']:
        buffer.write(" (\N{ADMISSION TICKETS} ON TOUR)")
    buffer.write("\n")
    buffer.write("{listeners} listeners, {play_count} plays on last.fm\n".format(**vars))
    buffer.write("\n")
    buffer.write("**Similar:** {}\n".format(", ".join(vars['similar'])))
    buffer.write("**Tags:** {}\n".format(", ".join(vars['tags'])))
    buffer.write("\n")
    buffer.write("{bio}".format(**vars))
    buffer.write("\n\n")
    buffer.write("<{url}>\n".format(**vars))

    return buffer.getvalue()


def setup():
    config.add(api_key)

    if not api_key():
        raise PluginSetupError("This plugin requires an API key from http://last.fm. Registration is free.")

    commands.add(lastscrobble)
    commands.add(tagtop)
    commands.add(artist)
