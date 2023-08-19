import subprocess, os, logging, re, sys
try:
    from getinfo2 import getinfo
    from manifestdownload import manifestdownload
    from normaldownload import normaldownload
    from decipher import decrypt, nparam
    from getjsfunctions import getfunctions
    from extractmanifest import extractmanifest

except ModuleNotFoundError:
    sys.path.append(os.path.dirname(__file__))
    from getinfo2 import getinfo
    from manifestdownload import manifestdownload
    from normaldownload import normaldownload
    from decipher import decrypt, nparam
    from getjsfunctions import getfunctions
    from extractmanifest import extractmanifest
import asyncio, traceback
from datetime import datetime
from prettytable import PrettyTable
import requests
import json
import aiohttp

class ytdownload:
    
    def __init__(self) -> None:
        pass
    class someerror(Exception):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)
    async def merge(videourl: str, audiourl: str, mimetypevideo: str, mimetypeaudio: str, verbose: bool = False):
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")
        videoextension = mimetypevideo.split('/')[1].split(';')[0]
        audioextension = mimetypeaudio.split('/')[1].split(';')[0]

        video = await normaldownload(videourl, filename=f'tempvideo.{videoextension}')
        logging.debug(f'downloaded video, {video}')
        audio = await normaldownload(audiourl, filename=f'tempaudio.{audioextension}')
        logging.debug(f'downloaded audio, {audio}')
        if video and audio:
            logging.info('successfully downloaded both, merging now')
            try:
                result = subprocess.run(f'ffmpeg -i tempvideo.{videoextension} -i tempaudio.{audioextension} -v quiet -c:v copy {"-c:a copy " if videoextension == audioextension else ""} -map 0:v:0 -map 1:a:0 -y merged.{videoextension}'.split(), check=True)
            except Exception as e:
                print(e)
                return
            logging.debug(result.stdout)
            other = [x for x in os.listdir() if x.startswith('temp')]
            for i in [x for x in os.listdir() if x.startswith('funny') and x.endswith('.js')]:
                logging.debug(f'removing file {i}')
                os.remove(i)
            for i in other:
                logging.debug(f"removing file {i}")
                os.remove(i)
            return f'merged.{videoextension}', videoextension
        else:
            raise ytdownload.someerror(f"no idea honestly")
        
    class invalidlink(Exception):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)

    class invalidcodec(Exception):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)
            
    class noformatsavaliable(Exception):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)
    
    class theydontmix(Exception):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)

    class invalidpriority(Exception):
        def __init__(self, *args: object) -> None:
            super().__init__(*args)

    async def download(link:str, verbose: bool = False, 
                 manifest: bool = False, maxsize: int = None, 
                 premerged: bool = False, codec: str = None, 
                 nodownload: bool = False, priority: str = None, 
                 audioonly: bool = False, mp3audio: bool = False,
                 itag: int = None, filename: str = None):
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
            
            nodownload (bool, optional): Whether to only get information from the video and output to links.json.
            URLs aren't deciphered. Default is False.
            
            priority (str, optional): When finding the best format under max size, prioritize 'video', 'audio', or 'none'.
            Default is 'video'.
            
            audioonly (bool, optional): Download only the audio. Default is False.
            
            mp3audio (bool, optional): Download audio in MP3 format. Automatically sets audioonly to True.
            Default is False.

            itag (int, optional): Download specific itag

            filename (str, optional): set output filename
        """
        if premerged and manifest:
            raise ytdownload.theydontmix(f"manifests arent premerged")
        if priority:
            priority = priority.lower()
        if priority not in ['video', 'audio', 'none', None]:
            raise ytdownload.invalidpriority(f"{priority} is not a valid priority! use one of ['video', 'audio', 'None']")
        if priority == None and not manifest:
            priority = 'video'
        if priority and manifest:
            raise ytdownload.theydontmix(f'cant prioritize anything in manifests')
        if nodownload:
            if maxsize or codec or priority or premerged or manifest or audioonly:
                print('no need to specify other arguments if only getting info')
        if mp3audio and not audioonly:
            audioonly = True
        pattern1 = r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+'
        pattern2 = r'(?:https?://)?(?:www\.)?youtu\.be/[\w-]+'
        pattern3 = r'(?:https?://)?(?:www\.)?youtube\.com/shorts/[\w-]+(?:\?feature=[\w]+)?'
        match = re.findall(pattern1, link)
        if not match:
            match = re.findall(pattern2, link)
            if not match:
                match = re.findall(pattern3, link)
                if not match:
                        raise ytdownload.invalidlink(f"{link} is not a valid link, a normal link looks like https://youtu.be/id or https://youtube.com/watch?v=id")
        codecs = ['vp9', 'avc1', 'av01', 'vp09', None]
        if codec not in codecs:
            raise ytdownload.invalidcodec(f"{codec} isnt a valid video codec, use one of these: ['vp9', 'avc1', 'vp09, 'av01']")
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s - linenumber: %(lineno)d")
        links, otherinfo, basejslink, needlogin = await getinfo(link, verbose=verbose, manifest=manifest, premerged=premerged, nodownload=nodownload)
        if nodownload:
            logging.info('writing information into files')

            table = PrettyTable()
            table.field_names = ['itag', 'formattype', 'codec', 'size','resol', 'bitrate','fps', 'type', 'audioQuality', 'prot']
            functions = await getfunctions(basejslink, verbose=verbose)
            for key, value in links['mergedsig'].items():
                if value.get('contentLength'):
                    continue
                url = decrypt(value.get('signatureCipher'), functions=functions, verbose=verbose, needlogin=needlogin)
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as r:

                        contentLength = r.headers.get('content-length')
                links['mergedsig'][key]['contentLength'] = contentLength
            for key, value in links['mergednosig'].items():
                if value.get('contentLength'):
                    continue
                async with aiohttp.ClientSession() as session:
                    async with session.get(value.get('url')) as r:


                        links['mergednosig'][key]['contentLength'] = r.headers.get('content-length')
            if links['manifest'].get('0'):
                logging.info('extracting manifest info')
            links['manifest'] = extractmanifest(links['manifest']['0'], nodownload=nodownload, duration=float(links['unmergednosig']['0'].get('approxDurationMs'))/1000) if links['manifest'].get('0') else {}
            all_entries = list(links['unmergedsig'].values()) + list(links['unmergednosig'].values()) + list(links['mergednosig'].values()) + list(links['manifest'].values())
            if not os.path.exists('videoinfo'):
                os.mkdir('videoinfo')
            with open('videoinfo/links.json', 'w') as f1:
                json.dump(links, f1)
            with open('videoinfo/otherinfo.json', 'w') as f1:
                json.dump(otherinfo, f1)
            # Sort the list by bitrate
            sorted_entries = sorted(all_entries, key=lambda x: round(int(x.get('contentLength'))/(1024*1024), 2) if x.get('contentLength') else float(x.get('FILESIZE')), reverse=False)
            for entrydata in sorted_entries:
                itag = entrydata.get('itag') if entrydata.get('itag') else entrydata.get('URL').split('itag/')[1].split('/')[0]
                formattype = entrydata.get('mimeType', 'video/mp4').split(';')[0]
                codec = entrydata.get('mimeType').split('codecs=')[1].replace('"', '') if entrydata.get('mimeType') else entrydata.get('CODECS')
                try:
                    filesize = f"{round(int(entrydata.get('contentLength'))/(1024*1024), 2)}mb" if entrydata.get('contentLength') else '~'+ str(entrydata.get('FILESIZE')) + 'mb'
                except Exception as e:
                    logging.info(e)
                    logging.info(entrydata)
                resolution = "x".join([str(entrydata.get('width')), str(entrydata.get('height'))]) if entrydata.get('width') else entrydata.get('RESOLUTION')
                bitrate = entrydata.get('bitrate') if entrydata.get('bitrate') else entrydata.get('BANDWIDTH')
                fps = entrydata.get('fps') if entrydata.get('fps') else entrydata.get('FRAME-RATE')
                vidaud = 'both' if entrydata.get('CODECS') else 'audio' if 'audio' in entrydata.get('mimeType') else 'both' if entrydata.get('itag') in ['22', '18', '17', 22, 18, 17] else  'video' if 'video' in entrydata.get('mimeType') else 'None'
                newlist = [itag, formattype, codec, filesize, resolution, bitrate, fps, vidaud]
                for i in table.field_names[8:-1]:
                    newlist.append(entrydata.get(i, 'not available'))
                if entrydata.get('BANDWIDTH'):
                    newlist.append('m3u8')
                else:
                    newlist.append('https')
                table.add_row(newlist)
            print(table)

            return table
        video = None
        audio = None
        manifestvideo = None
        videoandaudio = None
        if maxsize and not itag:
            videoids = []
            audioids = []
            # if manifest:
            #     for key, value in links['manifest']:
            #         videoids.append(key)
                    
            
            if links['unmergedsig'] != {} and not manifest and not premerged:
                logging.info('downloading unmerged signatured')
                for key, value in links['unmergedsig'].items():
                    if codec and codec in value.get('mimeType'):
                        videoids.append(key)
                    elif 'video' in value.get('mimeType') and not codec and not audioonly:
                        videoids.append(key)
                    elif 'audio' in value.get('mimeType'):
                        if not mp3audio:
                            audioids.append(key)
                        else:
                            if 'mp4a' in value.get('mimeType'):
                                audioids.append(key)
                if priority == 'video' and not audioonly:
                    for videof in videoids:
                        for audiof in audioids:
                            if int(links['unmergedsig'][videof].get('contentLength'))/(1024*1024) + int(links['unmergedsig'][audiof].get('contentLength'))/(1024*1024) > maxsize:
                                logging.debug(f"{videof} and {audiof} too big")
                                continue
                            else:
                                logging.debug(f"found pair, checking if same codecs {videof}, {audiof}")
                                video = links['unmergedsig'][videof]

                                logging.debug(f"{links['unmergedsig'][audiof]['mimeType'].split(';')[0].split('/')[1]}, {video['mimeType']}")
                                if links['unmergedsig'][audiof]['mimeType'].split(';')[0].split('/')[1] in video['mimeType']:
                                    audio = links['unmergedsig'][audiof]
                                    logging.debug('found optimal pair')
                                    break
                                else:
                                    logging.debug('nah')
                                    continue
                        if video and audio:
                            break
                    if video and not audio:
                        #gonna have to mix codecs 
                        logging.info('resorting to mixed codecs, merging will take longer')
                        for videof in videoids:
                            for audiof in audioids:
                                if int(links['unmergedsig'][videof].get('contentLength'))/(1024*1024) + int(links['unmergedsig'][audiof].get('contentLength'))/(1024*1024) > maxsize:
                                    continue
                                else:
                                    video = links['unmergedsig'][videof]
                                    audio = links['unmergedsig'][audiof]
                                    break
                            if video and audio:
                                break
                elif priority == 'audio' and not audioonly:
                    for audiof in audioids:
                        for videof in videoids:
                            if int(links['unmergedsig'][videof].get('contentLength'))/(1024*1024) + int(links['unmergedsig'][audiof].get('contentLength'))/(1024*1024) > maxsize:
                                continue
                            else:
                                video = links['unmergedsig'][videof]
                                if links['unmergedsig'][audiof]['mimeType'].split(';')[0].split('/')[1] in video['mimeType']:
                                    audio = links['unmergedsig'][audiof]
                                    break
                                else:
                                    continue
                        if video and audio:
                            break
                    if video and not audio:
                        #gonna have to mix codecs 
                        logging.info('resorting to mixed codecs, merging will take longer')
                        for audiof in audioids:
                            for videof in videoids:
                                if int(links['unmergedsig'][videof].get('contentLength'))/(1024*1024) + int(links['unmergedsig'][audiof].get('contentLength'))/(1024*1024) > maxsize:
                                    continue
                                else:
                                    video = links['unmergedsig'][videof]
                                    audio = links['unmergedsig'][audiof]
                                    break
                            if video and audio:
                                break
                else:
                    if not audioonly:
                        for videof, audiof in zip(videoids, audioids):
                                if int(links['unmergedsig'][videof].get('contentLength'))/(1024*1024) + int(links['unmergedsig'][audiof].get('contentLength'))/(1024*1024) > maxsize:
                                    continue
                                else:
                                    video = links['unmergedsig'][videof]
                                    if links['unmergedsig'][audiof]['mimeType'].split(';')[0].split('/')[1] in video['mimeType']:
                                        audio = links['unmergedsig'][audiof]
                                        break
                                    else:
                                        continue
                        if video and not audio:
                            #gonna have to mix codecs 
                            logging.info('resorting to mixed codecs, merging will take longer')
                            for videof, audiof in zip(videoids, audioids):
                                    if int(links['unmergedsig'][videof].get('contentLength'))/(1024*1024) + int(links['unmergedsig'][audiof].get('contentLength'))/(1024*1024) > maxsize:
                                        continue
                                    else:
                                        video = links['unmergedsig'][videof]
                                        audio = links['unmergedsig'][audiof]
                                        break
                    else:
                        for audiof in audioids:
                            if int(links['unmergedsig'][audiof].get('contentLength'))/(1024*1024)>maxsize:
                                continue
                            else:
                                audio = links['unmergedsig'][audiof]
                                break
                if not video:
                    if not audioonly and not audio:
                        raise ytdownload.noformatsavaliable(f"no formats avaliable that are under {maxsize}mb")
                if not audio:
                    raise ytdownload.noformatsavaliable(f'no formats avaliable that fit under filesize {maxsize}mb')
                logging.debug('getting javascript functions')
                functions = await getfunctions(basejslink, verbose=verbose)
                if not audioonly:
                    logging.debug(f'deciphering itag: {video.get("itag")}')
                    video['url'] = decrypt(video.get('signatureCipher'), functions, verbose=verbose, needlogin=needlogin)
                logging.debug(f'deciphering itag: {audio.get("itag")}')
                audio['url'] = decrypt(audio.get('signatureCipher'), functions, verbose=verbose, needlogin=needlogin)

            elif links['unmergednosig'] != {} and not manifest and not premerged:
                logging.info('downloading unmerged no signatured')
                for key, value in links['unmergednosig'].items():
                    if codec and codec in value.get('mimeType'):
                        videoids.append(key)
                    elif 'video' in value.get('mimeType') and not codec and not audioonly:
                        videoids.append(key)
                    elif 'audio' in value.get('mimeType'):
                        if not mp3audio:
                            audioids.append(key)
                        else:
                            if 'mp4a' in value.get('mimeType'):
                                audioids.append(key)
                if priority == 'video' and not audioonly:
                    for videof in videoids:
                        for audiof in audioids:
                            if int(links['unmergednosig'][videof].get('contentLength'))/(1024*1024) + int(links['unmergednosig'][audiof].get('contentLength'))/(1024*1024) > maxsize:
                                continue
                            else:
                                video = links['unmergednosig'][videof]
                                if links['unmergednosig'][audiof]['mimeType'].split(';')[0].split('/')[1] in video['mimeType']:
                                    audio = links['unmergednosig'][audiof]
                                    break
                                else:
                                    continue
                        if video and audio:
                            break
                    if video and not audio:
                        #gonna have to mix codecs 
                        logging.info('resorting to mixed codecs, merging will take longer')
                        for videof in videoids:
                            for audiof in audioids:
                                if int(links['unmergednosig'][videof].get('contentLength'))/(1024*1024) + int(links['unmergednosig'][audiof].get('contentLength'))/(1024*1024) > maxsize:
                                    continue
                                else:
                                    video = links['unmergednosig'][videof]
                                    audio = links['unmergednosig'][audiof]
                                    break
                            if video and audio:
                                break
                elif priority == 'audio' and not audioonly:
                    for audiof in audioids:
                        for videof in videoids:
                            if int(links['unmergednosig'][videof].get('contentLength'))/(1024*1024) + int(links['unmergednosig'][audiof].get('contentLength'))/(1024*1024) > maxsize:
                                continue
                            else:
                                video = links['unmergednosig'][videof]
                                if links['unmergednosig'][audiof]['mimeType'].split(';')[0].split('/')[1] in video['mimeType']:
                                    audio = links['unmergednosig'][audiof]
                                    break
                                else:
                                    continue
                        if video and audio:
                            break
                    if video and not audio:
                        #gonna have to mix codecs 
                        logging.info('resorting to mixed codecs, merging will take longer')
                        for audiof in audioids:
                            for videof in videoids:
                                if int(links['unmergednosig'][videof].get('contentLength'))/(1024*1024) + int(links['unmergednosig'][audiof].get('contentLength'))/(1024*1024) > maxsize:
                                    continue
                                else:
                                    video = links['unmergednosig'][videof]
                                    audio = links['unmergednosig'][audiof]
                                    break
                            if video and audio:
                                break
                else:
                    if not audioonly:
                        for videof, audiof in zip(videoids, audioids):
                            if int(links['unmergednosig'][videof].get('contentLength'))/(1024*1024) + int(links['unmergednosig'][audiof].get('contentLength'))/(1024*1024) > maxsize:
                                continue
                            else:
                                video = links['unmergednosig'][videof]
                                if links['unmergednosig'][audiof]['mimeType'].split(';')[0].split('/')[1] in video['mimeType']:
                                    audio = links['unmergednosig'][audiof]
                                    break
                                else:
                                    continue
                    if video and not audio:
                        #gonna have to mix codecs 
                        logging.info('resorting to mixed codecs, merging will take longer')
                        for videof, audiof in zip(videoids, audioids):
                                if int(links['unmergednosig'][videof].get('contentLength'))/(1024*1024) + int(links['unmergednosig'][audiof].get('contentLength'))/(1024*1024) > maxsize:
                                    continue
                                else:
                                    video = links['unmergednosig'][videof]
                                    audio = links['unmergednosig'][audiof]
                                    break
                    else:
                        for audiof in audioids:
                            if int(links['unmergednosig'][audiof].get('contentLength'))/(1024*1024)>maxsize:
                                continue
                            else:
                                audio = links['unmergednosig'][audiof]
                                break
                if not video and not audio:
                    raise ytdownload.noformatsavaliable(f"no formats avaliable that are under {maxsize}mb")
                if not audio:
                    raise ytdownload.noformatsavaliable(f'no formats avaliable that fit under filesize {maxsize}')
                logging.debug('deciphering n param')
                functions = await getfunctions(basejslink, verbose=verbose)
                if not audioonly:
                    video['url'] = nparam(video.get('url'), functions.get('thirdfunction'), functions.get('thirdfunctionname'))
                audio['url'] = nparam(audio.get('url'), functions.get('thirdfunction'), functions.get('thirdfunctionname'))
            elif premerged and not manifest and not audioonly:
                
                logging.info('downloading merged no sig')
                videoandaudio = []
                if links['mergednosig'] != {}:
                    for key, value in  links['mergednosig'].items():
                        if codec and codec in value.get('mimeType'):
                            videoandaudio.append(key)
                        elif not codec:
                            videoandaudio.append(key)
                    for videos in videoandaudio:
                        if int(links['mergednosig'][videos].get('contentLength'))/(1024*1024) > maxsize:
                            continue
                        else:
                            video = links['mergednosig'][videos]
                    if not video:
                        logging.info('couldnt find suitable match')
                        raise ytdownload.noformatsavaliable(f"no formats avaliable that are under {maxsize}mb")

                else:
                    logging.info('couldnt find merged with no sig, resorting to signatured')
                    for key, value in links['mergedsig'].items():
                        if codec and codec in value.get('mimeType'):
                            videoandaudio.append(key)
                        elif not codec:
                            videoandaudio.append(key)
                    for videos in videoandaudio:
                        if int(links['mergedsig'][videos].get('contentLength'))/(1024*1024)>maxsize:
                            continue
                        else:
                            video = links['mergedsig'][videos]
                    if not video:
                        logging.info('couldnt find suitable match')
                        raise ytdownload.noformatsavaliable(f"no formats avaliable that are under {maxsize}mb")
            elif manifest:
                manifestvideo = None
                manifestkeys = []
                logging.info('downloading from manifest')
                for key, value in links['manifest'].items():
                    if codec and codec in value.get('CODECS'):
                        manifestkeys.append(key)
                    elif not codec:
                        manifestkeys.append(key)
                    
                for mkey in manifestkeys:
                    if float(links['manifest'][mkey].get('FILESIZE'))>maxsize:
                        continue
                    else:
                        manifestvideo = links['manifest'][mkey]
                        break
                if not manifestvideo:
                    raise ytdownload.noformatsavaliable(f"no formats avaliable that are under {maxsize}mb")

        
        else:
            if itag:
                if itag in [17, 18, 22]:
                    premerged=True
                    for key, value in links['mergednosig'].items():
                        if value.get('itag') == itag:
                            video = value
                            logging.info(f'found video with itag {itag}')
                            break
                    if not video:
                        for key, value in links['mergedsig'].items():
                            if value.get('itag') == itag:
                                logging.info(f'found signatured video with itag {itag}')
                                video = value
                                break
                        if video:
                            functions = await getfunctions(basejslink, verbose=verbose)
                            video['url'] = decrypt(video.get('signatureCipher'), functions, verbose=verbose, needlogin=needlogin)
                    if not video:
                        raise ytdownload.noformatsavaliable(f"Idk i couldnt find the formats u want")

                if links['unmergedsig'] != {}:
                    for key, value in links['unmergedsig'].items():
                        if int(value.get('itag')) == itag:
                            video = value
                            logging.info('found video with itag')
                            break
                    if video:
                        for key, value in links['unmergedsig'].items():
                            if 'audio' in value.get('mimeType'):
                                audio = value
                                break
                        logging.info(f'pairing itag {itag}({video.get("itag")} with audio itag {audio.get("itag")})')
                        logging.debug('getting functions')
                        functions = await getfunctions(basejslink, verbose=verbose)
                        video['url'] = decrypt(video.get('signatureCipher'), functions, verbose=verbose, needlogin=needlogin)
                        audio['url'] = decrypt(audio.get('signatureCipher'), functions, verbose=verbose, needlogin=needlogin)
                        logging.debug('got decrypted')
                if links['unmergednosig'] != {} and not video and not audio:
                    for key, value in links['unmergednosig'].items():
                        if int(value.get('itag')) == itag:
                            logging.info(f'found unmerged no sig video with itag {itag}')
                            video = value
                            break
                    if video:
                        for key, value in links['unmergednosig'].items():
                            if 'audio' in value.get('mimeType'):
                                audio = value
                                break
                        logging.info(f'paring itag {itag}({video.get("itag")} with audio itag {audio.get("itag")})')
                        logging.debug('getting functions')
                        functions = await getfunctions(basejslink, verbose=verbose)
                        video['url'] = nparam(video.get('url'), thirdfunction=functions.get('thirdfunction'), thirdfunctionname=functions.get('thirdfunctionname'))
                        audio['url'] = nparam(audio.get('url'),thirdfunction=functions.get('thirdfunction'), thirdfunctionname=functions.get('thirdfunctionname'))
                        logging.debug('got decrypted')
                if links['manifest'] != {} and not video:
                    logging.debug('extracting manifest info')
                    links['manifest'] = extractmanifest(links['manifest']['0'], nodownload=nodownload, duration=float(links['unmergednosig']['0'].get('approxDurationMs'))/1000)
                    for key, value in links['manifest'].items():
                        if value.get('URL').split('/itag/')[1].split('/')[0] == str(itag):
                            logging.info(f'found manifest with itag {itag}')
                            manifestvideo = value
                            manifest = True
                            break
                if not manifestvideo and not video:
                    raise ytdownload.noformatsavaliable(f'couldnt find itag {itag}')
                
                

                
            
            
            elif not premerged and not manifest:
                if links['unmergedsig'] != {}:
                    for key, value in links['unmergedsig'].items():
                        if not audioonly:
                            if codec and codec in value.get('mimeType'):
                                video = value
                                break
                            if 'video' in value.get('mimeType') and not codec:
                                video = value
                                break
                    for key, value in links['unmergedsig'].items():
                        if 'audio' in value.get('mimeType'):
                            if not audioonly:
                                if value.get('mimeType').split(';')[0].split('/')[1] in video.get('mimeType'):
                                    audio = value
                                    break
                            else:
                                if not mp3audio:
                                    audio = value
                                    break
                                else:
                                    if 'mp4a' in value.get('mimeType'):
                                        audio = value
                                        break
                    if not audio:
                        #different codec
                        for key, value in links['unmergedsig'].items():
                            if 'audio' in value.get('mimeType'):
                                audio = value
                                break
                    logging.debug('getting javascript functions')
                    functions = await getfunctions(basejslink, verbose=verbose)
                    if not audioonly:
                        logging.debug(f'deciphering itag: {video.get("itag")}')
                        video['url'] = decrypt(video.get('signatureCipher'), functions, verbose=verbose, needlogin=needlogin)
                    logging.debug(f'deciphering itag: {audio.get("itag")}')
                    audio['url'] = decrypt(audio.get('signatureCipher'), functions, verbose=verbose, needlogin=needlogin)
                elif links['unmergednosig'] != {} and not manifest and not premerged:
                    logging.info('downloading unmerged no signatured')
                    logging.debug('gonna decipher n param')
                    functions = await getfunctions(basejslink, verbose=verbose)
                    if not audioonly:
                        for key, value in links['unmergednosig'].items():
                            if codec and codec in value.get('mimeType'):
                                video = value
                                break
                            elif not codec and 'video' in value.get('mimeType'):
                                video = value
                                break
                        logging.debug(f'deciphering n param for video itag: {video.get("itag")}')
                        video['url'] = nparam(video.get('url'), thirdfunction=functions.get('thirdfunction'), thirdfunctionname=functions.get('thirdfunctionname'))
                        logging.debug(video['url'])
                    for key, value in links['unmergednosig'].items():
                            if not audioonly:
                                if value.get('mimeType').split(';')[0].split('/')[1] in video.get('mimeType') and 'audio' in video.get('mimeType'):
                                    audio = value
                                    break
                            else:
                                if 'audio' in value.get('mimeType'):
                                    if not mp3audio:
                                        audio = value
                                        break
                                    else:
                                        if 'mp4a' in value.get('mimeType'):
                                            audio = value
                                            break
                    if not audio:
                        #different codec
                        for key, value in links['unmergednosig'].items():
                            if 'audio' in value.get('mimeType'):
                                audio = value
                                break
                    logging.debug(f'deciphering n param for itag: {audio.get("itag")}')
                    audio['url'] = nparam(audio.get('url'), thirdfunction=functions.get('thirdfunction'), thirdfunctionname=functions.get('thirdfunctionname'))
                    logging.debug(audio['url'])
            elif premerged and not manifest and not audioonly:
                if links['mergednosig'] != {}:
                    logging.info('downloading from merged not signatured')
                    for key, value in links['mergednosig'].items():
                        if codec and codec in value.get('mimeType'):
                            video = links['mergednosig'][key]
                        elif not codec:
                            video = links['mergednosig'][key]
                        break
                elif links['mergedsig'] != {}:
                    logging.info('downloading from merged signatured')
                    for key, value in links['mergedsig'].items():
                        if codec and codec in value.get('mimeType'):
                            video = links['mergedsig'][key]
                        elif not codec:
                            video = links['mergedsig'][key]
                        break
                    logging.debug('getting javascript functions')
                    functions = await getfunctions(basejslink, verbose=verbose)
                    logging.debug(f'deciphering itag: {video.get("itag")}')
                    video['url'] = decrypt(video.get('signatureCipher'), functions, verbose=verbose, needlogin=needlogin)
                else:
                    logging.info('no merged formats found?')
                    raise ytdownload.someerror(f'bruh idk')

                    
            elif manifest:
                if links['manifest'] != {}:
                    logging.info('downloading from manifest')
                    manifestvideo = None
                    manifestkeys = []
                    for key, value in links['manifest'].items():
                        if codec and codec in value.get('CODECS'):
                            manifestvideo = value
                            break
                        elif not codec:
                            manifestvideo = value
                            break
                else:
                    logging.info('no manifest found?')
                    raise ytdownload.someerror(f"no manifest found man idk")
                
                    




        if not manifest and not premerged and not audioonly:
            result = await ytdownload.merge(video.get('url'), audio.get('url'), video.get('mimeType'), audio.get('mimeType'), verbose=verbose)
        elif premerged and not audioonly:
            result = await normaldownload(video.get('url'), filename=f"merged.{video.get('mimeType').split('/')[1].split(';')[0]}")
        elif manifest and not audioonly:
            logging.info(f'downloading manifest: {manifestvideo.get("BANDWIDTH")} {manifestvideo.get("RESOLUTION")} {manifestvideo.get("FILESIZE")}mb')
            result = manifestdownload(manifestvideo, verbose=verbose)
        elif audioonly:
            if not manifest:
                result = await normaldownload(audio.get('url'), filename=f"merged.{audio.get('mimeType').split('/')[1].split(';')[0] if audio.get('mimeType').split('/')[1].split(';')[0] == 'webm' else 'mp3'}")
                if mp3audio:
                    result = await normaldownload(audio.get('url'), filename='merged.mp3')
            else:
                result = manifestdownload(manifestvideo, audioonly=True, verbose=verbose)
        if result and not filename:
            filename = "".join([x for x in otherinfo.get('title')+f'.{result[1]}' if x not in "\/:*?<>|"])
        elif result and filename:
            filename = filename + f'.{result[1]}'
            filename = "".join([x for x in filename if x not in '\/:*?<>|'])
        if result:
            try:
                os.rename(result[0], filename)
            except FileExistsError:
                while True:
                    choice = str(input("file with the same name exists already!\nwould you like to overwrite the file? [y/n]: "))
                    choice = choice.lower()
                    if choice not in ['y', 'n']:
                        continue
                    else:
                        break
                if choice == 'n':
                    timestamp = str(round(datetime.now().timestamp()))
                    extension = result[1]
                    filetitle = "".join([x for x in otherinfo.get('title') if x not in "\/:*?<>|()"])
                    filename = f"{filetitle}{timestamp}.{extension}"
                    os.rename(result[0], filename)
                else:
                    os.remove(filename)
                    os.rename(result[0], filename)
            except Exception as e:
                traceback.print_exc()
            if not manifest and premerged and not audioonly:
                return {'filename': filename,
                    'width': video.get('width'),
                    'height': video.get('height'),
                    'mimeType': video.get('mimeType'),
                    'filesize': str(round(os.path.getsize(filename)/(1024*1024),2)),
                    'bitrate': video.get('bitrate'),
                    'fps': video.get('fps'),
                    'audioquality': video.get('audioQuality')}
            elif not manifest and audio and not audioonly:
                maincommand = 'ffprobe -v quiet -print_format json -show_format -show_streams -i '.split()
                maincommand.append(f"{filename}")
                return {'filename': filename,
                    'width': video.get('width'),
                    'height': video.get('height'),
                    'audio quality': audio.get('audioQuality'),
                    'video codec': video.get('mimeType'),
                    'original audio codec': audio.get('mimeType'),
                    'audio codec': json.loads(subprocess.check_output(maincommand))['streams'][1]['codec_name'],
                    'filesize': str(round(os.path.getsize(filename)/(1024*1024),2)),
                    'videobitrate': video.get('bitrate'),
                    'audiobitrate': audio.get('bitrate'),
                    'fps': video.get('fps')}
            elif manifest and not audioonly:
                maincommand = 'ffprobe -v quiet -print_format json -show_format -show_streams -i '.split()
                maincommand.append(f"{filename}")
                return {'filename': filename,
                        'width': manifestvideo.get('RESOLUTION').split('x')[0],
                        'height': manifestvideo.get('RESOLUTION').split('x')[1],
                        'codec': manifestvideo.get('CODECS'),
                        'audiocodec': json.loads(subprocess.check_output(maincommand))['streams'][1]['codec_name'],
                        'audiobitrate': json.loads(subprocess.check_output(maincommand))['streams'][1]['bit_rate'],
                        'filesize': str(round(os.path.getsize(filename)/(1024*1024),2)),
                        'bitrate': manifestvideo.get('BANDWIDTH'),
                        'fps': manifestvideo.get('FRAME-RATE')}
            else:
                if audioonly and not manifest:
                    thecommand = 'ffprobe -v quiet -print_format json -show_format -show_streams -i'.split()
                    thecommand.append(f"{filename}")
                    logging.info(thecommand)
                    return {'filename': filename,
                            'codec': audio.get('mimeType').split('; ')[1],
                            'audioQuality': audio.get('audioQuality'),
                            'filesize': str(round(os.path.getsize(filename)/(1024*1024),2)),
                            'bitrate':str(int(json.loads(subprocess.check_output(thecommand))['format'].get('bit_rate'))/1000) +' kbs'}
                if audioonly and manifest:
                    maincommand = 'ffprobe -v quiet -print_format json -show_format -show_streams -i '.split()
                    maincommand.append(f"{filename}")
                    return {'filename': filename,
                            'codec': manifestvideo.get('CODECS').split(',')[1],
                            'actualcodec': json.loads(subprocess.check_output(maincommand))['streams'][1]['codec_name'],
                            'filesize': str(round(os.path.getsize(filename)/(1024*1024),2)),
                            'bitrate': str(int(json.loads(subprocess.run(f'ffprobe -v quiet -print_format json -show_format -show_streams -i {filename}'.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout)['streams'].get('bit_rate'))/1000) +' kbs'}
        else:
            raise ytdownload.someerror(f"some error, no result")

