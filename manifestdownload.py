from pprint import pformat
import subprocess, os, traceback, asyncio, json
import logging
from extractmanifest import getmanifesturls
import aiohttp, aiofiles
from yarl import URL
from tqdm.asyncio import tqdm
from datetime import datetime

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
    async def downloadmanifest(url: str, filename: str, progress, session: aiohttp.ClientSession):
        while True:
            try:
                async with aiofiles.open(filename, 'wb') as f1:
                    async with session.get(URL(url, encoded=True), timeout=10) as r:
                        if r.status != 200 and r.status != 206:
                            logging.debug('bad status code, waiting for 2 seconds')
                            await asyncio.sleep(2)
                            continue
                        while True:
                            chunk = await r.content.read(1024)
                            if not chunk:
                                break
                            await f1.write(chunk)
                            progress.update(len(chunk))
                        break
            except asyncio.exceptions.TimeoutError:
                logging.debug("timedout, trying again for filename: ", filename)
                continue
            except Exception as e:
                logging.debug(str(e) + '\n\n' + url)
                raise TypeError

    currentdate = round(datetime.now().timestamp())
    if not audioonly:
        # threads = asyncio.Semaphore(5)
        logging.debug('downloading ')
        progress = tqdm(total=totalsize, unit='iB', unit_scale=True)
        async with aiohttp.ClientSession() as session:
            videofilenames = []
            audiofilenames = []
            logging.debug("downloading video")
            for index, vurl in enumerate(videourls):
                await downloadmanifest(vurl, f'videoinfo/segmentv{index}-{currentdate}.ts', progress, session)
                videofilenames.append(f'videoinfo/segmentv{index}-{currentdate}.ts')
            logging.debug("video downloaded")
            logging.debug("downloading audio")
            for index, aurl in enumerate(audiourls):
                await downloadmanifest(aurl, f'videoinfo/segmenta{index}-{currentdate}.ts', progress, session)
                audiofilenames.append(f'videoinfo/segmenta{index}-{currentdate}.ts')
            progress.close()
            logging.debug("downloaded audio")
        async with aiofiles.open(f'videoinfo/manvideo-{currentdate}.ts', 'wb') as f1:
            for file in videofilenames:
                async with aiofiles.open(file, 'rb') as f2:
                    await f1.write(await f2.read())
        async with aiofiles.open(f'videoinfo/manaudio-{currentdate}.ts', 'wb') as f1:
            for file in audiofilenames:
                async with aiofiles.open(file, 'rb') as f2:
                    await f1.write(await f2.read())

    else:
        progress = tqdm(total=None, unit='iB', unit_scale=True)
        audiofilenames = []
        async with aiohttp.ClientSession() as session:
            for index, aurl in enumerate(audiourls):
                await downloadmanifest(aurl, f'videoinfo/segmenta{index}-{currentdate}.ts', progress, session)
                audiofilenames.append(f'videoinfo/segmenta{index}-{currentdate}.ts')
                progress.close()
        async with aiofiles.open(f'videoinfo/manaudio-{currentdate}.ts', 'wb') as f1:
            for file in audiofilenames:
                async with aiofiles.open(file, 'rb') as f2:
                    await f1.write(await f2.read())
    for vfile, afile in zip(videofilenames, audiofilenames):
        os.remove(vfile)
        os.remove(afile)
    audiobitrate = subprocess.run(f'ffprobe -v quiet -print_format json -show_format -show_streams -i videoinfo/manaudio-{currentdate}.ts'.split(), capture_output=True, text=True)
    audiobitrate = json.loads(audiobitrate.stdout)
    audiobitrate = audiobitrate.get('streams')[0].get('bit_rate')
    try:
        if not audioonly:
            subprocess.run(f'ffmpeg -i videoinfo/manvideo-{currentdate}.ts -i videoinfo/manaudio-{currentdate}.ts -loglevel error -c:v copy {"-c:a copy" if "avc1" in manifest.get("CODECS").split(",")[0] else f"-b:a {audiobitrate}"} merged{currentdate}.{extension}'.split(), check=True)

        else:
            subprocess.run(f'ffmpeg -i videoinfo/manaudio-{currentdate}.ts -loglevel error merged{currentdate}.{extension}', check=True)
    except Exception as e:
        traceback.print_exc()
        logging.debug('trying again with ffmpeg')
        try:
            subprocess.check_output(f'ffmpeg {"-i "+manifest.get("URL") if not audioonly else ""} -i {manifest.get("AUDIOLINK")} -loglevel error -c:v copy merged{currentdate}.{extension}'.split())
        except Exception as e:
            traceback.print_exc()
    os.remove(f'videoinfo/manvideo-{currentdate}.ts')
    os.remove(f'videoinfo/manaudio-{currentdate}.ts',)
    return f'merged{currentdate}.{extension}', extension, audiobitrate
