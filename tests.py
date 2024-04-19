from ytdownload import ytdownload
import asyncio, json
import aiohttp
LINKS = {
    "normal": "https://youtu.be/amXl7FG7J4c",
    "music": "https://youtu.be/IXP18B7DNwM",
    "age restricted": "https://youtu.be/3gdY05pyRCw", #not nsfw
    "playlist": "https://youtube.com/playlist?list=PLdoMQKNfIfytPz_qtUWoZC0mBONwu05rp&si=MZRF5-TVqrLyaMQD"
}

async def normal(url: str):
    async with ytdownload() as norm:
        result = await norm.download(url)
    print(json.dumps(result, indent=4))
    return result

async def grab(url: str):
    async with ytdownload(**{"nodownload": True}) as ginfo:
        table = await ginfo.download(url)
        info = ginfo.all_formats
    with open("video_info.txt", "w") as f1:
        f1.write(json.dumps(info, indent=4))
        f1.write("\n")
        f1.write(table.get_string())

async def searchyt(query: str):
    async with ytdownload(query=query) as ytsearch:
        await ytsearch.search()
        for vid in ytsearch.videos:
            print(vid)
    
async def own_session():
    async with aiohttp.ClientSession() as session:
        async with ytdownload() as ydl:
            ydl.session = session
            await ydl.download(LINKS['normal'])

asyncio.run(own_session())