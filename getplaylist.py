import aiohttp
class getplaylist:
    class unavaliable(Exception):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)
    async def getplaylist(url) -> list:
        playlistid = url.split('list=')[1].split('&')[0]
        headers = {
            'authority': 'www.youtube.com',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.6',
            'content-type': 'application/json',
            'origin': 'https://www.youtube.com',
            'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Brave";v="116"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': '""',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua-platform-version': '"10.0.0"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'same-origin',
            'sec-fetch-site': 'same-origin',
            'sec-gpc': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        }
        params = {
            'key': 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8',
            'prettyPrint': 'false',
        }
        json_data = {
            'context': {
                'client': {
                    'hl': 'en',
                    'gl': 'PL',
                    'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36,gzip(gfe)',
                    'clientName': 'WEB',
                    'clientVersion': '2.20230831.09.00',
                    'acceptHeader': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                },



            },
            'playlistId': playlistid,
            'racyCheckOk': False,
            'contentCheckOk': False,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post('https://www.youtube.com/youtubei/v1/next', params=params, headers=headers, json=json_data) as session:
                responsejson = await session.json()
        if not responsejson.get('contents', {}).get('twoColumnWatchNextResults', {}).get('playlist', {}):
            raise getplaylist.unavaliable(f'playlist not avaliable!')
        responsejson = responsejson['contents']['twoColumnWatchNextResults']['playlist']['playlist']['contents']

        return [f'https://youtube.com/watch?v={i["playlistPanelVideoRenderer"]["videoId"]}' for i in responsejson if not i.get('messageRenderer')]

if __name__ == '__main__':
    import asyncio
    print("\n".join(asyncio.run(getplaylist.getplaylist('https://youtube.com/playlist?list=PLdoMQKNfIfytnI8QNoPvfSB79LJxdGRVG&si=NxWM_EvIcU49nAfQ'))))