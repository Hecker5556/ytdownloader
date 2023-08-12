import requests
def totalfilesize(manifestinfo: dict, duration: float):
    bandwidth = int(manifestinfo.get('BANDWIDTH'))
    # totalduration = 0
    # r = requests.get(manifestinfo.get('URL'))
    # manifest = r.text
    # for i in manifest.split('#EXTINF:'):
    #     duration = float(i.split(',')[0] if not i.startswith('#') else 0)
    #     totalduration += duration
    filesize = str(round((((bandwidth * duration) / (1024*1024)) / 10), 2)) #plus minus 10-15%
    return filesize

