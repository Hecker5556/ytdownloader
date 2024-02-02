import re, aiohttp, logging, json, aiohttp_socks
from aiohttp_socks import ProxyConnector
def checkrestricted(webjson: dict):
    return True if webjson['playabilityStatus'].get('status') == 'LOGIN_REQUIRED' else False
async def getwebjson(link: str, cookies: dict, headers: dict = None, connector: aiohttp.TCPConnector | ProxyConnector = None, proxy: str = None):
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

    pattern1 = r'(?:https?://)?(?:www\.)?(?:m\.)?youtube\.com/watch\?v=([\w-]+)'
    pattern2 = r'(?:https?://)?(?:www\.)?(?:m\.)?youtu\.be\/([\w-]+)'
    pattern3 = r'(?:https?://)?(?:www\.)?(?:m\.)?youtube\.com/shorts/([\w-]+)(?:\?feature=[\w]+)?'
    videoid = re.findall(pattern1, link)[0] if re.findall(pattern1, link) else re.findall(pattern2, link)[0] if re.findall(pattern2, link) else re.findall(pattern3, link)[0]
    if not headers:
        headers = {
            'authority': 'www.youtube.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.5',
            'cache-control': 'max-age=0',
            'sec-ch-ua': '"Not/A)Brand";v="99", "Brave";v="115", "Chromium";v="115"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': '""',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua-platform-version': '"10.0.0"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'sec-gpc': '1',
            'service-worker-navigation-preload': 'true',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        }
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(f'https://youtube.com/watch?v={videoid}', cookies=cookies, headers=headers) as r:
            rtext = await r.text(encoding='utf-8')
    logging.info(f'https://youtube.com/watch?v={videoid}')
    pattern = r'var ytInitialPlayerResponse = (.*?\"nanos\":(?:\d+)}}}})'
    matches = re.findall(pattern, rtext, re.DOTALL)
    try:
        matches: str = matches[0]
    except IndexError:
        logging.info('var ytInitialPlayerResponse' in rtext)
        return False, False, False
    webjson = json.loads(matches)
    the = rtext.find("base.js")
    the2 = rtext[the-43:the+7]
    logging.debug(f'found base.js: https://youtube.com{the2}')
    basejslink = f'https://youtube.com{the2}'
    return webjson, videoid, basejslink
