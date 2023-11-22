from urllib.parse import unquote
import subprocess, logging, requests, os
def decrypt(sigurl: str, functions: dict, verbose: bool = False, needlogin: bool = False, proxy: str = None):
    logging.basicConfig(level = logging.DEBUG if verbose else logging.info)

    secondfunction = functions.get('secondfunction')
    wholefunctionsig = functions.get('wholefunctionsig')
    functionname = functions.get('functioname')
    thirdfunction = functions.get('thirdfunction')
    thirdfunctionname = functions.get('thirdfunctionname')
    sigurl = unquote(sigurl)
    signature = sigurl.split('https')[0].replace('s=', '').replace('&sp=sig&url=', '')
    url = unquote('https' + sigurl.split('https')[1])
    a = f"\n\n{secondfunction}\n\n{wholefunctionsig}\nconsole.log({functionname}('{signature}'))"
    if not os.path.exists('videoinfo'):
        os.mkdir('videoinfo')
    with open('videoinfo/funny.js', 'w') as f1:
        f1.write(a)
    result = subprocess.run('node videoinfo/funny.js'.split(), capture_output=True, text=True)
    deciphered = result.stdout
    newurl = url + '&sig=' + deciphered
    headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'accept-language': 'en-US,en;q=0.7',
    'cache-control': 'max-age=0',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    }
    if verbose:
        if needlogin:
            import env
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
            r = requests.get(newurl,stream = True, headers=logheaders, cookies=logcookies, proxies = {
        'http': proxy,
        'https': proxy} if proxy else None)
        else:
            r = requests.get(newurl,stream = True, headers=headers, proxies = {
        'http': proxy,
        'https': proxy
    } if proxy else None)
    
        if r.status_code == 200:
            logging.debug(f'successfully deciphered:\n{signature} --> {deciphered}')
        else:
            logging.debug(r.status_code)
            logging.debug(newurl)
            return newurl
    if '&n=' in newurl:

        newurl = nparam(newurl, thirdfunction, thirdfunctionname)
    return newurl

def nparam(newurl:str, thirdfunction:str, thirdfunctionname: str):
    nparam = newurl.split('&n=')[1]
    nparam = nparam[:nparam.find('&')]
    a = f'{thirdfunction}\nconsole.log({thirdfunctionname}("{nparam}"))'
    if not os.path.exists('videoinfo'):
        os.mkdir('videoinfo')
    with open('videoinfo/funny2.js', 'w') as f1:
        f1.write(a)
    result = subprocess.run('node videoinfo/funny2.js'.split(), capture_output=True, text=True)
    newnparam = result.stdout
    logging.debug(f'deciphered n param?\n{nparam} --> {newnparam}')
    newurl = newurl.replace(nparam, newnparam)
    return "".join(newurl).strip().replace('\n', '')