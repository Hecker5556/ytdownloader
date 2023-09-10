from pprint import pformat
import subprocess, os, traceback, asyncio, json
import logging
from extractmanifest import getmanifesturls
import aiohttp, aiofiles
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
    async def downloadmanifest(url: str, filename: str, progress, threads: asyncio.Semaphore, session: aiohttp.ClientSession):
        async with threads:
            async with aiofiles.open(filename, 'wb') as f1:
                while True:
                    try:
                        async with session.get(URL(url, encoded=True), timeout=10) as r:
                            while True:
                                chunk = await r.content.read(1024)
                                if not chunk:
                                    break
                                await f1.write(chunk)
                                progress.update(len(chunk))
                            break
                    except asyncio.exceptions.TimeoutError:
                        await asyncio.sleep(2)
                        continue
                    except Exception as e:
                        logging.debug(str(e) + '\n\n' + url)
                        raise TypeError

    if not audioonly:
        threads = asyncio.Semaphore(5)
        logging.debug('downloading ')
        progress = tqdm(total=totalsize, unit='iB', unit_scale=True)
        async with aiohttp.ClientSession() as session:
            videotasks = [downloadmanifest(url, f'videoinfo/segmentv{index}.ts', progress, threads, session) for index, url in enumerate(videourls)]
            audiotasks = [downloadmanifest(url, f'videoinfo/segmenta{index}.ts', progress, threads, session) for index, url in enumerate(audiourls)]
            await asyncio.gather(*videotasks)
            await asyncio.gather(*audiotasks)
            progress.close()
        async with aiofiles.open(f'videoinfo/manvideo.ts', 'wb') as f1:
            files = []
            for file in os.listdir('videoinfo'):
                if file.startswith('segmentv'):
                    files.append('videoinfo/' + file)
            files = sorted(files, key=lambda x: int(x.split('segmentv')[1].split('.ts')[0]))
            for file in files:
                async with aiofiles.open(file, 'rb') as f2:
                    await f1.write(await f2.read())
        async with aiofiles.open(f'videoinfo/manaudio.ts', 'wb') as f1:
            files = []
            for file in os.listdir('videoinfo'):
                if file.startswith('segmenta'):
                    files.append('videoinfo/' + file)
            files = sorted(files, key=lambda x: int(x.split('segmenta')[1].split('.ts')[0]))
            for file in files:
                async with aiofiles.open(file, 'rb') as f2:
                    await f1.write(await f2.read())

    else:
        progress = tqdm(total=None, unit='iB', unit_scale=True)
        await downloadmanifest(audiourls, 'videoinfo/manaudio.ts', progress)
        progress.close()
        async with aiofiles.open(f'videoinfo/manaudio.ts', 'wb') as f1:
            files = []
            for file in os.listdir('videoinfo'):
                if file.startswith('segmenta'):
                    files.append('videoinfo/' + file)
            files = sorted(files, key=lambda x: int(x.split('segmenta')[1].split('.ts')[0]))
            for file in files:
                async with aiofiles.open(file, 'rb') as f2:
                    await f1.write(await f2.read())
    for i in os.listdir('videoinfo'):
        if i.startswith('segmenta') or i.startswith('segmentv'):
            os.remove('videoinfo/'+i)
    audiobitrate = subprocess.run('ffprobe -v quiet -print_format json -show_format -show_streams -i videoinfo/manaudio.ts'.split(), capture_output=True, text=True)
    audiobitrate = json.loads(audiobitrate.stdout)
    audiobitrate = audiobitrate.get('streams')[0].get('bit_rate')
    try:
        if not audioonly:
            subprocess.run(f'ffmpeg -i videoinfo/manvideo.ts -i videoinfo/manaudio.ts -c:v copy {"-c:a copy" if "avc1" in manifest.get("CODECS").split(",")[0] else f"-b:a {audiobitrate}"} merged.{extension}'.split(), check=True)

        else:
            subprocess.run(f'ffmpeg -i videoinfo/manaudio.ts merged.{extension}', check=True)
    except Exception as e:
        traceback.print_exc()
        logging.debug('trying again with ffmpeg')
        try:
            subprocess.check_output(f'ffmpeg {"-i "+manifest.get("URL") if not audioonly else ""} -i {manifest.get("AUDIOLINK")} -c:v copy merged.{extension}'.split())
        except Exception as e:
            traceback.print_exc()
    return f'merged.{extension}', extension, audiobitrate
