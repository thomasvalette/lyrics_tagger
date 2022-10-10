import os
import aiohttp
import asyncio
import sys
import random
from mediafile import MediaFile
from rich import print
from bs4 import BeautifulSoup

NB_TRIES = 3


async def get_song_url(context, track):
    session = context["session"]
    progress = context["progress"]
    fetch_urls = context["fetch_urls"]
    url = f"https://genius.com/api/search/multi?per_page=5&q={track.artist} {track.title}"
    async with session.get(url) as resp:
        song_info = await resp.json()
        try:
            song_url = song_info["response"]["sections"][1]["hits"][0]["result"]["path"]
            progress.update(fetch_urls, advance=1)
            return (track, f"https://genius.com{song_url}")
        except Exception:
            progress.update(fetch_urls, advance=1)
            return (track, None)


async def get_song_lyrics(context, url, track, tries=0):
    """Return lyrics for the provided url
    Parsing is done with BS4 library
    """
    session = context["session"]
    progress = context["progress"]
    fetch_lyrics = context["fetch_lyrics"]
    async with session.get(url) as resp:
        result = await resp.text()
        soup = BeautifulSoup(result, "html.parser")
        if soup.find(
            "div", {"class": lambda L: L and L.startswith(
                "LyricsPlaceholder")}
        ):
            progress.update(fetch_lyrics, advance=1)
            return (track, "Instrumental")
        section = soup.find(
            "div", {"class": lambda L: L and L.startswith(
                "Lyrics__Container")}
        )
        # sometimes genius doesn't load properly lyrics
        try:
            progress.update(fetch_lyrics, advance=1)
            lyrics = section.get_text("\n")
            return (track, lyrics)
        except Exception:
            # try X times before failing
            if tries > NB_TRIES:
                return
            # random sleep time to avoid spam & bot detection
            await asyncio.sleep(random.random()+1)
            # retry until the lyrics is retreived
            tries += 1
            lyrics = await get_song_lyrics(session, url, progress, tries)
