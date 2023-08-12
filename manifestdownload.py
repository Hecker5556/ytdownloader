from pprint import pformat
import subprocess, os, traceback
import logging

def manifestdownload(manifest: dict, verbose: bool = False, audioonly: bool = False):
    if not os.path.exists('videoinfo'):
        os.mkdir('videoinfo')
    with open('videoinfo/manifest.txt', 'w') as f1:
        f1.write(pformat(manifest))
    #DOWNLOAD VIDEOS
    logging.basicConfig(level=logging.DEBUG if verbose else logging.info)
    logging.info('downloading chunked manifest videos...')

    try:
        subprocess.check_output(f'ffmpeg {"-i "+manifest.get("URL") if not audioonly else ""} -i {manifest.get("AUDIOLINK")} -v quiet -c copy merged.{"mp4" if not audioonly else "mp3"}')
    except Exception as e:
        traceback.print_exc()
    return f'merged.{"mp4" if not audioonly else "mp3"}', "mp4" if not audioonly else "mp3"
