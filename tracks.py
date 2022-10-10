import aiohttp
import asyncio
import os
import sys
from rich import print
from rich.progress import Progress
from rich.prompt import Confirm
from rich.table import Table
from mediafile import MediaFile, FileTypeError
from genius import get_song_lyrics, get_song_url


def get_tracks_from_directory(path):

    print(f"\n Selected path : [yellow][bold]{path}[/bold]")
    total_nb_files = 0
    for _, _, files in os.walk(path):
        total_nb_files += len(files)

    tracks = []
    with Progress() as progress:
        file_crawl = progress.add_task(
            "[yellow] Scanning local files ...            ", total=total_nb_files)
        for root, _, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    track = MediaFile(file_path)
                    tracks.append(track)
                except FileTypeError:
                    pass
                finally:
                    progress.update(file_crawl, advance=1)
        return tracks


async def tag_track(session, track):
    url = await get_song_url(session, track.artist, track.title)
    print(url)
    lyrics = await get_song_lyrics(session, url)
    track.lyrics = lyrics
    track.save()


async def tag_all_tracks(tracks):
    url_not_found = []
    lyric_not_found = []
    tagged_tracks = 0
    context = {}

    if Confirm.ask(f" {len(tracks)} tracks were found, continue?"):

        # creatikng progress bars for fancier display
        with Progress() as progress:

            fetch_urls = progress.add_task(
                "[blue] Fetching Genius urls ...   ", total=len(tracks))
            fetch_lyrics = progress.add_task(
                "[cyan] Fetching tracks lyrics & tagging ...", total=len(tracks))

            context["progress"] = progress
            context["fetch_urls"] = fetch_urls
            context["fetch_lyrics"] = fetch_lyrics

            async with aiohttp.ClientSession() as session:
                context["session"] = session
                tasks_url = []
                # retrieve all lyrics
                for track in tracks:
                    tasks_url.append(asyncio.ensure_future(
                        get_song_url(context, track)))
                urls = await asyncio.gather(*tasks_url)
                tasks_lyric = []

                # retrieve all lyrics
                for url in urls:
                    if url[1] is None:
                        url_not_found.append((url[0].artist, url[0].title))
                        progress.update(fetch_lyrics, advance=1)
                    else:
                        tasks_lyric.append(asyncio.ensure_future(
                            get_song_lyrics(context, url[1], url[0])))
                lyrics_list = await asyncio.gather(*tasks_lyric)

                # tag all tracks
                for lyrics in lyrics_list:
                    if lyrics[1] is None:
                        lyric_not_found.append(
                            lyrics[0].artist, lyrics[0].title)
                    else:
                        track = lyrics[0]
                        track.lyrics = lyrics[1]
                        track.save()
                        tagged_tracks += 1

        print("\n End Report: ")
        print(" ━━━━━━━━━━━")
        print(f"[green]Tagged track : {tagged_tracks}[/green]")
        print(f"[red]Url not found : {len(url_not_found)}[/red]")
        print(f"[red]Lyrics not found : {len(lyric_not_found)}[/red]")

        if Confirm.ask("\nDo you want to display error details?"):
            table = Table()

            table.add_column("Artist", style="cyan")
            table.add_column("Title", style="magenta")
            table.add_column("Error", justify="right")

            for err in url_not_found:
                table.add_row(err[0], err[1], "[yellow]Url Not Found[/yellow]")

            for err in lyric_not_found:
                table.add_row(err[0], err[1], "[red]Lyrics Not Found[/red]")

            print(table)


if __name__ == "__main__":
    # Only preform check if your code will run on non-windows environments.
    if sys.platform.startswith("win"):
        # Set the policy to prevent "Event loop is closed" error on Windows - https://github.com/encode/httpx/issues/914
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    tracks = get_tracks_from_directory(
        r"D:\Thomas\Music\FLAC_old")

    asyncio.run(tag_all_tracks(tracks))
