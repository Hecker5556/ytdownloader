import asyncio, aiohttp, aiofiles, json, re, prettytable, logging, os
from aiohttp_socks import ProxyConnector
from tqdm import tqdm
from datetime import datetime
from urllib.parse import unquote
from copy import deepcopy
from yarl import URL
LINKPATTERN_DEFAULT = r'(?:https?://)?(?:www\.)?(?:m\.)?youtube\.com/watch\?v=[\w-]+'
LINKPATTERN_MOBILE = r'(?:https?://)?(?:www\.)?(?:m\.)?youtu\.be/[\w-]+'
LINKPATTERN_SHORTS = r'(?:https?://)?(?:www\.)?(?:m\.)?youtube\.com/shorts/[\w-]+(?:\?feature=[\w]+)?'
LINKPATTERN_PLAYLIST = r'(?:https://)?(?:www\.)?youtube\.com/playlist\?list=(?:.*?)$'
LINKPATTERNLIST = [LINKPATTERN_PLAYLIST, LINKPATTERN_DEFAULT, LINKPATTERN_MOBILE, LINKPATTERN_SHORTS]
class ytdownload:
    class missing_node(Exception):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)
    def __init__(self, **kwargs):
        """
        Download YouTube videos and extract information.
        
        [GitHub Page](https://github.com/Hecker5556/ytdownloader.git)
        
        Arguments:
            link (str): YouTube video link.
            
            verbose (bool, optional): Whether to log connections and additional info. Default is False.
            
            manifest (bool, optional): Extract manifest info, download manifest chunks, and merge into a video.
            Default is False.
            
            maxsize (int, optional): Maximum size of output in MB. Default is None.
            
            premerged (bool, optional): Whether to download premerged videos. Default is False.
            
            codec (str, optional): One of ['vp9', 'avc1', 'av01', None].
            Downloads a video with the specific codec. Default is None.
            
            nodownload (bool, optional): Whether to only get information from the video and not download it.
            URLs aren't deciphered. Default is False. Returns a prettytable variable.
            
            priority (str, optional): When finding the best format under max size, prioritize 'video', 'audio', or 'none'.
            Default is 'video'.
            
            audioonly (bool, optional): Download only the audio. Default is False.
            
            mp3audio (bool, optional): Download audio in MP3 format. Automatically sets audioonly to True.
            Default is False.

            itag (int, optional): Download specific itag and the video/audio with it

            onlyitag (bool, optional): whether to download only that specific itag

            filename (str, optional): set output filename

            start (str, optional): set timestamp at which the video should start HH:MM:SS/MM:SS

            end (str, optional): set timestamp at which video should end HH:MM:SS/MM:SS
            
            returnurlonly (bool, optional): doesnt download the video, only returns the decypted url

            proxy (str, optional): proxy to use, supports https/socks

            overwrite (bool, optional): overwrite a file that has the same filename

            check_decipher (bool, optional): whether to check if deciphering was successful (can get ratelimited when downloading playlist)

            search (str, optional): query to search on youtube
        """
        self.link = None
        self.playlist = False
        if kwargs.get("link"):
            link = kwargs.get("link")
            for ptn in LINKPATTERNLIST:
                match = re.findall(ptn, link)
                if match:
                    self.link = match[0]
                    break
            if not self.link:
                raise ValueError(f"Provided link isn't valid")
        if self.link and "playlist?" in self.link:
            self.playlist = True
            self.link = link
        self.verbose = False
        self.manifest = False
        self.maxsize = None
        self.premerged = False
        self.codec = None
        self.nodownload = False
        self.priority = 'video'
        self.audioonly = False
        self.mp3audio = False
        self.itag = None
        self.onlyitag = False
        self.filename = None
        self.start = None
        self.end = None
        self.returnurlonly = False
        self.proxy = None
        self.overwrite = True
        self.logger = None
        self.check_decipher = False
        self.query = None
        self.progress = None
        self.session = None
        self.title = None
        for key, value in kwargs.items():
            if value == None:
                continue
            match key:
                case "link":
                    continue
                case "verbose":
                    if isinstance(value, bool) and value == True and not self.logger:
                        logging.basicConfig(level=logging.DEBUG, format="[%(asctime)s] - %(message)s, line %(lineno)d", datefmt='%H:%M:%S')
                        self.logger = logging.getLogger(__name__)
                    elif isinstance(value, bool) and value == False or value == None and not self.logger:
                        logging.basicConfig(level=logging.INFO, format="[%(asctime)s] - %(message)s, line %(lineno)d", datefmt='%H:%M:%S')
                        self.logger = logging.getLogger(__name__)
                    else:
                        print(f"{key}={value} is not a valid argument")
                case "manifest":
                    if isinstance(value, bool):
                        self.manifest = value
                    else:
                        print(f"{key}={value} is not a valid argument")
                case "maxsize":
                    if isinstance(value, int):
                        self.maxsize = value
                    else:
                        print(f"{key}={value} is not a valid argument")
                case "premerged":
                    if isinstance(value, bool):
                        self.premerged = value
                    else:
                        print(f"{key}={value} is not a valid argument")
                case "codec":
                    if isinstance(value, str) and value in ['vp9', 'avc1', 'av01', 'vp09']:
                        if value == "vp09":
                            self.manifest = True
                        self.codec = value
                    else:
                        print(f"{key}={value} is not a valid argument")
                case "nodownload":
                    if isinstance(value, bool):
                        self.nodownload = value
                    else:
                        print(f"{key}={value} is not a valid argument")
                case "priority":
                    if isinstance(value, str) and value in ['video', 'audio']:
                        self.priority = value
                    else:
                        print(f"{key}={value} is not a valid argument")
                case "audioonly":
                    if isinstance(value, bool):
                        self.audioonly = value
                    else:
                        print(f"{key}={value} is not a valid argument")
                case "mp3audio":
                    if isinstance(value, bool):
                        if value:
                            self.audioonly = value
                        self.mp3audio = value
                    else:
                        print(f"{key}={value} is not a valid argument")
                case "itag":
                    if isinstance(value, int):
                        self.itag = value
                        if self.itag in [17, 18, 22]:
                            self.premerged = True
                    else:
                        print(f"{key}={value} is not a valid argument")
                case "onlyitag":
                    if isinstance(value, bool):
                        self.onlyitag = value
                    else:
                        print(f"{key}={value} is not a valid argument")
                case "filename":
                    if isinstance(value, str):
                        self.filename = value
                    else:
                        print(f"{key}={value} is not a valid argument")
                case "start":
                    if isinstance(value, str) and len(value) in [5, 8]:
                        self.start = self.returnstringdate(value)
                    else:
                        print(f"{key}={value} is not a valid argument")
                case "end":
                    if isinstance(value, str) and len(value) in [5, 8]:
                        self.end = self.returnstringdate(value)
                    else:
                        print(f"{key}={value} is not a valid argument")
                case "returnurlonly":
                    if isinstance(value, bool):
                        self.returnurlonly = value
                case "proxy":
                    if isinstance(value, str):
                        if value.startswith("https://"):
                            self.proxy = value
                        elif value.startswith("socks"):
                            self.proxy = value
                        else:
                            print(f"{value} is not a valid proxy! Valid https/socks5 proxy example: socks4://127.0.0.1:9050 / https://username:password@69.14.15.16")
                    else:
                        print(f"{key}={value} is not a valid argument")
                case "overwrite":
                    if isinstance(value, bool):
                        self.overwrite = value
                    else:
                        print(f"{key}={value} is not a valid argument")
                case "check_decipher":
                    if isinstance(value, bool):
                        self.check_decipher = value
                    else:
                        print(f"{key}={value} is not a valid argument")
                case "search":
                    if isinstance(value, str):
                        self.query = value
                    else:
                        print(f"{key}={value} is not a valid argument")
                case _:
                    print(f"unknown argument: {key}")
        if not self.logger:
            logging.basicConfig(level=logging.INFO, format="[%(asctime)s] - %(message)s, line %(lineno)d", datefmt='%H:%M:%S')
            self.logger = logging.getLogger(__name__)
        self.proxypreset = None
        if self.proxy:
            self.proxypreset = self.proxy if self.proxy and self.proxy.startswith('https') else None
    def returnstringdate(self, timething: str):
        if len(timething) == 5:
            return datetime.strptime(timething, "%M:%S").strftime("%H:%M:%S")
        elif len(timething) == 8:
            return datetime.strptime(timething, "%H:%M:%S").strftime("%H:%M:%S")
    def _make_connector(self):
        if self.proxy and self.proxy.startswith("socks"):
            return ProxyConnector.from_url(self.proxy)
        return aiohttp.TCPConnector()
    async def download(self, link: str = None):
        async with aiohttp.ClientSession(connector=self._make_connector()) as session:
            if not self.session:
                self.session = session
            if self.query:
                await self.search()
                choices = []
                txt = ""
                for index, key in enumerate(self.videos.keys()):
                    txt += f"[{index}] - {key}\n{self.videos[key]}\n"
                    choices.append(self.videos[key])
                print(txt)
                choice = int(input("pick number to download: "))
                if choice > len(choices):
                    raise ValueError("not a valid choice")
                self.link = choices[choice]
            if link:
                self.link = None
                for ptn in LINKPATTERNLIST:
                    match = re.findall(ptn, link)
                    if match:
                        self.link = match[0]
                        break
                if not self.link:
                    raise ValueError(f"Provided link isn't valid")
            if (link and "playlist?" in link) or (self.link and "playlist?" in self.link):
                if link:
                    self.link = link
                self.playlist = True
                await self.get_playlist()
                self.logger.info(f"grabbed playlist, {len(self.links)} links")
                results = []
                for link in self.links:
                    self.logger.info("fetching video information")
                    self.logger.debug(f"getting {link}")
                    self.link = link
                    await self.get_video_info()
                    if self.nodownload:
                        res = await self._generate_table()
                        results.append(res)
                    await self._pick_formats()
                    res = await self._download_fr()
                    results.append(res)
                    self.logger.info(f"got {self.all_formats['misc']['title']}")
                    await asyncio.sleep(3)
                return results
            else:
                self.logger.info("fetching video information")
                await self.get_video_info()
                if self.nodownload:
                    return await self._generate_table()
                await self._pick_formats()
                return await self._download_fr()
    async def search(self, query: str = None):
        if not self.query:
            self.query = query
        headers = {
            'authority': 'www.youtube.com',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'origin': 'https://www.youtube.com',
            'referer': f'https://www.youtube.com/results?search_query={self.query}',
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
                    'originalUrl': f'https://www.youtube.com/results?search_query={self.query}',
                    'platform': 'DESKTOP',
                    'acceptHeader': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',

                },

                
            },
            'query': self.query,
        }
        if not self.session:
            self.session = aiohttp.ClientSession(connector=self._make_connector())
        async with self.session.post('https://www.youtube.com/youtubei/v1/search', headers=headers, params=params, json=json_data) as r:
            response = await r.text('utf-8')
            responsejson = json.loads(response)
        videos = {}
        for result in responsejson['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']:
            if result.get('videoRenderer'):
                videos[result['videoRenderer']['title']['runs'][0]['text']] = f"https://youtube.com/watch?v={result['videoRenderer']['videoId']}"
            elif result.get('playlistRenderer'):
                videos[result['playlistRenderer']['title']['simpleText']] = f"https://youtube.com/playlist?list={result['playlistRenderer']['playlistId']}"
        self.videos = videos
    async def get_playlist(self, link: str = None):
        if link:
            if not "playlist?" in link:
                raise ValueError("invalid playlist link")
            self.link = link
        playlistid = self.link.split('list=')[1].split('&')[0]
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

        if not self.session:
            self.session = aiohttp.ClientSession(connector= self._make_connector())
        async with self.session.post('https://www.youtube.com/youtubei/v1/next', params=params, headers=headers, json=json_data, proxy=self.proxypreset) as r:
            response = await r.text("utf-8")
            responsejson = json.loads(response)
        if not responsejson.get('contents').get('twoColumnWatchNextResults').get('playlist'):
            raise ValueError("playlist is unavaliable!")
        self.title = responsejson['contents']['twoColumnWatchNextResults']['playlist']['playlist']['title']
        responsejson = responsejson['contents']['twoColumnWatchNextResults']['playlist']['playlist']['contents']
        self.links =  [f'https://youtube.com/watch?v={i["playlistPanelVideoRenderer"]["videoId"]}' for i in responsejson if not i.get('messageRenderer')]
    async def _pick_formats(self):
        if self.start or self.end:
            duration = int(self.all_formats['misc']['lengthSeconds'])
            begin = None
            finish = None
            reference = datetime.strptime("00:00:00", "%H:%M:%S")
            if self.start:
                begin = datetime.strptime(self.start, "%H:%M:%S")
                begin = begin - reference
                begin = begin.total_seconds()
            if self.end:
                finish = datetime.strptime(self.end, "%H:%M:%S")
                finish = finish - reference
                finish = finish.total_seconds()
            if begin and finish:
                customduration = finish-begin
            elif begin:
                customduration = duration-begin
            elif finish:
                customduration = duration-finish
            if customduration < 0:
                raise ValueError(f"{self.start if self.start else 'no start'} and {self.end if self.end else 'no end'} are not valid timestamps! They returned a duration of under 0")
            thepercent = (duration-customduration) / duration
            if self.maxsize:
                self.maxsize = round(self.maxsize * (1 + thepercent))
                self.logger.debug(f'new maxsize {self.maxsize}')
        self.video = {}
        self.audio = {}
        self.manifest_video = {}
        self.manifest_audio = {}
        self.done = False
        if self.maxsize and not self.itag:
            video_ids = []
            audio_ids = []
            if not self.manifest and not self.premerged:
                avaliable = 'unmerged_sig' if self.all_formats.get('unmerged_sig') else 'unmerged_unsig'
                self.logger.debug(f"downloading {avaliable}")
                for key, value in deepcopy(self.all_formats[avaliable]).items():
                    if value.get('contentLength') and int(value.get('contentLength'))/(1024*1024)>self.maxsize:
                        continue
                    if self.codec and self.codec in value.get('mimeType'):
                        video_ids.append(key)
                    elif 'video' in value['mimeType'] and not self.codec and not self.audioonly:
                        video_ids.append(key)
                    elif 'audio' in value['mimeType']:
                        if not self.mp3audio:
                            audio_ids.append(key)
                        elif 'mp4a' in value['mimeType']:
                            audio_ids.append(key)
                
                if self.priority == "video" and not self.audioonly:
                    for video in video_ids:
                        for audio in audio_ids:
                            if (int(self.all_formats[avaliable][video].get('contentLength'))+int(self.all_formats[avaliable][audio].get('contentLength')))/(1024*1024) > self.maxsize:
                                self.logger.debug(f"video {video} and audio {audio} too large")
                                continue
                            self.video = self.all_formats[avaliable][video]
                            audio = self.all_formats[avaliable][audio]
                            if audio['mimeType'].split(";")[0].split('/')[1] in self.video['mimeType']:
                                self.audio = audio
                                break
                        if self.video and self.audio:
                            break
                    if not (self.video and self.audio):
                        self.logger.debug("couldnt find 2 formats with compatible codecs under max size, mixing codecs (audio will be reencoded)")
                        self.video = None
                        self.audio = None
                        for video in video_ids:
                            for audio in audio_ids:
                                if (int(self.all_formats[avaliable][video].get('contentLength'))+int(self.all_formats[avaliable][audio].get('contentLength')))/(1024*1024) > self.maxsize:
                                    self.logger.debug(f"video {video} and audio {audio} too large")
                                    continue
                                self.video = self.all_formats[avaliable][video]
                                self.audio = self.all_formats[avaliable][audio]
                            if self.video and self.audio:
                                break
                        if not (self.video and self.audio):
                            raise self.no_valid_formats(f"No valid formats under the max size {self.maxsize}")
                elif self.priority == "audio" and not self.audioonly:
                    for audio in audio_ids:
                        for video in video_ids:
                            if (int(self.all_formats[avaliable][video].get('contentLength'))+int(self.all_formats[avaliable][audio].get('contentLength')))/(1024*1024) > self.maxsize:
                                self.logger.debug(f"video {video} and audio {audio} too large")
                                continue
                            self.video = self.all_formats[avaliable][video]
                            audio = self.all_formats[avaliable][audio]
                            if audio['mimeType'].split(";")[0].split('/')[1] in self.video['mimeType']:
                                self.audio = audio
                                break
                        if self.video and self.audio:
                            break
                    if not (self.video and self.audio):
                        self.logger.debug("couldnt find 2 formats with compatible codecs under max size, mixing codecs (audio will be reencoded)")
                        self.video = None
                        self.audio = None
                        for audio in audio_ids:
                            for video in video_ids:
                                if (int(self.all_formats[avaliable][video].get('contentLength'))+int(self.all_formats[avaliable][audio].get('contentLength')))/(1024*1024) > self.maxsize:
                                    self.logger.debug(f"video {video} and audio {audio} too large")
                                    continue
                                self.video = self.all_formats[avaliable][video]
                                self.audio = self.all_formats[avaliable][audio]
                            if self.video and self.audio:
                                break
                        if not (self.video and self.audio):
                            raise self.no_valid_formats(f"No valid formats under the max size {self.maxsize}")
                elif not self.priority and not self.audioonly:
                    for (video, audio) in zip(video_ids, audio_ids):
                        if (int(self.all_formats[avaliable][video].get('contentLength'))+int(self.all_formats[avaliable][audio].get('contentLength')))/(1024*1024) > self.maxsize:
                            self.logger.debug(f"video {video} and audio {audio} too large")
                            continue
                        self.video = video
                        audio = self.all_formats[avaliable][audio]
                        if audio['mimeType'].split(";")[0].split('/')[1] in self.video['mimeType']:
                            self.audio = audio
                            break
                    
                    if not (self.video and self.audio):
                        self.logger.debug("couldnt find 2 formats with compatible codecs under max size, mixing codecs (audio will be reencoded)")
                        self.video = None
                        self.audio = None
                        for (video, audio) in zip(video_ids, audio_ids):
                            if (int(self.all_formats[avaliable][video].get('contentLength'))+int(self.all_formats[avaliable][audio].get('contentLength')))/(1024*1024) > self.maxsize:
                                self.logger.debug(f"video {video} and audio {audio} too large")
                                continue
                            self.video = video
                            self.audio = audio
                        if not (self.video and self.audio):
                            raise self.no_valid_formats(f"No valid formats under the max size {self.maxsize}")
                else:
                    for audio in audio_ids:
                        if (int(self.all_formats[avaliable][audio].get('contentLength')))/(1024*1024) > self.maxsize:
                            self.logger.debug(f"{audio} is too big")
                            continue
                        self.audio = self.all_formats[avaliable][audio]
                        break
                    if not self.audio:
                        raise self.no_valid_formats(f"No valid formats under the max size {self.maxsize}")
                if self.video:
                    self.video['url'] = await self._decipher_url(self.video.get('signatureCipher') if self.video.get('signatureCipher') else self.video['url'], unciphered=False if self.video.get('signatureCipher') else True)
                self.audio['url'] = await self._decipher_url(self.audio.get('signatureCipher') if self.audio.get('signatureCipher') else self.audio['url'], unciphered=False if self.audio.get('signatureCipher') else True)
            elif self.premerged and not self.manifest:
                premerged_video = []
                avaliable = 'merged_sig' if self.all_formats.get('merged_sig') else 'merged_unsig'
                for key, value in self.all_formats[avaliable].items():
                    if self.codec and self.codec in value.get('mimeType'):
                        premerged_video.append(key)
                        continue
                    elif not self.codec:
                        premerged_video.append(key)
                for video in premerged_video:
                    if int(self.all_formats[avaliable][video].get('contentLength'))/(1024*1024) > self.maxsize:
                        continue
                    self.video = self.all_formats[avaliable][video]
                    break
                if not self.video:
                    raise self.no_valid_formats(f"No valid formats under the max size {self.maxsize}")
            elif self.manifest:
                manifest_keys = []
                for key, value in self.all_formats['manifest'].items():
                    if self.codec and self.codec in value.get("CODECS"):
                        manifest_keys.append(key)
                    elif not self.codec:
                        manifest_keys.append(key)
                for manifest in manifest_keys:
                    if float(self.all_formats['manifest'][manifest].get('FILESIZE'))>self.maxsize:
                        continue
                    self.manifest_video = self.all_formats['manifest'][manifest]
                    break
                if not self.manifest_video:
                    raise self.no_valid_formats(f"No valid formats under the max size {self.maxsize}")
        elif self.itag:
            if self.itag in [17, 18, 22]:    
                avaliable = 'merged_sig' if self.all_formats.get('merged_sig') else 'merged_unsig'
                for key, value in self.all_formats[avaliable].items():
                    if int(value.get('itag')) == int(self.itag):
                        self.video = value
                        break
                if not self.video:
                    raise self.no_valid_formats(f"Couldn't find a format with that itag")
                self.video['url'] = await self._decipher_url(self.video.get('signatureCipher') if self.video.get('signatureCipher') else self.video.get('url'), unciphered=True if self.video.get('url') else False)
            else:
                await self._extract_manifest(self.all_formats['manifest']['0'])
                for k, v in deepcopy(self.all_formats).items():
                    if k == "manifest":
                        for key, value in v.items():
                            if int(value.get('video_itag')) == int(self.itag):
                                self.manifest = True
                                self.manifest_video = value
                                break
                            if int(value.get('audio_itag')) == int(self.itag):
                                self.manifest = True
                                self.manifest_video = value
                                break
                    else:
                        for key, value in v.items():
                            if not value:
                                continue
                            if int(value.get("itag")) == int(self.itag):
                                if k == "manifest":
                                    self.manifest = True
                                    self.manifest_video = value
                                    break
                                if 'video' in value.get('mimeType'):
                                    self.video = value
                                    self.video['url'] = await self._decipher_url(self.video['signatureCipher'] if self.video.get('signatureCipher') else self.video.get('url'), unciphered=True if self.video.get('url') else False)
                                    break
                                if 'audio' in value.get('mimeType'):
                                    self.audio = value
                                    self.audio['url'] = await self._decipher_url(self.audio['signatureCipher'] if self.audio.get('signatureCipher') else self.audio.get('url'), unciphered=True if self.audio.get('url') else False)
                                    break
                    if (self.video or self.audio or self.manifest_video):
                        break
                if not (self.video or self.audio or self.manifest_video):
                    raise self.no_valid_formats(f"Couldn't find any formats with itag {self.itag}")
                if not self.onlyitag:
                    avaliable = 'unmerged_sig' if self.all_formats.get("unmerged_sig") else "unmerged_unsig"

                    if self.video:
                        for key, value in self.all_formats[avaliable].items():
                            if 'audio' in value['mimeType'] and self.video['mimeType'].split(";")[0].split('/')[1] in value['mimeType']:
                                self.audio = value
                                self.audio['url'] = await self._decipher_url(self.audio['signatureCipher'] if self.audio.get('signatureCipher') else self.audio.get('url'), unciphered=True if self.audio.get('url') else False)
                                break
                    elif self.audio:
                        for key, value in self.all_formats[avaliable].items():
                            if 'video' in value['mimeType'] and self.audio['mimeType'].split(";")[0].split('/')[1] in value['mimeType']:
                                self.video = value
                                self.video['url'] = await self._decipher_url(self.video['signatureCipher'] if self.video.get('signatureCipher') else self.video.get('url'), unciphered=True if self.video.get('url') else False)
                                break
        elif not self.premerged and not self.manifest:
            avaliable = 'unmerged_sig' if self.all_formats.get("unmerged_sig") else "unmerged_unsig"
            video_ids = []
            audio_ids = []
            for key, value in self.all_formats[avaliable].items():
                if self.codec and self.codec in value.get('mimeType'):
                    video_ids.append(key)
                elif 'video' in value.get('mimeType') and not self.codec and not self.audioonly:
                    video_ids.append(key)
                elif 'audio' in value.get('mimeType'):
                    if self.mp3audio:
                        if 'mp4a' in value.get('mimeType'):
                            audio_ids.append(key)
                    else:
                        audio_ids.append(key)
            if not self.audioonly:
                for i in video_ids:
                    for k in audio_ids:
                        if self.all_formats[avaliable][i]['mimeType'].split(";")[0].split('/')[1] in self.all_formats[avaliable][k]['mimeType'].split(";")[0].split('/')[1]:
                            self.video = self.all_formats[avaliable][i]
                            self.video['url'] = await self._decipher_url(self.video['signatureCipher'] if self.video.get('signatureCipher') else self.video.get('url'), unciphered=True if self.video.get('url') else False)
                            self.audio =self.all_formats[avaliable][k]
                            self.audio['url'] = await self._decipher_url(self.audio['signatureCipher'] if self.audio.get('signatureCipher') else self.audio.get('url'), unciphered=True if self.audio.get('url') else False)
                            
                            break
                    if (self.video and self.audio):
                        break
            else:
                self.audio = self.all_formats[avaliable][audio_ids[0]]
                self.audio['url'] = await self._decipher_url(self.audio['signatureCipher'] if self.audio.get('signatureCipher') else self.audio.get('url'), unciphered=True if self.audio.get('url') else False)
        elif self.premerged and not self.manifest:
             avaliable = 'merged_sig' if self.all_formats.get('merged_sig') else 'merged_unsig'
             for key, value in self.all_formats[avaliable].items():
                 self.video = value
                 break
        elif self.manifest:
            for key, value in self.all_formats.get('manifest').items():
                if self.codec and self.codec in value['CODECS']:
                    self.manifest_video = value
                    break
                elif not self.codec:
                    self.manifest_video = value
                    break
    async def _download_fr(self):
        if self.returnurlonly:
            return {'video': self.video.get('url'), 'audio': self.audio.get('url'), 'misc': self.all_formats['misc']}
        count = 1
        if not self.manifest:
            if self.audioonly:
                self.ext = "m4a" if "mp4a" in self.audio['mimeType'] else 'opus' if 'webm' in self.audio['mimeType'] else 'ec-3' if 'ec-3' in self.audio['mimeType'] else 'ac-3'
                filename = f"temp_audio_{int(datetime.now().timestamp())}.{self.ext}"
                logging.debug(f"Downloading audio itag {self.audio.get('itag')}")
                while True:
                    await self._download(self.audio['url'], filename, None if not self.audio.get('contentLength') else int(self.audio['contentLength']))
                    self.result_file = filename
                    if os.path.exists(self.result_file):
                        break
                    else:
                        if count == 4:
                            raise ConnectionError(f"failed to download audio")
                        await asyncio.sleep(count*5)
            elif self.video and not self.audio and not self.video.get('type'):
                ext_vid = "mp4" if "avc1" in self.video['mimeType'] else 'webm'
                filename_vid = f"temp_video_{int(datetime.now().timestamp())}.{ext_vid}"
                logging.debug(f"Downloading video itag {self.video.get('itag')}")
                while True:
                    await self._download(self.video['url'], filename_vid, None if not self.video.get('contentLength') else int(self.audio['contentLength']) if self.audio.get('contentLength') else None)
                    self.result_file = filename
                    self.ext = ext_vid
                    if os.path.exists(self.result_file):
                        break
                    else:
                        if count == 4:
                            raise ConnectionError(f"failed to download audio")
                        await asyncio.sleep(count*5)
            elif not self.video and self.audio:
                self.ext = "m4a" if "mp4a" in self.audio['mimeType'] else 'opus' if 'webm' in self.audio['mimeType'] else 'ec-3' if 'ec-3' in self.audio['mimeType'] else 'ac-3'
                filename = f"temp_audio_{int(datetime.now().timestamp())}.{self.ext}"
                logging.debug(f"Downloading audio itag {self.audio.get('itag')}")
                while True:
                    await self._download(self.audio['url'], filename, None if not self.audio.get('contentLength') else int(self.audio['contentLength']))
                    self.result_file = filename
                    if os.path.exists(self.result_file):
                        break
                    else:
                        if count == 4:
                            raise ConnectionError(f"failed to download audio")
                        await asyncio.sleep(count*5)
            elif self.video and self.audio and not self.video.get('type'):
                logging.debug(f"Downloading video itag {self.video.get('itag')}\nvideo url: {self.video['url']}\nDownloading audio itag {self.audio.get('itag')}\naudio url: {self.audio['url']}")
                await self._unmerged_download_merge()
            elif self.video and self.video.get('type'):
                ext_vid = "mp4" if "avc1" in self.video['mimeType'] else 'webm'
                filename_vid = f"temp_video_{int(datetime.now().timestamp())}.{ext_vid}"
                logging.debug(f"Downloading video itag {self.video.get('itag')}")
                await self._dash_download(filename_vid)
                if self.audio:
                    ext_aud = "m4a" if "mp4a" in self.audio['mimeType'] else 'opus' if 'webm' in self.audio['mimeType'] else 'ec-3' if 'ec-3' in self.audio['mimeType'] else 'ac-3'
                    compatible = True if ext_vid == "mp4" and ext_aud in ['m4a', 'ec-3', 'ac-3'] else True if ext_vid == 'webm' and ext_aud in ['opus'] else False
                    filename_aud = f"temp_audio_{int(datetime.now().timestamp())}.{ext_aud}"
                    logging.debug(f"Downloading audio itag {self.audio.get('itag')}")
                    await self._download(self.audio['url'], filename, None if not self.audio.get('contentLength') else int(self.audio['contentLength']))
                    self.result_file = f"merged_{int(datetime.now().timestamp())}.{ext_vid}"
                    process = await asyncio.subprocess.create_subprocess_exec("ffmpeg", *[x for x in ['-i', filename_vid, '-i', filename_aud, '-c:v', 'copy', "-c:a" if compatible else "", "copy" if compatible else "",'-map', '0:v:0', '-map', '1:a:0','-ab', str(self.audio.get('bitrate')), '-y', self.result_file] if x != ""], stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                    stdout, stderr = await process.communicate()
                    self.logger.debug(f"STDOUT: \n{stdout.decode() if stdout else None}\nSTDERR: \n{stderr.decode() if stderr else None}")
                    os.remove(filename_aud)
                    os.remove(filename_vid)
                else:
                    self.result_file = filename_vid
                self.ext = ext_vid
        else:
            if not self.audioonly:
                self.ext = "mp4" if "avc1" in self.manifest_video['CODECS'] else 'webm'
                logging.debug(f"Downloading video itag {self.manifest_video.get('video_itag')}\nDownloading audio itag {self.manifest_video.get('audio_itag')}")
            else:
                self.ext = 'm4a'
                logging.debug(f"Downloading audio itag {self.manifest_video.get('audio_itag')}")
            self.result_file = f"merged_{int(datetime.now().timestamp())}.{self.ext}"
            await self._manifest_download()
        if self.title and not os.path.exists(self.title):
            os.mkdir("".join([x for x in self.title if x not in '"\\/:*?<>|()']))
        clear = lambda x: "".join([i for i in x if i not in "\\/:*?<>|()"])
        give_file = lambda folder, title, date, ext: f"{clear(folder)}/"+clear(title)+date+f".{ext}" if folder else clear(title)+date+f".{ext}"
        resultfile = give_file(self.title, self.all_formats['misc'].get('title') if not self.filename else self.filename, "", self.ext)
        try:
            os.rename(self.result_file, resultfile)
        except FileExistsError:
            if self.overwrite == True:
                os.remove(resultfile)
                os.rename(self.result_file, resultfile)
            else:
                resultfile = "".join([x for x in give_file(self.title, self.all_formats['misc'].get('title') if not self.filename else self.filename, str(int(datetime.now().timestamp()), self.ext)) if x not in '"\\/:*?<>|()'])
                os.rename(self.result_file, resultfile)
        self.result_file = resultfile
        if self.start or self.end:
            tempfile = f"tempfile_{int(datetime.now().timestamp())}.{self.ext}"
            process = await asyncio.subprocess.create_subprocess_exec("ffmpeg", *["-i", self.result_file, "-ss" if self.start else "", self.start if self.start else "", "-to" if self.end else "", self.end if self.end else "", "-c", "copy", tempfile], stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await process.communicate()
            logging.debug(f"STDOUT: \n{stdout.decode() if stdout else None}\nSTDERR: \n{stderr.decode() if stderr else None}")
            os.remove(self.result_file)
            os.rename(tempfile, self.result_file)
        if self.mp3audio:
            tempfile = f"tempfile_{int(datetime.now().timestamp())}.mp3"
            process = await asyncio.subprocess.create_subprocess_exec("ffmpeg", *["-i", self.result_file,'-ab', str(self.audio.get('bitrate')) if self.audio.get('bitrate') else str(self.manifest_video.get('audio_bitrate')), tempfile], stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await process.communicate()
            logging.debug(f"STDOUT: \n{stdout.decode() if stdout else None}\nSTDERR: \n{stderr.decode() if stderr else None}")
            os.remove(self.result_file)
            os.rename(tempfile, self.result_file)
        process = await asyncio.subprocess.create_subprocess_exec("ffprobe", *['-i', self.result_file, '-show_streams', '-print_format', 'json', '-v', 'quiet', '-show_format'], stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()
        file_info = json.loads(stdout.decode())
        for i in file_info.get('streams'):
            if i['codec_type'] == 'audio':
                codec = i['codec_tag_string']
        result = {
            'filename': self.result_file,
            'width': self.video.get('width') if self.video.get('width') and not self.audioonly else self.manifest_video.get("RESOLUTION").split("x")[0] if self.manifest_video.get("RESOLUTION") and not self.audioonly else None,
            'height': self.video.get('height')if self.video.get('width') and not self.audioonly else self.manifest_video.get("RESOLUTION").split("x")[1] if self.manifest_video.get("RESOLUTION") and not self.audioonly else None,
            'video_mimeType': self.video.get('mimeType') if self.video.get('mimeType') and not self.audioonly else self.manifest_video.get('CODECS').split(',')[0] if self.manifest_video.get('CODECS') and not self.audioonly else None,
            'audio_mimeType': self.audio.get('mimeType') if self.audio.get('mimeType') else self.manifest_video.get('CODECS').split(',')[1] if self.manifest_video.get('CODECS') else None,
            'video_bitrate': self.video.get('bitrate') if self.video.get('bitrate') and not self.audioonly else self.manifest_video.get('BANDWIDTH') if self.manifest_video.get("BANDWIDTH") and not self.audioonly else None,
            'audio_bitrate': self.audio.get('bitrate') if self.audio.get('bitrate') else self.manifest_video.get('audio_bitrate') if self.manifest_video.get('audio_bitrate') else None,
            'filesize': round(os.path.getsize(self.result_file)/(1024*1024), 2),
            'fps': self.video.get('fps') if self.video.get('fps') and not self.audioonly else self.manifest_video.get("FRAME-RATE") if self.manifest_video.get("FRAME-RATE") and not self.audioonly else None,
            'audioQuality': self.audio.get("audioQuality") if self.audio.get("audioQuality") else None,
            'audio_codec': codec,
            'video_itag': self.video.get('itag') if self.video.get('itag') and not self.audioonly else self.manifest_video.get('video_itag') if self.manifest_video.get('video_itag') and not self.audioonly else None,
            'audio_itag': self.audio.get('itag') if self.audio.get('itag') else self.manifest_video.get('audio_itag') if self.manifest_video.get('audio_itag') else None
        }
        self.result = result
        return result
    async def _manifest_download(self):
        video_urls = []
        audio_urls = []
        if not self.audioonly:
            async with self.session.get(URL(self.manifest_video['URL'], encoded=True), proxy=self.proxypreset) as r:
                logging.debug(f"request info: {json.dumps(self.request_to_dict(r.request_info))}")
                rtext = await r.text('utf-8')
                rtext = rtext.split("\n")
                for url in rtext:
                    if url.startswith('https'):
                        video_urls.append(url)
                    elif url.startswith('#EXT-X-MAP:URI="'):
                        video_urls.append(url.split('#EXT-X-MAP:URI="')[1].replace('"', ''))
        temp_file_v = None
        temp_file_a = None
        async with self.session.get(URL(self.manifest_video['AUDIOLINK'], encoded=True), proxy=self.proxypreset) as r:
            logging.debug(f"request info: {json.dumps(self.request_to_dict(r.request_info))}")
            rtext = await r.text('utf-8')
            rtext = rtext.split("\n")
            for url in rtext:
                if url.startswith('https'):
                    audio_urls.append(url)
                elif url.startswith('#EXT-X-MAP:URI="'):
                    audio_urls.append(url.split('#EXT-X-MAP:URI="')[1].replace('"', ''))
        if not self.audioonly:
            temp_file_v = f"temp_video_{int(datetime.now().timestamp())}.ts"
            temp_file_a = f"temp_audio_{int(datetime.now().timestamp())}.ts"
            self.progress = tqdm(total=float(self.manifest_video['FILESIZE'])*1024*1024, unit='iB' ,unit_scale=True)
            await self._manifest_worker(video_urls, temp_file_v)
            logging.debug("finished downloading video manifest")
            await self._manifest_worker(audio_urls, temp_file_a)
            logging.debug("finished download audio manifest")
            self.progress.close()
            compatible = True if 'mp4a' and 'avc1' in self.manifest_video['CODECS'] else False
            audio_bitrate = await asyncio.subprocess.create_subprocess_exec("ffprobe", *['-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', '-i', temp_file_a], stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await audio_bitrate.communicate()
            audio_bitrate = json.loads(stdout.decode()).get('streams')[0].get('bit_rate')
            self.manifest_video['audio_bitrate'] = audio_bitrate
            args = [x for x in ["-i" ,temp_file_v, "-i" ,temp_file_a ,"-c:v" ,"copy" ,"-c:a" if compatible else "", "copy" if compatible else "", "-ab" ,str(audio_bitrate), "-map", "0:v:0", "-map", "1:a:0" ,"-y" ,self.result_file] if x != ""]
            logging.debug(f"ffmpeg {' '.join(args)}")
            process = await asyncio.subprocess.create_subprocess_exec("ffmpeg", *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await process.communicate()
            self.logger.debug(f"STDOUT: \n{stdout.decode() if stdout else None}\nSTDERR: \n{stderr.decode() if stderr else None}")
        else:
            temp_file_a = f"temp_audio_{int(datetime.now().timestamp())}.{self.ext}"
            self.progress = tqdm(total=float(self.manifest_video['FILESIZE'])*1024*1024, unit='iB' ,unit_scale=True)
            await self._manifest_worker(audio_urls, temp_file_a)
            self.progress.close()
            self.result_file = temp_file_a
            audio_bitrate = await asyncio.subprocess.create_subprocess_exec("ffprobe", *['-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', '-i', temp_file_a], stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await audio_bitrate.communicate()
            audio_bitrate = json.loads(stdout.decode()).get('streams')[0].get('bit_rate')
            self.manifest_video['audio_bitrate'] = audio_bitrate
        [os.remove(x) if x else None for x in [temp_file_a, temp_file_v]]
    async def _manifest_worker(self, links: list[str], filename: str):
        async with aiofiles.open(filename, 'wb') as f1:
            headers = {
                'range': 'bytes=0-'
            }
            for link in links:
                async with self.session.get(URL(link, encoded=True), proxy=self.proxypreset, headers=headers) as r:
                    logging.debug(f"request info: {json.dumps(self.request_to_dict(r.request_info))}")
                    if r.status not in [200, 206]:
                        logging.info(f"bad status on manifest download: {r.status}")
                    while True:
                        chunk = await r.content.read(1024)
                        if not chunk:
                            break
                        await f1.write(chunk)
                        self.progress.update(len(chunk))
    async def _dash_download(self, filename: str):
        segment_count_pattern = r'Segment-Count: (.*?)\n'
        async with self.session.get(self.video['url'] + "&sq=0", proxy=self.proxypreset) as r:
            logging.debug(f"request info: {json.dumps(self.request_to_dict(r.request_info))}")
            rtext = await r.text("unicode_escape")
        segments = int(re.findall(segment_count_pattern, rtext)[0].rstrip())
        self.logger.debug(f"{segments} segments in dash video")
        progress = tqdm(total=int(self.video['contentLength']), unit='iB', unit_scale=True)
        headers = {
            'range': 'bytes=0-'
        }
        async with aiofiles.open(filename, 'wb') as f1:
            for i in range(segments):
                async with self.session.get(self.video['url'] + f"&sq={i}", proxy=self.proxypreset, headers=headers) as r:
                    logging.debug(f"request info: {json.dumps(self.request_to_dict(r.request_info))}")
                    while True:
                        chunk = await r.content.read(1024)
                        if not chunk:
                            break
                        await f1.write(chunk)
                        progress.update(len(chunk))
        progress.close()
        
    async def _unmerged_download_merge(self):
        ext_vid = "mp4" if "avc1" in self.video['mimeType'] else 'webm'
        filename_vid = f"temp_video_{int(datetime.now().timestamp())}.{ext_vid}"
        ext_aud = "m4a" if "mp4a" in self.audio['mimeType'] else 'opus' if 'webm' in self.audio['mimeType'] else 'ec-3' if 'ec-3' in self.audio['mimeType'] else 'ac-3'
        filename_aud = f"temp_audio_{int(datetime.now().timestamp())}.{ext_aud}"
        compatible = True if ext_vid == "mp4" and ext_aud in ['m4a', 'ec-3', 'ac-3'] else True if ext_vid == 'webm' and ext_aud in ['opus'] else False
        count = 1
        while True:
            await self._download(self.video['url'], filename_vid, None if not self.video.get('contentLength') else int(self.video['contentLength']))
            await self._download(self.audio['url'], filename_aud, None if not self.audio.get('contentLength') else int(self.audio['contentLength']))
            self.result_file = f"merged_{int(datetime.now().timestamp())}.{ext_vid}"
            args = [x for x in ['-i', filename_vid, '-i', filename_aud, '-c:v', 'copy', "-c:a" if compatible else "","copy" if compatible else "", '-map', '0:v:0', '-map', '1:a:0','-ab', str(self.audio.get('bitrate')), '-y', self.result_file] if x != ""]
            process = await asyncio.subprocess.create_subprocess_exec("ffmpeg", *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await process.communicate()
            self.logger.debug(f"STDOUT: \n{stdout.decode() if stdout else None}\nSTDERR: \n{stderr.decode() if stderr else None}")
            if not os.path.exists(self.result_file):
                self.session.cookie_jar.clear()
                if count == 4:
                    raise ConnectionError(f"tried 3 times, couldnt download both video and audio\nvideo url {self.video['url']}\naudio url {self.audio['url']}")
                self.logger.debug(f"trying again, errored, waiting {5*count} seconds")
                await asyncio.sleep(5*count)
                count += 1
                continue
            break
        os.remove(filename_vid)
        os.remove(filename_aud)
        self.ext = ext_vid
    async def _download(self, url: str, filename: str, content_length: int):
        if not self.session:
            self.session = aiohttp.ClientSession(connector=self._make_connector())
        async with aiofiles.open(filename, 'wb') as f1:
            if not content_length:
                async with self.session.head(url, proxy=self.proxypreset) as headresponse:
                    logging.debug(f"request info: {json.dumps(self.request_to_dict(headresponse.request_info))}")
                    content_length = int(headresponse.headers.get('content-length'))
                    self.video['content-length'] = content_length
                    await asyncio.sleep(5)
            if content_length > (10*1024*1024):
                await self._chunk_download(url, f1, content_length)
            else:
                progress = tqdm(total=content_length, unit='iB', unit_scale=True)
                headers = {
                    'range': 'bytes=0-'
                }
                async with self.session.get(url, proxy=self.proxypreset, headers=headers) as r:
                    logging.debug(f"request info: {json.dumps(self.request_to_dict(r.request_info))}")
                    if r.status == 302:
                        self.logger.debug(f"ratelimited, waiting 5 seconds...")
                        return
                    if r.status not in [200, 206]:
                        self.logger.info("bad download, status %s" % str(r.status))
                        return
                    while True:
                        chunk = await r.content.read(1024)
                        if not chunk:
                            break
                        await f1.write(chunk)
                        progress.update(len(chunk))


                progress.close()
    async def _chunk_download(self, url: str, fp: aiofiles.threadpool.text.AsyncTextIOWrapper, content_length: int):
        headers = {
            "range": "bytes=0-"
        }
        chunk_size = 10 * 1024 * 1024
        chunks, _ = divmod(content_length, 10*1024*1024)
        progress = tqdm(total=content_length, unit='iB', unit_scale=True)
        for i in range(chunks+1):
            start = i*chunk_size
            end = start + chunk_size - 1
            if i == chunks:
                headers['range'] = f"bytes={start}-"

                self.logger.debug(f"Sending range request: {headers['range']}")
                async with self.session.get(url, headers=headers, proxy=self.proxypreset) as r:
                    logging.debug(f"request info: {json.dumps(self.request_to_dict(r.request_info))}")
                    if r.status == 302:
                        self.logger.debug(f"ratelimited, waiting 5 seconds...")
                        return
                    if r.status not in [200, 206]:
                        self.logger.info("bad download, status %s" % str(r.status))
                        return

                    while True:
                        chunk = await r.content.read(1024)
                        if not chunk:
                            break
                        await fp.write(chunk)
                        progress.update(len(chunk))

            else:
                headers['range'] = f"bytes={start}-{end}"
                self.logger.debug(f"Sending range request: {headers['range']}")
                async with self.session.get(url, headers=headers, proxy=self.proxypreset) as r:
                    if r.status == 302:
                        self.logger.debug(f"ratelimited, waiting 5 seconds...")
                        await asyncio.sleep(5)
                        r = await self.session.get(url, proxy=self.proxypreset, headers=headers)
                    if r.status not in [200, 206]:
                        self.logger.info("bad download, status %s" % str(r.status))
                    logging.debug(f"request info: {json.dumps(self.request_to_dict(r.request_info))}")
                    while True:
                        chunk = await r.content.read(1024)
                        if not chunk:
                            break
                        await fp.write(chunk)
                        progress.update(len(chunk))
        progress.close()

    class no_valid_formats(Exception):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)

    class decipher_fail(Exception):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)
    async def _generate_table(self):
        table = prettytable.PrettyTable()
        table.field_names = ['itag', 'formattype', 'codec', 'size','resol', 'bitrate','fps', 'type', 'audioQuality', 'prot']
        temp_all = deepcopy(self.all_formats)
        for key, value in temp_all['merged_sig'].items():
            if value.get('contentLength') and isinstance(value.get('contentLength'), str):
                continue
            newurl = await self._decipher_url(value.get('signatureCipher'))
            async with self.session.head(newurl, proxy=self.proxypreset) as r:
                logging.debug(f"request info: {json.dumps(self.request_to_dict(r.request_info))}")
                self.all_formats['merged_sig'][key]['url'] = newurl
                self.all_formats['merged_sig'][key]['contentLength'] = r.headers.get('content-length')
        for key, value in temp_all['merged_unsig'].items():
            if value.get('contentLength') and isinstance(value.get('contentLength'), str):
                continue
            async with self.session.head(value.get('url'), proxy=self.proxypreset) as r:
                logging.debug(f"request info: {json.dumps(self.request_to_dict(r.request_info))}")
                self.all_formats['merged_unsig'][key]['contentLength'] = r.headers.get('content-length')
        if self.all_formats['manifest'].get('0'):
            self.logger.debug('extracting manifest info')
            await self._extract_manifest(self.all_formats['manifest'].get('0'))
        allitags = []
        all_entries = []
        for i in list(self.all_formats['unmerged_sig'].values()) + list(self.all_formats['unmerged_unsig'].values()) + list(self.all_formats['merged_sig'].values()) + list(self.all_formats['merged_unsig'].values()) + list(self.all_formats['manifest'].values()):
            itag = int(i.get('itag') if i.get('itag') else i.get('URL').split('itag/')[1].split('/')[0])
            if itag not in allitags:
                all_entries.append(i)
                allitags.append(itag)
        async with aiofiles.open(f"videoinfo/video-{self.video_id}.json", "w") as f1:
            self.all_formats['misc'] = self.other_video_info
            await f1.write(json.dumps(self.all_formats, indent=4))
        sorted_entries = sorted(all_entries, key=lambda x: round(int(x.get('contentLength'))/(1024*1024), 2) if x.get('contentLength') else float(x.get('FILESIZE')), reverse=False)
        for entrydata in sorted_entries:
            itag = entrydata.get('itag') if entrydata.get('itag') else entrydata.get('URL').split('itag/')[1].split('/')[0]
            formattype = entrydata.get('mimeType', 'video/mp4').split(';')[0]
            codec = entrydata.get('mimeType').split('codecs=')[1].replace('"', '') if entrydata.get('mimeType') else entrydata.get('CODECS')
            try:
                filesize = f"{round(int(entrydata.get('contentLength'))/(1024*1024), 2)}mb" if entrydata.get('contentLength') and not entrydata.get('type') else f'~{round(int(entrydata.get("contentLength"))/(1024*1024), 2)}mb' if entrydata.get('contentLength') and entrydata.get('type') else '~'+ str(entrydata.get('FILESIZE')) + 'mb'
            except Exception as e:
                self.logger.info(e)
                self.logger.info(entrydata)
            resolution = "x".join([str(entrydata.get('width')), str(entrydata.get('height'))]) if entrydata.get('width') else entrydata.get('RESOLUTION')
            bitrate = entrydata.get('bitrate') if entrydata.get('bitrate') else entrydata.get('BANDWIDTH')
            fps = entrydata.get('fps') if entrydata.get('fps') else entrydata.get('FRAME-RATE')
            vidaud = 'both' if entrydata.get('CODECS') else 'audio' if 'audio' in entrydata.get('mimeType') else 'both' if entrydata.get('itag') in ['22', '18', '17', 22, 18, 17] else  'video' if 'video' in entrydata.get('mimeType') else 'None'
            newlist = [itag, formattype, codec, filesize, resolution, bitrate, fps, vidaud]
            for i in table.field_names[8:-1]:
                newlist.append(entrydata.get(i, 'not available'))
            if entrydata.get('BANDWIDTH'):
                newlist.append('m3u8')
            elif entrydata.get('type'):
                newlist.append('DASH')
            else:
                newlist.append('https')
            table.add_row(newlist)
        return table
                
    async def get_video_info(self, link: str = None):
        if link:
            self.link = None
            for ptn in LINKPATTERNLIST:
                match = re.findall(ptn, link)
                if match:
                    self.link = match[0]
                    break
            if not self.link:
                raise ValueError(f"Provided link isn't valid")
        if not self.session:
            async with aiohttp.ClientSession(connector=self._make_connector()) as session:
                self.session = session
                await self._get_video_info()
        else:
            await self._get_video_info()
    def request_to_dict(self, request: aiohttp.RequestInfo):
        headers = {}
        for key, value in request.headers.items():
            headers[key] = deepcopy(value)
        return {'url': str(request.url), 'headers': headers, 'method': request.method}
    async def _get_video_info(self):
        cookies = {
        "PREF": "f4=4000000&f6=40000000&tz=Europe.Warsaw&f5=30000&f7=100",
        "CONSENT": "PENDING+915"
        }
        self.video_id = None
        VIDEOIDPATTERN_DEFAULT = r'(?:https?://)?(?:www\.)?(?:m\.)?youtube\.com/watch\?v=([\w-]+)'
        VIDEOIDPATTERN_MOBILE = r'(?:https?://)?(?:www\.)?(?:m\.)?youtu\.be\/([\w-]+)'
        VIDEOIDPATTERN_SHORTS = r'(?:https?://)?(?:www\.)?(?:m\.)?youtube\.com/shorts/([\w-]+)(?:\?feature=[\w]+)?'
        VIDEOIDPATTERN_LIST = [VIDEOIDPATTERN_MOBILE, VIDEOIDPATTERN_DEFAULT, VIDEOIDPATTERN_SHORTS]
        for ptn in VIDEOIDPATTERN_LIST:
            match = re.findall(ptn, self.link)
            if match:
                self.video_id = match[0]
                break
        if not self.video_id:
            raise ValueError(f"Couldn't find video id in link {self.link}")
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
        async with self.session.get(f"https://youtube.com/watch?v={self.video_id}", headers=headers, cookies=cookies, proxy=self.proxypreset) as response:
            logging.debug(f"request info: {json.dumps(self.request_to_dict(response.request_info))}")
            response = await response.text("utf-8")

        self.logger.debug(f"SENT GET REQUEST TO https://youtube.com/watch?v={self.video_id}")

        initialplayerresponsepattern = r'var ytInitialPlayerResponse = (.*?\"nanos\":(?:\d+)}}}})'
        matches = re.findall(initialplayerresponsepattern, response, re.DOTALL)
        if not matches:
            raise ConnectionError(f"couldn't get the initial response from default youtube site")
        responsejson: dict = json.loads(matches[0])
        basejspattern = r"href=\"(/s/player/(?:.*?)/player_ias\.vflset/(?:.*?)/base\.js)\""
        matches = re.findall(basejspattern, response)
        if not matches:
            raise FileNotFoundError(f"Couldn't find base.js in page source, maybe fault on my end?")
        self.basejslink = f"https://youtube.com{re.findall(basejspattern, response)[0]}"
        self.logger.debug(f"base.js link: {self.basejslink}")

        self.video_unmerged_info = {}
        self.video_merged_info = {}
        self.other_video_info = {}
        self.all_formats = {
            "manifest": {},
            "unmerged_unsig": {},
            "merged_unsig": {},
            "unmerged_sig": {},
            "merged_sig": {}
        }
        self.needlogin = False
        if responsejson['playabilityStatus'].get('status') == 'LOGIN_REQUIRED':
            self.needlogin = True
            try:
                import env
                logging.info("LOGIN REQUIRED, will try use credentials")

                logheaders = {
                    'authority': 'www.youtube.com',
                    'accept': '*/*',
                    'accept-language': 'en-US,en;q=0.7',
                    'authorization': env.authorization,
                    'content-type': 'application/json',
                    'Cookie': f"SID={env.SID};HSID={env.HSID};SSID={env.SSID};APISID={env.APISID};SAPISID={env.SAPISID};",
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
                    'videoId': self.video_id,
                    'playbackContext': {
                        'contentPlaybackContext': {
                            'html5Preference': 'HTML5_PREF_WANTS',
                        },
                    },
                    'racyCheckOk': True,
                    'contentCheckOk': True,
                }
                async with self.session.post(
                    'https://www.youtube.com/youtubei/v1/player',
                    params=logparams,
                    headers=logheaders,
                    json=logjson_data, proxy=self.proxypreset
                ) as r:
                    logging.debug(f"request info: {json.dumps(self.request_to_dict(r.request_info))}")
                    response = await r.text("utf-8")
                    responsejson = json.loads(response)
                avaliable_itags = list(map(lambda x: int(x[1].get('itag')), self.video_unmerged_info.items()))
                for index, i in enumerate(responsejson['streamingData']['adaptiveFormats']):
                    if int(i['itag']) in avaliable_itags:
                        continue
                    self.video_unmerged_info[str(index)] = i
                    avaliable_itags.append(int(i['itag']))
                avaliable_itags = list(map(lambda x: int(x[1].get('itag')), self.video_merged_info.items()))
                for index, i in enumerate(responsejson['streamingData']['formats']):
                    if int(i['itag']) in avaliable_itags:
                        continue
                    self.video_merged_info[str(index)] = i
                    avaliable_itags.append(int(i['itag']))
            except:
                self.logger.info("LOGIN REQUIRED. Will try to use TVHTML5_SIMPLY_EMBEDDED_PLAYER to grab info")
                json_data = {
                    "context": {
                        "client": {
                            "clientName": "TVHTML5_SIMPLY_EMBEDDED_PLAYER",
                            "clientVersion": "2.0",
                            "hl": "en",
                            "timeZone": "UTC",
                            "utcOffsetMinutes": 0
                        },
                        "thirdParty": {
                            "embedUrl": "https://www.youtube.com/"
                        }
                    },
                    "videoId": self.video_id,
                    "playbackContext": {
                        "contentPlaybackContext": {
                            "html5Preference": "HTML5_PREF_WANTS",
                            "signatureTimestamp": 19828
                        }
                    },
                    "contentCheckOk": True,
                    "racyCheckOk": True
                }
                async with self.session.post("https://www.youtube.com/youtubei/v1/player?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8", headers=headers, json=json_data, proxy=self.proxypreset) as response:
                    logging.debug(f"request info: {json.dumps(self.request_to_dict(response.request_info))}")
                    response = await response.text("utf-8")
                    responsejson = json.loads(response)
                    avaliable_itags = list(map(lambda x: int(x[1].get('itag')), self.video_unmerged_info.items()))
                    for index, i in enumerate(responsejson['streamingData']['adaptiveFormats']):
                        if int(i['itag']) in avaliable_itags:
                            continue
                        self.video_unmerged_info[str(index)] = i
                        avaliable_itags.append(int(i['itag']))
                    avaliable_itags = list(map(lambda x: int(x[1].get('itag')), self.video_merged_info.items()))
                    for index, i in enumerate(responsejson['streamingData']['formats']):
                        if int(i['itag']) in avaliable_itags:
                            continue
                        self.video_merged_info[str(index)] = i
                        avaliable_itags.append(int(i['itag']))
        avaliable_itags = list(map(lambda x: int(x[1].get('itag')), self.video_unmerged_info.items()))
        for index, i in enumerate(responsejson['streamingData']['adaptiveFormats']):
            if int(i['itag']) in avaliable_itags:
                continue
            self.video_unmerged_info[str(index)] = i
            avaliable_itags.append(int(i['itag']))
        avaliable_itags = list(map(lambda x: int(x[1].get('itag')), self.video_merged_info.items()))
        for index, i in enumerate(responsejson['streamingData']['formats']):
            if int(i['itag']) in avaliable_itags:
                continue
            self.video_merged_info[str(index)] = i
            avaliable_itags.append(int(i['itag']))
        for key, value in responsejson["videoDetails"].items():
            self.other_video_info[key] = value
        
        if not os.path.exists("videoinfo"):
            os.mkdir("videoinfo")
        self.got_functions = False
        self.expire = None

        self.all_formats['misc'] = self.other_video_info
        if self.video_unmerged_info.get("0"):
            if self.video_unmerged_info["0"].get("signatureCipher"):
                self.logger.debug("found unmerged signatured formats from web response")
                self.all_formats['unmerged_sig'] = self.video_unmerged_info
                self.sortdictbysize("unmerged_unsig")
            elif self.video_unmerged_info["0"].get("url"):
                self.logger.debug("found unmerged unsignatured formats from web response")
                self.all_formats['unmerged_unsig'] = self.video_unmerged_info
                self.sortdictbysize("unmerged_unsig")
        if self.video_merged_info.get("0"):
            if self.video_merged_info["0"].get("signatureCipher"):
                self.logger.debug("found merged signatured formats from web response")
                if self.premerged:
                    for key, value in deepcopy(self.video_merged_info).items():
                        if value.get('content-length'):
                            continue
                        newurl = await self._decipher_url(value.get('signatureCipher'))
                        async with self.session.head(newurl, proxy=self.proxypreset) as r:
                            logging.debug(f"request info: {json.dumps(self.request_to_dict(r.request_info))}")
                            self.video_merged_info[key]['contentLength'] = r.headers.get('content-length')
                            self.video_merged_info[key]['url'] = newurl

                self.all_formats['merged_sig'] = self.video_merged_info
                self.sortdictbysize("merged_unsig")
            elif self.video_merged_info["0"].get("url"):
                self.logger.debug("found merged unsignatured formats from web response")
                for key, value in deepcopy(self.video_merged_info).items():
                    if value.get('content-length'):
                        continue
                    if not self.expire:
                        self.expire = datetime.fromtimestamp(int(re.findall(r"expire=(\d+)", value.get('url'))[0]))
                    async with self.session.head(value.get('url'), proxy=self.proxypreset) as r:
                        logging.debug(f"request info: {json.dumps(self.request_to_dict(r.request_info))}")
                        self.video_merged_info[key]['contentLength'] = r.headers.get('content-length')
                self.all_formats['merged_unsig'] = self.video_merged_info
                self.sortdictbysize("merged_unsig")

        self.logger.debug(f"Starting API requests")
        headers = {
        'authority': 'www.youtube.com',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.7',
        'content-type': 'application/json',
        'origin': 'https://www.youtube.com',
        'referer': self.link, 
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
        clients: dict ={'IOS': {'clientVersion': '17.33.2', 
                                'userAgent': 'com.google.ios.youtube/17.33.2 (iPhone14,3; U; CPU iOS 15_6 like Mac OS X)',
                                'apikey': 'AIzaSyB-63vPrdThhKuerbB2N_l7Kwwcxj6yUA',
                                'deviceModel': 'iPhone14,3'},
                        'XBOXONEGUIDE': {'clientVersion': '1.0',
                                        'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; Xbox; Xbox One) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.10553',
                                        'apikey': 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'}}

        api_responses = {}
        for key, value in clients.items():
            self.logger.debug(f'downloading {key} api')
            json_data = {
                'videoId': self.video_id,
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
            'key': value.get('apikey') if not self.needlogin else env.apikey,
            'prettyPrint': 'false',
            }
            async with self.session.post(
            'https://www.youtube.com/youtubei/v1/player/',
            params=params,
            json=json_data, 
            cookies=cookies,
            headers=headers if not self.needlogin else logheaders,
            proxy=self.proxypreset
            ) as apiresponse:
                logging.debug(f"request info: {json.dumps(self.request_to_dict(apiresponse.request_info))}")
                apiresponse = await apiresponse.text("utf-8")
                apiresponse = json.loads(apiresponse)
                api_responses[key] = apiresponse

        for count, (key, value) in enumerate(api_responses.items()):
            alreadyin = False
            if not value.get('streamingData'):
                self.logger.debug(f"Nothing avaliable from {key}")
                continue
            if value.get('streamingData').get('hlsManifestUrl') and self.manifest:
                await self._extract_manifest(value.get('streamingData').get('hlsManifestUrl'))
            elif value.get('streamingData').get('hlsManifestUrl'):
                self.all_formats['manifest']['0'] = value.get('streamingData').get('hlsManifestUrl')
            if value.get('captions') and not self.all_formats.get('captions'):
                for i in value.get('captions')['playerCaptionsTracklistRenderer']['captionTracks']:
                    if i.get('baseUrl'):
                        self.all_formats['captions'] = i['baseUrl']
                        
            if value['streamingData'].get('formats'):
                if value['streamingData']['formats'][0].get('url'):
                    self.logger.debug(f"found merged unsig from {key}")
                    for i in range(len(value.get('streamingData').get('formats'))):
                        avaliable_itags = list(map(lambda x: int(x[1].get('itag')), self.all_formats['merged_unsig'].items()))
                        if int(value.get('streamingData').get('formats')[i].get('itag')) in avaliable_itags:
                            continue
                        if self.premerged:
                            self.logger.debug("adding content lengths to merged formats")
                            async with self.session.head(value.get('streamingData').get('formats')[i].get('url'), proxy=self.proxypreset) as mergedresponse:
                                logging.debug(f"request info: {json.dumps(self.request_to_dict(mergedresponse.request_info))}")
                                content_length = mergedresponse.headers.get("content-length")
                                if content_length:
                                    value.get('streamingData').get('formats')[i]['contentLength'] = int(content_length)
                        self.all_formats['merged_unsig'][str(i)] = value.get('streamingData').get('formats')[i]
                    self.sortdictbysize('merged_unsig')
                elif value['streamingData']['formats'][0].get('signatureCipher'):
                    self.logger.debug(f"found merged sig from {key}")
                    for i in range(len(value.get('streamingData').get('formats'))):
                        avaliable_itags = list(map(lambda x: int(x[1].get('itag')), self.all_formats['merged_sig'].items()))
                        if int(value.get('streamingData').get('formats')[i].get('itag')) in avaliable_itags:
                            continue
                        if self.premerged:
                            self.logger.debug("adding content lengths to merged formats")
                            url = await self._decipher_url(value.get('streamingData').get('formats')[i].get('signatureCipher'))
                            value.get('streamingData').get('formats')[i]['url'] = url
                            async with self.session.head(url, proxy=self.proxypreset) as mergedresponse:
                                logging.debug(f"request info: {json.dumps(self.request_to_dict(mergedresponse.request_info))}")
                                content_length = mergedresponse.headers.get("content-length")
                                if content_length:
                                    value.get('streamingData').get('formats')[i]['contentLength'] = int(content_length)
                        self.all_formats['merged_sig'][str(i)] = value.get('streamingData').get('formats')[i]
                    self.sortdictbysize('merged_sig')
            if value['streamingData'].get('adaptiveFormats'):
                if value['streamingData']['adaptiveFormats'][0].get('url'):
                    self.logger.debug(f"found unmerged unsig in {key}")
                    for i in range(len(value['streamingData']['adaptiveFormats'])):
                        avaliable_itags = list(map(lambda x: int(x[1].get('itag')), self.all_formats['unmerged_unsig'].items()))
                        if int(value['streamingData']['adaptiveFormats'][i].get('itag')) in avaliable_itags:
                            self.logger.debug(f"{value['streamingData']['adaptiveFormats'][i].get('itag')} already in")
                            continue
                        self.all_formats['unmerged_unsig'][str(i)] = value['streamingData']['adaptiveFormats'][i]
                    self.sortdictbysize('unmerged_unsig')
                elif value['streamingData']['adaptiveFormats'][0].get('signatureCipher'):
                    self.logger.debug(f"found unmerged sig in {key}")
                    for i in range(len(value['streamingData']['adaptiveFormats'])):
                        avaliable_itags = list(map(lambda x: int(x[1].get('itag')), self.all_formats['unmerged_sig'].items()))
                        if int(value['streamingData']['adaptiveFormats'][i].get('itag')) in avaliable_itags:
                            self.logger.debug(f"{value['streamingData']['adaptiveFormats'][i].get('itag')} already in")
                            continue
                        self.all_formats['unmerged_sig'][str(i)] = value['streamingData']['adaptiveFormats'][i]
                    self.sortdictbysize('unmerged_sig')
        for key, value in self.all_formats.items():
            if isinstance(value, dict) and len(value.keys()) > 0:
                self.logger.debug(f"{key} is avaliable")
            else:
                self.logger.debug(f"{key} is not avaliable")
        if not self.expire:
            for ftype, baloney in self.all_formats.items():
                for key, value in baloney.items():
                    if isinstance(value, str):
                        continue
                    if value.get('url'):
                        self.expire = datetime.fromtimestamp(int(re.findall(r"expire=(\d+)", value.get('url'))[0]))
                        break
                if self.expire:
                    break
        self.all_formats['expire'] = self.expire.isoformat() if self.expire else None
        if not os.path.exists("videoinfo"):
            os.mkdir('videoinfo')
        self.logger.debug("writing video information into " + f"videoinfo/video-{self.video_id}.json")
        async with aiofiles.open(f"videoinfo/video-{self.video_id}.json", "w") as f1:
            temp =deepcopy(self.all_formats)
            temp['misc'] = self.other_video_info
            await f1.write(json.dumps(temp, indent=4))
        self.logger.info("successfully fetched video information")
    async def _decipher_url(self, ciphered_url: str, unciphered: bool = False):

        await self._get_decipher_functions()
        if not unciphered:
            secondfunction = self.functions.get('secondfunction')
            wholefunctionsig = self.functions.get('wholefunctionsig')
            functionname = self.functions.get('functioname')
            thirdfunction = self.functions.get('thirdfunction')
            thirdfunctionname = self.functions.get('thirdfunctionname')
            ciphered_url = unquote(ciphered_url)
            signature = ciphered_url.split('https')[0].replace('s=', '').replace('&sp=sig&url=', '')
            url = unquote('https' + ciphered_url.split('https')[1])
            decipher_js_script = f"\n\n{secondfunction}\n\n{wholefunctionsig}\nconsole.log({functionname}('{signature}'))"
            if not os.path.exists('videoinfo'):
                os.mkdir('videoinfo')
            async with aiofiles.open("videoinfo/deciphersignature.js", "w") as f1:
                await f1.write(decipher_js_script)
            check_node = await asyncio.create_subprocess_exec("node", "-v", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await check_node.communicate()
            if check_node.returncode != 0:
                raise self.missing_node(f"Node.js is missing, install it!\n{stderr.decode()}")
            result = await asyncio.create_subprocess_exec('node',  'videoinfo/deciphersignature.js', stdout=asyncio.subprocess.PIPE)
            stdout, _ = await result.communicate()
            deciphered = stdout.decode('utf-8')
            newurl = url + '&sig=' + deciphered
            headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.7',
            'cache-control': 'max-age=0',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            }
            if self.check_decipher:
                self.logger.debug("checking if deciphering worked")
                async with self.session.head(newurl, headers=headers, proxy=self.proxypreset) as r:
                    logging.debug(f"request info: {json.dumps(self.request_to_dict(r.request_info))}")
                    if r.status == 302:
                        self.logger.debug("rate limted, waiting 5 seconds")
                        await asyncio.sleep(5)
                        async with self.session.head(newurl, headers=headers, proxy=self.proxypreset) as r:
                            logging.debug(f"request info: {json.dumps(self.request_to_dict(r.request_info))}")
                    if r.status not in [200, 206]:
                        self.logger.debug(f"url not successfully deciphered, \n  {newurl}\ncode {r.status}")
        if  unciphered or ("&n=" in newurl):
            if unciphered:
                newurl = unquote(ciphered_url)
            nparam = newurl.split("&n=")[1] if len(newurl.split("&n=")) > 1 else None
            if not nparam:
                return ciphered_url
            nparam = nparam.split("&")[0]
            thirdfunction = self.functions.get('thirdfunction')
            thirdfunctionname = self.functions.get('thirdfunctionname')
            decipher_js_script = f'{thirdfunction}\nconsole.log({thirdfunctionname}("{nparam}"))'
            async with aiofiles.open("videoinfo/deciphersignature.js", "w") as f1:
                await f1.write(decipher_js_script)
            result = await asyncio.create_subprocess_exec('node',  'videoinfo/deciphersignature.js', stdout=asyncio.subprocess.PIPE)
            stdout, _ = await result.communicate()
            deciphered = stdout.decode('utf-8')
            self.logger.debug(f"deciphered n param \n {nparam} -> {deciphered}")
            newurl = newurl.replace(nparam, deciphered)
            newurl = "".join(newurl).strip().replace('\n', '')
        return newurl

    async def _get_decipher_functions(self):
        if self.got_functions:
            return
        async with self.session.get(self.basejslink, proxy=self.proxypreset) as response:
            logging.debug(f"request info: {json.dumps(self.request_to_dict(response.request_info))}")
            basejstext = await response.text("utf-8")
        sigpattern = r'((.*?)=function\(a\)(.*?)return a.join\(\"\"\)\}\;)'
        sigmatches = re.findall(sigpattern, basejstext[basejstext.find('return a.join("")};')-300: basejstext.find('return a.join("")};') + len('return a.join("")};')])
        functionname = sigmatches[0][1]
        self.logger.debug(f"found first function, name: {functionname}")
        wholefunctionsig = sigmatches[0][0]
        self.logger.debug(f"whole function: \n{wholefunctionsig}")
        secfunctionpattern = r';(.*?)\.(.*?)\(a'
        secondfunctionname = re.findall(secfunctionpattern, wholefunctionsig)[0][0]
        self.logger.debug(f"found second function, name: {secondfunctionname}")
        secondfunction = re.findall(fr'(var {secondfunctionname}=([\s\S]*?));var', basejstext[basejstext.find(f'var {secondfunctionname}=')-50:basejstext.find(f'var {secondfunctionname}=')+len(f'var {secondfunctionname}=') + 200])[0][0]
        self.logger.debug(f"whole function: \n{secondfunction}")
        thirdfunctionpattern = r'((.*?)=function\(a\)\{var b=([\s\S]*?)return b.join\(\"\"\)};)'
        matches = re.findall(thirdfunctionpattern, basejstext[basejstext.find('return b.join("")};')-8000:basejstext.find('return b.join("")};')+len('return b.join("")};')])
        thirdfunction = matches[0][0]
        thirdfunctionname = matches[0][1]
        self.logger.debug(f"found third function, name: {thirdfunction}")    
        self.functions = {'secondfunction': secondfunction, 'wholefunctionsig': wholefunctionsig, 
                                'functioname': functionname, 'thirdfunction': thirdfunction, 
                                'thirdfunctionname': thirdfunctionname}
        self.got_functions = True
    
    async def _extract_manifest(self, hls_manifest_url):
        async with self.session.get(hls_manifest_url, proxy=self.proxypreset) as r:
            logging.debug(f"request info: {json.dumps(self.request_to_dict(r.request_info))}")
            manifestresponse = await r.text("utf-8")
        entries = manifestresponse.split('#EXT-X-STREAM-INF:')[1:]
        audios = manifestresponse.split('#EXT-X-STREAM-INF:')[0]
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
            infodict['MAINURL'] = hls_manifest_url
            infodict['FILESIZE'] = str(round((((int(infodict.get('BANDWIDTH')) * int(self.other_video_info.get('lengthSeconds'))) / (1024*1024)) / 10), 2))
            itag_pattern = r"itag/(\d*)/"
            infodict['video_itag'] = re.findall(itag_pattern, infodict['URL'])[0]
            infodict['audio_itag'] = re.findall(itag_pattern, infodict['AUDIOLINK'])[0]
            parsedvalues[str(index)] = infodict
        self.all_formats['manifest'] = {idx: item for idx, item in enumerate(dict(sorted(parsedvalues.items(), key=lambda x: float(x[1]['FILESIZE']), reverse=True)).values())}

    def sortdictbysize(self, name: str):
        tempdict = {}
        length = int(self.other_video_info.get('lengthSeconds'))
        for key, value in self.all_formats[name].items():
            try:
                tempdict[key] = int(value["contentLength"])
            except Exception as e:
                self.logger.debug(f"some error occured when sorting key {key} and name {name}: {e}")
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
            tempdict[str(index)] = self.all_formats[name][key]
        self.all_formats[name] = tempdict
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc_value, traceback):
        self.logger.debug(f"{exc_type}, {exc_value}, {traceback}")
        if self.session:
            await self.session.close()
        if self.progress:
            self.progress.close()
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='download youtube videos in different ways, file sizes')
    parser.add_argument("link", nargs='?', help="link to a youtube video")
    parser.add_argument("--search", '-se', type=str, help='search for a youtube video with the input')
    parser.add_argument("--verbose", "-v", action='store_true', help='print out connections, information, checks if signatre deciphering is working')
    parser.add_argument('--manifest', '-m', action='store_true', help='whether to download videos from video manifest (ios)')
    parser.add_argument('--maxsize', '-s', type=int, help='maximum size in mb, may go over')
    parser.add_argument('--premerged', '-p', action='store_true', help='whether to download premerged versions only (720p, 360p, 144p 3gpp)')
    parser.add_argument('--codec', '-c', help="which video codec to download, has to be one of these ['vp9', 'avc1', 'av01', None] (if you dont know what this is, vp9 is webm, avc1 is mp4, av01 is new type of mp4 that may not work on many platforms)")
    parser.add_argument('--nodownload', '-nd', action='store_true',help='doesnt download, only gets all the information and stores in links.json and otherinfo.json')
    parser.add_argument('--priority', '-pr', default='video',type=str, help='prioritize video/audio quality. accepted argument: ["video", "audio", "none"], if none, will pair similar qualities')
    parser.add_argument('--audioonly', '-a', action='store_true', default=False, help='whether to only extract audio and return in mp3 format')
    parser.add_argument('--mp3audio', '-mp3',action='store_true',default=False, help='when downloading audio only, whether to convert it to mp3')
    parser.add_argument('--itag', '-i', type=int, help='download that specific itag and automatically pair audio to it')
    parser.add_argument("--onlyitag", "-oi", action="store_true", help="whether to only download the itag provided")
    parser.add_argument('--file-name', "-f", type=str, help='set output filename')
    parser.add_argument('--start', '-st', type=str, help='at what timestamp should the video start? MM:SS or HH:MM:SS')
    parser.add_argument('--end', '-e', type=str, help='at what timestamp should the video end? MM:SS or HH:MM:SS')
    parser.add_argument('--overwrite', '-ow', action='store_false', default=True, help='overwrites video if a video with the same title already exists')
    parser.add_argument("--returnurlonly", "-url", action="store_true", help="returns only the url")
    parser.add_argument("--proxy", type=str, help="use proxy for all connections")
    args = parser.parse_args()
    kwargs = vars(args)
    start = datetime.now()
    the = ytdownload(**kwargs)
    logging.debug(f"used arguments: \n{json.dumps(kwargs, indent=4)}")
    result = asyncio.run(the.download())
    finish=datetime.now()
    duration = finish-start
    print(f"it took {int(duration.total_seconds()//60):02}:{int(duration.total_seconds()%60):02}")
    if not isinstance(result, prettytable.PrettyTable):
        print(json.dumps(result, indent=4))
    else:
        print(result)