import argparse
from main import ytdownload
from datetime import datetime
parser = argparse.ArgumentParser(description='download youtube videos in different ways, file sizes')
parser.add_argument("link", help="link to a youtube video")
parser.add_argument("--verbose", "-v", action='store_true', help='print out connections, information, checks if signatre deciphering is working')
parser.add_argument('--manifest', '-m', action='store_true', help='whether to download videos from video manifest (ios)')
parser.add_argument('--maxsize', '-s', type=int, help='maximum size in mb, may go over')
parser.add_argument('--premerged', '-p', action='store_true', help='whether to download premerged versions only (720p, 360p, 144p 3gpp)')
parser.add_argument('--codec', '-c', help="which video codec to download, has to be one of these ['vp9', 'avc1', 'av01', None] (if you dont know what this is, vp9 is webm, avc1 is mp4, av01 is new type of mp4 that may not work on many platforms)")
parser.add_argument('--no-download', '-nd', action='store_true',help='doesnt download, only gets all the information and stores in links.json and otherinfo.json')
parser.add_argument('--priority', '-pr', type=str, help='prioritize video/audio quality. accepted argument: ["video", "audio", "none"], if none, will pair similar qualities')
parser.add_argument('--audio-only', '-a', action='store_true', help='whether to only extract audio and return in mp3 format')
parser.add_argument('--mp3-audio', '-mp3',action='store_true', help='when downloading audio only, whether to convert it to mp3')
args = parser.parse_args()

start = datetime.now()
try:
    result = ytdownload.download(link=args.link, verbose=args.verbose, 
                                manifest=args.manifest, maxsize=args.maxsize,
                                premerged=args.premerged, codec=args.codec,
                                nodownload=args.no_download, priority=args.priority, 
                                audioonly=args.audio_only, mp3audio=args.mp3_audio)
except Exception as e:
    import traceback, os
    traceback.print_exc()
    for i in os.listdir():
        if i.startswith('temp') or i.startswith('merged'):
            os.remove(i)
    for i in os.listdir('videoinfo/segments'):
        os.remove(f'videoinfo/segments/{i}')
if result != 'complete':
    print(" ".join(([": ".join((str(key), str(value))) for key, value in result.items()])))
else:
    print(result)
finish = datetime.now()
difference = finish-start
print(f"it took {difference.seconds//60:02}:{difference.seconds%60:02}")
