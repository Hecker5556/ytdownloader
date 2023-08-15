import aiohttp, aiofiles, os
from tqdm.asyncio import tqdm
from betterparallel import betterparallel
async def normaldownload(link: str, filename: str):
    headers = {'range': 'bytes=0-',
               'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(link, headers=headers) as response:
                totalsize = int(response.headers.get('content-length'))
                if totalsize > 10*1024*1024: #unthrottled when under 10mb idk
                    a = await betterparallel(link, filename)
                    return a
                progress = tqdm(total=totalsize, unit='B', unit_scale=True)
                async with aiofiles.open(filename, 'wb') as f1:
                    while True:
                        chunk = await response.content.read(1024)
                        if not chunk:
                            break
                        await f1.write(chunk)
                        progress.update(len(chunk))
                    progress.close()
        except TypeError:
            print(link)
    return filename, os.path.splitext(filename)[1].replace('.', '')
