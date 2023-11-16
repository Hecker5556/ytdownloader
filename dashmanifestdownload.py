import aiohttp, aiofiles, asyncio, os, re
from tqdm.asyncio import tqdm
from datetime import datetime
from getjsfunctions import getfunctions
from decipher import decrypt
import logging
async def download(info: dict) -> tuple:
    segments = int(info.get('segments'))
    links = []
    for i in range(segments):
        links.append(info.get('url') + f'&sq={i}')
    extension = 'mp4' if 'avc1' in info.get('mimeType') else 'webm'
    progress = tqdm(total=int(info.get('contentLength')), unit='iB', unit_scale=True)
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit_per_host=10)) as session:
        tasks = [downloadworker(link, f'videoinfo/segmentv{index}.{extension}', session, progress) for index, link in enumerate(links)]
        await asyncio.gather(*tasks)
    progress.close()
    filelist = os.listdir('videoinfo')
    segmentlist = []
    filename = f'tempvideo{round(datetime.now().timestamp())}.{extension}'
    async with aiofiles.open(filename, 'wb') as f1:
        for file in filelist:
            if file.startswith('segmentv') and file.endswith(extension):
                segmentlist.append('videoinfo/' + file)
        segmentlist = sorted(segmentlist, key=lambda x: int(x.split('segmentv')[1].split('.')[0]))
        for file in segmentlist:
            async with aiofiles.open(file, 'rb') as f2:
                await f1.write(await f2.read())
            os.remove(file)
    return filename, extension
    
async def extractinfo(info: dict, length) -> dict:
    info["contentLength"] = length * info["bitrate"]
    return info

async def downloadworker(link: str, filename: str, session: aiohttp.ClientSession, progress: tqdm):

    while True:
        try:
            async with aiofiles.open(filename, 'wb') as f1:
                async with session.get(link, timeout=10) as r:
                    while True:
                        chunk = await r.content.read(1024)
                        if not chunk:
                            break
                        await f1.write(chunk)
                        progress.update(len(chunk))
                    break

        except asyncio.TimeoutError:
            continue

if __name__ == "__main__":
    info = {'itag': 247,
            'url': 'https://rr4---sn-2va3vhuxa-f5fz.googlevideo.com/videoplayback?expire=1695072255&ei=n2sIZdzYLsaSv_IPvYe-qAI&ip=78.30.66.220&id=o-AK65uGlwM2ITBUsla3A6y-64G5j2Z_3nM4bGGwvAz4JR&itag=247&aitags=133%2C134%2C135%2C136%2C160%2C242%2C243%2C244%2C247%2C278&source=yt_otf&requiressl=yes&mh=eV&mm=31%2C29&mn=sn-2va3vhuxa-f5fz%2Csn-f5f7kn7z&ms=au%2Crdu&mv=m&mvi=4&pl=21&initcwndbps=426250&spc=UWF9fwpBHVQ7DpRYHkcHpGoUDfbcbHoMdiiVoUc9pw&vprv=1&svpuc=1&mime=video%2Fwebm&ns=C4gwVwAhgqJg43vWYs5W-WkP&otf=1&otfp=1&dur=0.000&lmt=1547509493846281&mt=1695050242&fvip=1&keepalive=yes&fexp=24007246&beids=24350017&c=WEB&n=VrrNYIlag0fb3VE&sparams=expire%2Cei%2Cip%2Cid%2Caitags%2Csource%2Crequiressl%2Cspc%2Cvprv%2Csvpuc%2Cmime%2Cns%2Cotf%2Cotfp%2Cdur%2Clmt&sig=AOq0QJ8wRQIhANixvxjAN8Jq1AkEQI6aoM-cXNdLPFJZJIuigVu7J5rLAiByMYqsFeHO1PlsT1SGkEt6MFRK9_uuzWinhywkTAsJYw%3D%3D&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=AG3C_xAwRQIhAM-3F2UY18TYwPChlEMTTjQrLHa4bp95r7Pn8qN9UlXjAiByHAKILz3L-3H4wRrzyIoCgy-XQ4XYKwcpKFVipsO-sA%3D%3D',
            'mimeType': 'video/webm; codecs="vp9"',
            'bitrate': 1505280,
            'width': 1280,
            'height': 720,
            'lastModified': '1547509493846281',
            'quality': 'hd720',
            'fps': 30,
            'qualityLabel': '720p',
            'projectionType': 'RECTANGULAR',
            'type': 'FORMAT_STREAM_TYPE_OTF',
            'contentLength': 16280496,
            'segments': '334'}
    
    asyncio.run(download(info))