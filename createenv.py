with open('.env', 'w') as f1:
    sid = str(input('SID: '))
    f1.write(f'SID = "{sid}"\n')
    hsid = str(input('HSID: '))
    f1.write(f'HSID = "{hsid}"\n')
    ssid = str(input('SSID: '))
    f1.write(f'SSID = "{ssid}"\n')
    apisid = str(input('APISID: '))
    f1.write(f'APISID = "{apisid}"\n')
    sapisid = str(input('SAPISID: '))
    f1.write(f'SAPISID = "{sapisid}"\n')
    authorization = str(input('authorization: '))
    f1.write(f'authorization = "{authorization}"\n')
    f1.write('apikey = "AIzaSyB-63vPrdThhKuerbB2N_l7Kwwcxj6yUA"')