import asyncio
import json
import os

import aiohttp
import guessit
import re

from application.models import Movie, NewMovieNotification, MovieDirectory
from django.conf import settings
from django.utils import timezone
from urllib.parse import urlencode

def write_file(filename, data):
    with open(os.path.join(settings.MEDIA_ROOT, "posters", filename), "wb") as f:
        f.write(data)


async def save_poster(poster_url, loop, aiohttp_session):
    if not poster_url:
        return ""

    async with aiohttp_session.get(poster_url) as resp:
        filename = os.path.basename(poster_url)
        loop.call_soon(write_file, filename, await resp.read())
        return os.path.join("posters", filename)  # return media url


END_WITH_YEAR_RE = re.compile(r"(.*) ([1-2][0-9]{3})$")
class OMDBAPI:
    def __init__(self, loop, aiohttp_session):
        self.loop = loop
        self.aiohttp_session = aiohttp_session

    async def search(self, name):
        infos = guessit.guessit(name, {"type": "movie"})
        if not infos.get('title'):
            return

        params = {'s': infos['title'], 'type': 'movie', 'r': 'json', 'apikey': settings.OMDB_API_KEY}
        if "year" in infos:
            params['y'] = infos["year"]

        try_again_on_fail = False
        if 'alternative_title' in infos:
            params['s'] += " " + infos["alternative_title"]
            try_again_on_fail = True

        movie = await self.try_search(params)

        if movie is None and "y" not in params:
            m = END_WITH_YEAR_RE.search(params['s'])
            if m:
                params["s"] = m.group(1)
                params["y"] = m.group(2)
                movie = await self.try_search(params)

        if movie is None and try_again_on_fail:
            params['s'] = infos['title']
            movie = await self.try_search(params)

        return movie


    async def try_search(self, options):
        params = urlencode(options)
        url = 'http://www.omdbapi.com/?%s' % params
        async with self.aiohttp_session.get(url) as resp:
            data = await resp.text()
            resp = json.loads(data)
            if "Search" in resp:
                for res in resp['Search']:
                    poster = res['Poster'] if res['Poster'] != 'N/A' else ""
                    return Movie(
                        title=res['Title'],
                        imdbid=res['imdbID'],
                        poster=await save_poster(poster, self.loop, self.aiohttp_session),
                    )
        return None

    async def get_detailled_infos(self, imdbid):
        params = urlencode({'i': imdbid, 'plot': 'full', 'r': 'json', 'apikey': settings.OMDB_API_KEY})
        url = 'http://www.omdbapi.com/?%s' % params
        async with self.aiohttp_session.get(url) as resp:
            resp = json.loads(await resp.text())
            if resp['Response'] == 'True':
                return resp
