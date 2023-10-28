import argparse
from main import ytdownload
from datetime import datetime
import traceback, os, asyncio, sys, logging
sys.path.append(os.path.dirname(__file__))

from getplaylist import getplaylist

parser = argparse.ArgumentParser(description='download youtube videos in different ways, file sizes')
parser.add_argument("link", nargs='?', help="link to a youtube video")
parser.add_argument("--search", '-se', type=str, help='search for a youtube video with the input')
parser.add_argument("--verbose", "-v", action='store_true', help='print out connections, information, checks if signatre deciphering is working')
parser.add_argument('--manifest', '-m', action='store_true', help='whether to download videos from video manifest (ios)')
parser.add_argument('--maxsize', '-s', type=int, help='maximum size in mb, may go over')
parser.add_argument('--premerged', '-p', action='store_true', help='whether to download premerged versions only (720p, 360p, 144p 3gpp)')
parser.add_argument('--codec', '-c', help="which video codec to download, has to be one of these ['vp9', 'avc1', 'av01', None] (if you dont know what this is, vp9 is webm, avc1 is mp4, av01 is new type of mp4 that may not work on many platforms)")
parser.add_argument('--no-download', '-nd', action='store_true',help='doesnt download, only gets all the information and stores in links.json and otherinfo.json')
parser.add_argument('--priority', '-pr', type=str, help='prioritize video/audio quality. accepted argument: ["video", "audio", "none"], if none, will pair similar qualities')
parser.add_argument('--audio-only', '-a', action='store_true', help='whether to only extract audio and return in mp3 format')
parser.add_argument('--mp3-audio', '-mp3',action='store_true', help='when downloading audio only, whether to convert it to mp3')
parser.add_argument('--itag', '-i', type=int, help='download that specific itag and automatically pair audio to it')
parser.add_argument('--file-name', "-f", type=str, help='set output filename')
parser.add_argument('--start', '-st', type=str, help='at what timestamp should the video start? MM:SS or HH:MM:SS')
parser.add_argument('--end', '-e', type=str, help='at what timestamp should the video end? MM:SS or HH:MM:SS')
parser.add_argument('--over-write', '-ow', action='store_true', help='overwrites video if a video with the same title already exists')
parser.add_argument('--dont-overwrite', '-d', action='store_true', help='doesnt overwrite video if a video with the same title exists, instead adds timestamp')
args = parser.parse_args()
class provideinput(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
if not args.link and not args.search:
    raise provideinput(f'please provide input')
class onlyoneinput(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
if args.link and args.search:
    raise onlyoneinput(f'only one input please')
if args.search:
    from ytsearch import main
    results = asyncio.run(main(args.search))
    for result in results.keys():
        print(result)
        user = str(input('is this what you were looking for? [y/n]: '))
        if user.lower() == 'y':
            args.link = results[result]
            break
start = datetime.now()
playlistlinks = None
resultdict = {}
if 'playlist?' in args.link:
    playlistlinks = asyncio.run(getplaylist.getplaylist(args.link))
    resultdict = {}
try:
    if playlistlinks:
        for index, url in enumerate(playlistlinks):
            while True:
                try:
                    result = asyncio.run(ytdownload.download(link=url, verbose=args.verbose, 
                                                manifest=args.manifest, maxsize=args.maxsize,
                                                premerged=args.premerged, codec=args.codec,
                                                nodownload=args.no_download, priority=args.priority, 
                                                audioonly=args.audio_only, mp3audio=args.mp3_audio,
                                                itag=args.itag, filename=args.file_name, start=args.start,
                                                end=args.end, overwrite=args.over_write, dontoverwrite=args.dont_overwrite))
                    resultdict[index] = result
                    break
                except ytdownload.noformatsavaliable as e:
                    print(e)
                    break
                except Exception as e:
                    print(e)
                    continue
    else:
        count = 0
        while True:
            try:
                result = asyncio.run(ytdownload.download(link=args.link, verbose=args.verbose, 
                                            manifest=args.manifest, maxsize=args.maxsize,
                                            premerged=args.premerged, codec=args.codec,
                                            nodownload=args.no_download, priority=args.priority, 
                                            audioonly=args.audio_only, mp3audio=args.mp3_audio,
                                            itag=args.itag, filename=args.file_name, start=args.start,
                                            end=args.end))
                break
            except ytdownload.noformatsavaliable:
                logging.info('no formats avaliable at ur requested settings (filesize)')
                break
            except Exception as e:
                logging.info(e)
                count += 1
                if count == 3:
                    break
                logging.info('\nTrying Again...')
except KeyboardInterrupt:
    print('cleaning up')
    for i in os.listdir():
        if i.startswith('tempvideo') or i.startswith('tempaudio') or i.startswith('merged'):
            print(f'deleting {i}')
            os.remove(i)
    for i in os.listdir('videoinfo'):
        if (i.startswith('funny') and i.endswith('.js')) or (i.startswith('segmenta') or i.startswith('segmentv')):
            print(f'deleting {i}')
            os.remove('videoinfo/'+i)
except Exception as e:
    traceback.print_exc()
    for i in os.listdir():
        if i.startswith('temp') or i.startswith('merged'):
            os.remove(i)
    for i in os.listdir('videoinfo'):
        if i.startswith('segmenta') or i.startswith('segmentv'):
            print(f'deleting {i}')
            os.remove('videoinfo/'+i)
try:
    if playlistlinks:

        print("\n".join(([": ".join((str(key), str(value))) for key, value in resultdict.items()])))
    else:
        if isinstance(result, dict):
            print(" ".join(([": ".join((str(key), str(value))) for key, value in result.items()])))
        else:
            pass
except:
    pass
finish = datetime.now()
difference = finish-start
print(f"it took {difference.seconds//60:02}:{difference.seconds%60:02}")
