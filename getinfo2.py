import requests, json, re, logging, os, sys, aiohttp
from pprint import pformat
from extractmanifest import extractmanifest
from decipher import decrypt
from getjsfunctions import getfunctions
from datetime import datetime
from checkrestricted import checkrestricted, getwebjson
from dashmanifestdownload import extractinfo
class someerror(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
async def getinfo(link: str, verbose: bool = False, manifest: bool = False, 
                  premerged: bool = False, nodownload: bool = False):
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")
    logging.info('downloading video info')
    cookies = {
        "PREF": "f4=4000000&f6=40000000&tz=Europe.Warsaw&f5=30000&f7=100",
        "CONSENT": "PENDING+915"
    }
    webjson, videoid, basejslink = await getwebjson(link, cookies)
    if not webjson:
        raise someerror("idk")

    needlogin = False
    info: dict = {}
    from pprint import pprint
    try:
        for index, i in enumerate(webjson['streamingData']['adaptiveFormats']):
            info[str(index)] = i
        info2: dict = {}
        for index, i in enumerate(webjson['streamingData']['formats']):
            info2[str(index)] = i
    except KeyError:
        logging.debug(webjson['playabilityStatus'].get('status'))
        if checkrestricted(webjson):
            logging.info('age restricted video, using login details for api requests...')
            try:
                import env
            except ModuleNotFoundError:
                logging.info('do python createenv.py and read github docs')
                sys.exit()
            logcookies = {
                'SID': env.SID,
                'HSID': env.HSID,
                'SSID': env.SSID,
                'APISID': env.APISID,
                'SAPISID': env.SAPISID,
            }

            logheaders = {
                'authority': 'www.youtube.com',
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.7',
                'authorization': env.authorization,
                'content-type': 'application/json',
                'origin': 'https://www.youtube.com',
                'sec-ch-ua': '"Not/A)Brand";v="99", "Brave";v="115", "Chromium";v="115"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-model': '""',
                'sec-ch-ua-platform': '"Windows"',
                'sec-ch-ua-platform-version': '"10.0.0"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'same-origin',
                'sec-fetch-site': 'same-origin',
                'sec-gpc': '1',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
                'x-goog-authuser': '0',
                'x-origin': 'https://www.youtube.com',
                'x-youtube-bootstrap-logged-in': 'true',
            }

            logparams = {
                'key': env.apikey,
                'prettyPrint': 'false',
            }

            logjson_data = {
                'context': {
                    'client': {
                        'hl': 'en',
                        'gl': 'PL',
                        'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
                        'clientName': 'WEB',
                        'clientVersion': '2.20231030.04.00',
                        'acceptHeader': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    },
                    'user': {
                        'lockedSafetyMode': False,
                    },

                },
                'videoId': videoid,
                'playbackContext': {
                    'contentPlaybackContext': {
                        'html5Preference': 'HTML5_PREF_WANTS',
                    },
                },
                'racyCheckOk': True,
                'contentCheckOk': True,
            }

            r2 = requests.post(
                'https://www.youtube.com/youtubei/v1/player',
                params=logparams,
                cookies=logcookies,
                headers=logheaders,
                json=logjson_data,
            )
            
            try:
                webjson = json.loads(r2.text)
            except:
                logging.info(r2.text)
            try:
                for index, i in enumerate(webjson['streamingData']['adaptiveFormats']):
                    info[str(index)] = i
                info2: dict = {}
                for index, i in enumerate(webjson['streamingData']['formats']):
                    info2[str(index)] = i
                needlogin = True
            except KeyError:
                logging.info(f'no idea tbh\n{webjson}')
    otherinfo: dict = {}
    for key, value in webjson["videoDetails"].items():
        otherinfo[key] = value
    if not os.path.exists('videoinfo'):
        os.mkdir('videoinfo')
    with open('videoinfo/otherinfo.json', 'w') as f1:
        json.dump(otherinfo, f1)
    headers = {
        'authority': 'www.youtube.com',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.7',
        'content-type': 'application/json',
        'origin': 'https://www.youtube.com',
        'referer': link, #link
        'sec-ch-ua': '"Not/A)Brand";v="99", "Brave";v="115", "Chromium";v="115"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-platform': '"Windows"',
        'sec-ch-ua-platform-version': '"10.0.0"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'sec-gpc': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'x-goog-authuser': '0',
        'x-origin': 'https://www.youtube.com',
        'x-youtube-bootstrap-logged-in': 'true',
    }

    logging.info(f'videoid: {videoid}')
    clients: dict ={'IOS': {'clientVersion': '17.33.2', 
                            'userAgent': 'com.google.ios.youtube/17.33.2 (iPhone14,3; U; CPU iOS 15_6 like Mac OS X)',
                            'apikey': 'AIzaSyB-63vPrdThhKuerbB2N_l7Kwwcxj6yUA',
                            'deviceModel': 'iPhone14,3'},
                    'XBOXONEGUIDE': {'clientVersion': '1.0',
                                     'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; Xbox; Xbox One) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.10553',
                                     'apikey': 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'}}    
    responses: dict = {}
    allinks: dict = {'manifest': {},
                     'unmergednosig': {},
                     'mergednosig': {},
                     'mergedsig': {},
                     'unmergedsig': {}}
    async def sortdictbysize(name: str):
        tempdict = {}
        length = int(otherinfo.get('lengthSeconds'))
        for key, value in allinks[name].items():
            try:
                tempdict[key] = int(value["contentLength"])
            except Exception as e:
                logging.debug(f"some error occured when sorting key {key} and name {name}: {e}")
                value["contentLength"] = (length * value["bitrate"])/8
                tempdict[key] = int(value["contentLength"])

        newdict = {}
        arr = list(tempdict.items())
        for i in range(len(tempdict.keys())):
            minindex = i
            for j in range(i, len(tempdict.keys())):
                if arr[j][1] < arr[minindex][1]:
                    minindex = j
            arr[i], arr[minindex] = arr[minindex], arr[i]
        for key, value in arr:
            newdict[key] = value

        tempdict = {}
        for index, key in enumerate(reversed(newdict.keys())):
            tempdict[str(index)] = allinks[name][key]

        allinks[name] = tempdict
    if info.get('0'):
        if info.get('0').get('signatureCipher'):
            logging.debug('found unmerged with signatures from web')
            allinks['unmergedsig'] = info
            await sortdictbysize("unmergedsig")
        elif info.get('0').get('url'):
            allinks['unmergednosig'] = info
            logging.debug('found unmerged no signatures from web')
            await sortdictbysize("unmergednosig")
        if info2.get('0').get('signatureCipher'):
            logging.debug('found merged with signatures from web')
            allinks['mergedsig'] = info2
            try:
                await sortdictbysize("mergedsig")
            except:
                pass
        elif info2.get('0').get('url'):
            logging.debug('found merged no signatures from web')
            try:
                await sortdictbysize("mergednosig")
            except:
                pass
    else:
        logging.debug('couldnt find anything from webpage')
    logging.debug('downloading apis')
    for key, value in clients.items():
        logging.debug(f'downloading {key} api')
        json_data = {
            'videoId': videoid,
            'context': {
                'client': {
                    'hl': 'en',
                    'userAgent': value.get('userAgent'),
                    'clientName': key,
                    'clientVersion': value.get('clientVersion'),
                    'acceptHeader': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    },
                'user': {
                    'lockedSafetyMode': False,
                },
                "playbackContext": {
                    "contentPlaybackContext": {
                        "html5Preference": "HTML5_PREF_WANTS"
                        }
                        }},
                        "contentCheckOk": True, 
                        "racyCheckOk": True}
        if 'IOS' in key:
            json_data['context']['client']['deviceModel'] = value.get('deviceModel')
        params = {
        'key': value.get('apikey') if not needlogin else env.apikey,
        'prettyPrint': 'false',
        }
        response = requests.post(
            'https://www.youtube.com/youtubei/v1/player/',
            params=params,
            json=json_data, cookies=cookies if not needlogin else logcookies, headers=headers if not needlogin else logheaders
        )
        logging.debug(params)
        logging.debug(json_data)
        logging.debug(headers if not needlogin else logheaders)
        logging.debug(cookies if not needlogin else logcookies)
        responses[key] = json.loads(response.text)
    for count, (key, value) in enumerate(responses.items()):        
        if value.get('streamingData') == None:
            logging.debug(f'\n\n\nNONE AVALIABLE {key}\n\n\n')
            # with open(f'{key}response.txt', 'w') as f1:
            #     json.dump(responses[key], f1)
            continue
        
        
        if value.get('streamingData').get('hlsManifestUrl') and manifest:
            allinks['manifest'] = extractmanifest(value.get('streamingData').get('hlsManifestUrl'), nodownload=nodownload, duration=float(info['0'].get('approxDurationMs'))/1000)
        else:
            if value.get('streamingData').get('hlsManifestUrl'):
                allinks['manifest']['0'] = value.get('streamingData').get('hlsManifestUrl')



        if value.get('streamingData').get('formats'):
            if value.get('streamingData').get('formats')[0].get('url'):
                logging.debug('found merged formats unsignatured ' + key)
                for i in range(len(value.get('streamingData').get('formats'))):
                    allinks['mergednosig'][str(i)] = value.get('streamingData').get('formats')[i]
                if premerged:
                    logging.debug('adding content lengths to merged formats')
                    for index, i in enumerate(value.get('streamingData').get('formats')):
                        if i.get('contentLength'):
                            continue
                        r = requests.get(i.get('url'), stream=True)
                        contentlength = r.headers.get('content-length')
                        allinks['mergednosig'][str(index)]['contentLength'] = contentlength
                    await sortdictbysize('mergednosig')
            else:
                if value.get('streamingData').get('formats')[0].get('signatureCipher'):
                    logging.debug('found merged formats signatured' + key)
                    for i in range(len(value.get('streamingData').get('formats'))):
                        allinks['mergedsig'][str(i)] = value.get('streamingData').get('formats')[i]
                    if premerged:
                        logging.debug('adding content lengths to merged formats')
                        for index, i in enumerate(value.get('streamingData').get('formats')):
                            if i.get('contentLength'):
                                continue
                            functions = getfunctions(basejslink, verbose=verbose)
                            url = decrypt(i.get('signatureCipher'), functions=functions, verbose=verbose, needlogin=needlogin)
                            r = requests.get(url, stream=True)
                            contentLength = r.headers.get('content-length')
                            allinks['mergedsig'][str(index)]['contentLength'] = contentLength
                            allinks['mergedsig'][str(index)]['url'] = url
                        await sortdictbysize('mergedsig')
        if value.get('streamingData').get('adaptiveFormats'):
            try:
                if value.get('streamingData').get('adaptiveFormats')[0].get('url') and not info['0'].get('url'):
                    logging.debug('found unmerged formats no signature ' + key)
                    for i in range(len(value.get('streamingData').get('adaptiveFormats'))):
                        allinks['unmergednosig'][(str(i))] = value.get('streamingData').get('adaptiveFormats')[i]
                    await sortdictbysize('unmergednosig')

                elif value.get('streamingData').get('adaptiveFormats')[0].get('signatureCipher') and not info['0'].get('signatureCipher'):
                    logging.debug('found unmerged formats with signature ' + key)
                    for i in range(len(value.get('streamingData').get('adaptiveFormats'))):
                        allinks['unmergedsig'][(str(i))] = value.get('streamingData').get('adaptiveFormats')[i]
                    logging.debug("sorting unmergedsig")
                    await sortdictbysize('unmergedsig')
                elif info['0'].get('url'):
                    segmentcount = None
                    for k, v in allinks['unmergednosig'].items():
                        async with aiohttp.ClientSession() as session:
                            if not v.get('contentLength'):
                                    async with session.get(v.get('url')) as r:
                                        if r.headers.get('content-length'):
                                            v['contentLength'] = r.headers.get('content-length')
                                            allinks['unmergednosig'][k] = v


                    await sortdictbysize('unmergednosig')
                elif info['0'].get('signatureCipher'):
                    await sortdictbysize('unmergedsig')
            except Exception as e:
                print(e)
                print(info)
        # pprint(value.get('streamingData').get('formats') if value.get('streamingData').get('formats') else 'no premerged formats')

    # pprint(allinks, sort_dicts=False, indent=4)
    logging.debug('\n-----checking if everything needed is there-----\n')
    needed = ['manifest', 'unmergednosig', 'mergednosig','mergedsig', 'unmergedsig']
    for i in needed:
        if allinks.get(i):
            logging.debug(f"{i} is present")
        else:
            logging.info(f"{i} not present")
    logging.debug('\n\n\n')
 
    logging.debug('writing links as file')
    if not os.path.exists('videoinfo'):
        os.mkdir('videoinfo')
    with open('videoinfo/allinksformatted.txt', 'w') as f1:
        f1.write(pformat(allinks, sort_dicts=False))
    with open('videoinfo/allinks.txt', 'w') as f1:
        json.dump(allinks, f1)
    return allinks, otherinfo, basejslink, needlogin



# print(manifestdownload(a['manifest'][0]))
