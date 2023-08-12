import requests
from tqdm import tqdm

def paralleldownloader(url:str, filename: str):
    headers = {'range': 'bytes=0-',}

    r = requests.get(url, stream=False, headers=headers)
    if r.status_code != 200 and r.status_code != 204:
        raise requests.ConnectionError(f'{r.status_code}')
    progress = tqdm(total=None, unit='iB', unit_scale=True)
    with open(filename, 'wb') as f1:
        
        progress.update(len(r.content))
        f1.write(r.content)
    progress.close()
    return True