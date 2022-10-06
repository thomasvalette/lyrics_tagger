import asyncio
import sys
import aiohttp
from pathlib import Path
from genius import get_song_lyrics, get_song_url
from mediafile import MediaFile
from rich import print


def build_tree(path, content=[], level=0, nb_item=0):
    idx = 0
    separator = "├──"

    for entity in path.iterdir():
        if entity.is_dir():
            nb_file = len(list(entity.iterdir()))
            content.append("  " * level + "📁 " + entity.name)
            level += 1
            build_tree(entity, content, level, nb_file)
            level -= 1
        else:
            idx += 1
            filename = entity.name
            if len(filename) > 40:
                filename = filename[0:36] + "..."

            if idx == nb_item:
                separator = "└──"
            content.append(
                ["  " * level + separator + f"{filename:40}", entity])

    return content


async def tag_files(tracks, replace=False):

    print(tracks)

    for idx, track in enumerate(tracks):
        track_info = MediaFile(track[1])
        tracks[idx] = track + [track_info.artist, track_info.title]

    async with aiohttp.ClientSession() as session:
        # retrieving song urls
        tasks = []
        for track in tracks:
            tasks.append(
                asyncio.ensure_future(get_song_url(
                    session, track[2], track[3]))
            )

        songs_urls = await asyncio.gather(*tasks)

        for idx, track in enumerate(tracks):
            tracks[idx] = track + [songs_urls[idx]]

        # retrieving song lyrics
        tasks = []
        for track in tracks:
            tasks.append(asyncio.ensure_future(
                get_song_lyrics(session, track[4])))

        songs_lyrics = await asyncio.gather(*tasks)

        # tagging files
        for idx, track in enumerate(tracks):

            track_info = MediaFile(track[1])
            track_info.lyrics = songs_lyrics[idx]

            # # check lyrics existence
            # if len(track_info.lyrics) > 0:
            #     tracks[idx][0] += "[gold3] Existing lyrics found"
            #     if not replace:
            #         tracks[idx][0] += ", ignoring track ...[/gold3]"
            #         return

            # tracks[idx][0] += ", replaced ...[/gold3]"

        for track in tracks:
            print(track[0])


if __name__ == "__main__":

    # Only preform check if your code will run on non-windows environments.
    if sys.platform.startswith("win"):
        # Set the policy to prevent "Event loop is closed" error on Windows - https://github.com/encode/httpx/issues/914
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    tree = build_tree(Path.home() / r"D:\tmp")

    tasks = []

    for item in tree:
        # file
        if type(item) is list:
            tasks.append(item)
        # folder
        else:
            print(item)
            if len(tasks) > 0:
                asyncio.run(tag_files(tasks))
            tasks = []
