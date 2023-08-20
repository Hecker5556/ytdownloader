import requests, logging, queue, threading, asyncio
import aiohttp
from yarl import URL
from readmanifestduration import totalfilesize
async def getmanifesturls(url: str):
    if url == None:
        raise requests.ConnectionError(f"{url} url is NONE for some reason")
    async with aiohttp.ClientSession() as session:
        async with session.get(URL(url, encoded=True)) as r:
            logging.debug(r.status)
    # r = requests.get(url)
            urls = await r.text()
            urls = urls.split('\n')
            urls = [i for i in urls if i.startswith('https')]
            logging.debug('got urls')
            return urls

def extractmanifest(link: str, nodownload: bool = False, duration: float = None):
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
        allinks: dict = {'manifest': {}}
        r = requests.get(link)


        entries = r.text.split('#EXT-X-STREAM-INF:')[1:]
        audios = r.text.split('#EXT-X-STREAM-INF:')[0]
        audiolinks: dict = {}
        for i in audios.split('\n'):
            if i.startswith('#EXT-X-MEDIA:URI="https'):
                audiolink = i.split('#EXT-X-MEDIA:URI="')[1].split('",')[0]
                audioid = [x.split('=')[1] for x in i.split('#EXT-X-MEDIA:URI="')[1].split(',') if x.startswith('GROUP-ID')]
                
                audiolinks[audioid[0].replace('"', '')] = audiolink

        parsedvalues: dict = {}
        for index, entry in enumerate(entries):
            entry_parts = entry.split(',')
            infodict = {}
            url = ""
            for i, ent in enumerate(entry_parts):
                ent = ent.split('=')
                if ent[0] == 'BANDWIDTH':
                    infodict['BANDWIDTH'] = ent[1]
                elif ent[0] == 'CODECS':
                    codecs_value = ','.join(entry_parts[i:i+2])  # Combine two parts of codecs value
                    infodict['CODECS'] = codecs_value.split('=')[1].replace('"', '')
                elif ent[0] == 'RESOLUTION':
                    infodict['RESOLUTION'] = ent[1]
                elif ent[0] == 'FRAME-RATE':
                    infodict['FRAME-RATE'] = ent[1]
                elif ent[0] == 'VIDEO-RANGE':
                    infodict['VIDEO-RANGE'] = ent[1]
                elif ent[0] == 'AUDIO':
                    infodict['AUDIO'] = ent[1].replace('"', '')
                    if ent[1].replace('"', '') in audiolinks:
                        for key1, value1 in audiolinks.items():
                            if key1 == ent[1].replace('"', ''):
                                infodict['AUDIOLINK'] = value1
                elif ent[0] == 'CLOSED-CAPTIONS':
                    infodict['CLOSED-CAPTIONS'] = ent[1].split('\n')[0]
                    url = ent[1].split('\n')[1] 
                else:
                    url += ',' + ent[0]
            infodict['URL'] = url.strip()
            infodict['MAINURL'] = link
            infodict['FILESIZE'] = totalfilesize(infodict, duration)
            parsedvalues[str(index)] = infodict

        allinks['manifest'] = parsedvalues
        sorted_manifest = dict(sorted(allinks['manifest'].items(), key=lambda x: float(x[1]['FILESIZE']), reverse=True))
        sorted_manifest = {idx: item for idx, item in enumerate(sorted_manifest.values())}
        allinks['manifest'] = sorted_manifest


        return allinks['manifest']
