import aiohttp, aiofiles, os, asyncio, logging
from tqdm.asyncio import tqdm
from aiohttp_socks import ProxyConnector
async def betterparallel(link: str, filename: str, connector = None, proxy = None, totalsize: int = 0):
    # async with aiohttp.ClientSession(connector=connector) as session:
    #     async with session.get(link, proxy=proxy if proxy and proxy.startswith("https") else None) as response:
    #         totalsize = int(response.headers.get('content-length'))
    tenmb = 10*1024*1024
    chunksize, remainder = divmod(totalsize, tenmb)
    logging.debug((chunksize, remainder))
    startbyte = 0
    progress = tqdm(total=totalsize, unit='B', unit_scale=True)
    connector = aiohttp.TCPConnector()
    if proxy:
        if "socks" in proxy:
            if "socks5h" in proxy:
                prox = proxy.replace("socks5h", "socks5")
                connector = ProxyConnector.from_url(url=prox)
            else:
                connector = ProxyConnector.from_url(url=proxy)
        else:
            connector = aiohttp.TCPConnector()
    async with aiohttp.ClientSession(connector=connector) as session:
        for i in range(chunksize +1):
            endbyte = startbyte + tenmb - 1
            if i == chunksize:
                endbyte += startbyte + remainder -1
            await parallelworker(link=link, filename=filename, startbyte=startbyte, endbyte=endbyte, progress=progress, session=session, proxy=proxy)
            startbyte = endbyte + 1
        
        progress.close()
    return filename, os.path.splitext(filename)[1].replace('.', '')

async def parallelworker(link:str, filename:str, startbyte: int, endbyte: int, progress, session: aiohttp.ClientSession, proxy: str = None):
    headers = {'range': f'bytes={startbyte}-{endbyte}'}
    if not os.path.exists(filename):
        async with aiofiles.open(filename, 'w') as f1:
            pass
    async with aiofiles.open(filename, 'ab') as f1:
        async with session.get(link, headers=headers, proxy=proxy if proxy and proxy.startswith("https") else None) as response:
            if response.status != 200 and response.status != 206:
                print('failed to download' + str(response.status))
                return
            while True:
                chunk = await response.content.read(1024)
                if not chunk:
                    break
                await f1.write(chunk)
                progress.update(len(chunk))


                