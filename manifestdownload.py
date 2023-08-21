from pprint import pformat
import subprocess, os, traceback, asyncio
import logging
from extractmanifest import getmanifesturls
import aiohttp, aiofiles, requests
from yarl import URL
from tqdm.asyncio import tqdm

async def manifestdownload(manifest: dict, verbose: bool = False, audioonly: bool = False):
    if not os.path.exists('videoinfo'):
        os.mkdir('videoinfo')
    with open('videoinfo/manifest.txt', 'w') as f1:
        f1.write(pformat(manifest))
    #DOWNLOAD VIDEOS
    logging.basicConfig(level=logging.DEBUG if verbose else logging.info)
    logging.info('downloading chunked manifest videos...')
    extension = 'mp4' if not audioonly and 'avc1' in manifest.get('CODECS') else 'webm' if not audioonly and 'vp09' in manifest.get('CODECS') else 'mp3'
    if not audioonly:
        videourls = await getmanifesturls(manifest.get('URL'))
        logging.debug(f'\n\nVIDEOURLS LEN {len(videourls)}\n\n')
    audiourls = await getmanifesturls(manifest.get('AUDIOLINK'))
    logging.debug(f'\n\nAUDIOURLS LEN {len(audiourls)}\n\n')
    totalsize = float(manifest.get('FILESIZE'))*(1024*1024)
    async def downloadmanifest(urls: list, filename: str, filetype: str):
        async with aiofiles.open(filename, 'wb') as f1:
            async with aiohttp.ClientSession() as session:
                for url in urls:
                    async with session.get(URL(url, encoded=True)) as r:
                        logging.debug(r.headers)
                        progress = tqdm(total=None, unit='iB', unit_scale=True)
                        while True:
                            chunk = await r.content.read(1024)
                            if not chunk:
                                break
                            await f1.write(chunk)
                            progress.update(len(chunk))
                        progress.close()
                    logging.debug(f"DOWNLOADED SEGMENT TYPE {filetype}")

    if not audioonly:

        logging.debug('downloading video')
        await downloadmanifest(videourls, 'videoinfo/manvideo.ts', 'video')
        logging.debug('downloading audio')
        await downloadmanifest(audiourls, 'videoinfo/manaudio.ts', 'audio')


    else:
        progress = tqdm(total=None, unit='iB', unit_scale=True)
        await downloadmanifest(audiourls, 'videoinfo/manaudio.ts', progress)
        progress.close()
    try:
        if not audioonly:
            subprocess.run(f'ffmpeg -i videoinfo/manvideo.ts -i videoinfo/manaudio.ts -c:v copy {"-c:a copy" if "avc1" in manifest.get("CODECS").split(",")[0] else ""} merged.{extension}'.split(), check=True)

        else:
            subprocess.run(f'ffmpeg -i videoinfo/manaudio.ts merged.{extension}', check=True)

    except Exception as e:
        traceback.print_exc()
        logging.debug('trying again with ffmpeg')
        try:
            subprocess.check_output(f'ffmpeg {"-i "+manifest.get("URL") if not audioonly else ""} -i {manifest.get("AUDIOLINK")} -c:v copy merged.{extension}'.split())
        except Exception as e:
            traceback.print_exc()
    return f'merged.{extension}', extension
