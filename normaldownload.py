import aiohttp, aiofiles, os
from tqdm.asyncio import tqdm
from betterparallel import betterparallel
from aiohttp_socks import ProxyConnector
async def normaldownload(link: str, filename: str, connector = None, proxy = None):
    headers = {'range': 'bytes=0-',
               'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',}
    connector = aiohttp.TCPConnector()
    if proxy:
        if "socks" in proxy:
            if "socks5h" in proxy:
                prox = proxy.replace("socks5h", "socks5")
                connector = ProxyConnector.from_url(url=prox)
            else:
                connector = ProxyConnector.from_url(url=proxy)
        else:
            connector = aiohttp.TCPConnector(proxy=proxy)
    try:
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(link, headers=headers) as response:
                totalsize = int(response.headers.get('content-length'))
                if totalsize > 10*1024*1024: #unthrottled when under 10mb idk
                    a = await betterparallel(link, filename, connector, proxy)
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
