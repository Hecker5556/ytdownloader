import aiohttp, json

async def main(query: str) -> dict:
    headers = {
        'authority': 'www.youtube.com',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/json',
        'origin': 'https://www.youtube.com',
        'referer': f'https://www.youtube.com/results?search_query={query}',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        'x-origin': 'https://www.youtube.com',
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
                'clientVersion': '2.20230829.01.01',
                'originalUrl': f'https://www.youtube.com/results?search_query={query}',
                'platform': 'DESKTOP',
                'acceptHeader': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',

            },

            
        },
        'query': query,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post('https://www.youtube.com/youtubei/v1/search', headers=headers, params=params, json=json_data) as r:
            responsejson = await r.json()
    videos = {}
    for result in responsejson['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']:
        if result.get('videoRenderer'):
            videos[result['videoRenderer']['title']['runs'][0]['text']] = f"https://youtube.com/watch?v={result['videoRenderer']['videoId']}"
    return videos

if __name__ == '__main__':
    import asyncio
    print(asyncio.run(main('blonde')))
