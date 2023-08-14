import requests, json, re, logging, os
from pprint import pformat
from extractmanifest import extractmanifest
from decipher import decrypt
from getjsfunctions import getfunctions
import env
class someerror(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
def getinfo(link: str, verbose: bool = False, manifest: bool = False, premerged: bool = False, nodownload: bool = False):
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")
    logging.info('downloading video info')
    pattern1 = r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([\w-]+)'
    pattern2 = r'(?:https?://)?(?:www\.)?youtu\.be\/([\w-]+)'
    pattern3 = r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([\w-]+)(?:\?feature=[\w]+)?'
    videoid = re.findall(pattern1, link)[0] if re.findall(pattern1, link) else re.findall(pattern2, link)[0] if re.findall(pattern2, link) else re.findall(pattern3, link)[0]
    cookies = {
        "PREF": "hl=en&tz=UTC",
        "CONSENT": "YES+cb.20210328-17-p0.en+FX+789"
    }
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
    
    r = requests.get(f'https://youtube.com/watch?v={videoid}', cookies=cookies, headers=headers)
    logging.info(f'https://youtube.com/watch?v={videoid}')
    rtext = r.text
    pattern = r'var ytInitialPlayerResponse = {.*?"nanos":\d+}}}}'
    matches = re.findall(pattern, rtext, re.DOTALL)
    try:
        matches: str = matches[0]
    except IndexError:
        logging.info('var ytInitialPlayerResponse' in r.text)
        raise someerror(f"idk")
    matches = matches[29:]
    webjson = json.loads(matches)

    needlogin = False
    info: dict = {}
    try:
        for index, i in enumerate(webjson['streamingData']['adaptiveFormats']):
            info[str(index)] = i
        info2: dict = {}
        for index, i in enumerate(webjson['streamingData']['formats']):
            info2[str(index)] = i
    except KeyError:
        logging.debug(webjson['playabilityStatus'].get('status'))
        if webjson['playabilityStatus'].get('status') == 'LOGIN_REQUIRED':
            logging.info('age restricted video, using login details...')
            if not os.path.exists('env.py'):
                logging.info('create a env.py file and place needed details there or run createenv.py, more information in the github docs')
                from sys import exit
                exit()
            with open('env.py', 'r') as f1:
                if len(f1.readlines()) != 7:
                    logging.info('not enough needed information, refer to documents')
                    from sys import exit
                    exit()
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
                        'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36,gzip(gfe)',
                        'clientName': 'WEB',
                        'clientVersion': '2.20230809.00.00',
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
    the = rtext.find("base.js")
    the2 = rtext[the-43:the+7]
    logging.debug(f'found base.js: https://youtube.com{the2}')
    basejslink = f'https://youtube.com{the2}'
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
    if info.get('0'):
        if info.get('0').get('signatureCipher'):
            logging.debug('found unmerged with signatures from web')
            allinks['unmergedsig'] = info
        elif info.get('0').get('url'):
            allinks['unmergednosig'] = info
            logging.debug('found unmerged no signatures from web')
        
        if info2.get('0').get('signatureCipher'):
            logging.debug('found merged with signatures from web')
            allinks['mergedsig'] = info2
        elif info2.get('0').get('url'):
            logging.debug('found merged no signatures from web')
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


        def sortdictbysize(name: str):
            sortedthe = dict(sorted(allinks[name].items(), key=lambda x: int(x[1]['contentLength']), reverse=True))
            sortedthe = {str(idx): item for idx, item in enumerate(sortedthe.values())}
            allinks[name] = sortedthe   
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
                    sortdictbysize('mergednosig')
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
                        sortdictbysize('mergedsig')
        if value.get('streamingData').get('adaptiveFormats'):
            if value.get('streamingData').get('adaptiveFormats')[0].get('url') and not info['0'].get('url'):
                logging.debug('found unmerged formats no signature ' + key)
                for i in range(len(value.get('streamingData').get('adaptiveFormats'))):
                    allinks['unmergednosig'][(str(i))] = value.get('streamingData').get('adaptiveFormats')[i]
                sortdictbysize('unmergednosig')
        sortdictbysize('unmergedsig')
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
