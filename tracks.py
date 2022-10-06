import aiohttp
import asyncio
import os
import sys
from rich import print
from mediafile import MediaFile, FileTypeError
from genius import get_song_lyrics, get_song_url


def get_tracks_from_directory(path):
    tracks = []
    for root, _, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                track = MediaFile(file_path)
                tracks.append(track)
            except FileTypeError:
                pass
    return tracks


async def tag_track(session, track):
    url = await get_song_url(session, track.artist, track.title)
    print(url)
    lyrics = await get_song_lyrics(session, url)
    track.lyrics = lyrics
    track.save()
    print(f"{track.title} saved!")


async def tag_all_tracks(tracks):
    track_not_found = []
    lyric_not_found = []
    nb_tracks = 0
    async with aiohttp.ClientSession() as session:
        tasks_url = []
        # retrieve all lyrics
        for track in tracks:
            tasks_url.append(asyncio.ensure_future(
                get_song_url(session, track)))
        urls = await asyncio.gather(*tasks_url)

        tasks_lyric = []

        # retrieve all lyrics
        for url in urls:
            if url[1] is None:
                track_not_found.append(f"{url[0].artist} - {url[0].title}")
            else:
                tasks_lyric.append(asyncio.ensure_future(
                    get_song_lyrics(session, url[1], url[0])))
        lyrics_list = await asyncio.gather(*tasks_lyric)

        # tag all tracks
        for lyrics in lyrics_list:
            if lyrics[1] is None:
                lyric_not_found.append(
                    f"{lyrics[0].artist} - {lyrics[0].title}")
            else:
                track = lyrics[0]
                track.lyrics = lyrics[1]
                track.save()
                nb_tracks += 1

        return nb_tracks, track_not_found, lyric_not_found

if __name__ == "__main__":
    # Only preform check if your code will run on non-windows environments.
    if sys.platform.startswith("win"):
        # Set the policy to prevent "Event loop is closed" error on Windows - https://github.com/encode/httpx/issues/914
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    tracks = get_tracks_from_directory(r"D:\tmp")

    a, b, c = asyncio.run(tag_all_tracks(tracks))

    print(a, b, c)
