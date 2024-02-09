import requests, logging, re, json
async def getfunctions(link: str, verbose: bool = False, proxy = None):
    log_level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")
    basejs = requests.get(link, proxies = {
        'http': proxy,
        'https': proxy} if proxy else None, stream=True)
    sigpattern = r'((.*?)=function\(a\)(.*?)return a.join\(\"\"\)\}\;)'
    sigmatches = re.findall(sigpattern, basejs.text[basejs.text.find('return a.join("")};')-300: basejs.text.find('return a.join("")};') + len('return a.join("")};')])
    functionname = sigmatches[0][1]
    logging.debug(functionname)
    wholefunctionsig = sigmatches[0][0]
    logging.debug(wholefunctionsig)
    secfunctionpattern = r';(.*?)\.(.*?)\(a'
    secondfunctionname = re.findall(secfunctionpattern, wholefunctionsig)[0][0]
    logging.debug(secondfunctionname)
    # returna = basejs.text.find('return a.join("")') + 20
    # closestfunction = basejs.text[returna-200:returna]
    # pattern = r'(\$?\w+)=function\(a\)'
    # functionname = re.findall(pattern, closestfunction)
    # logging.debug(functionname)
    # wholefunctionsig = closestfunction[closestfunction.find(functionname[0]):returna]
    # temp2 = wholefunctionsig.split(';')
    # temp3 = None
    # for index, i in enumerate(temp2[1:-3]):
    #     if index == 0:
    #         temp3 = i.split('.')[0]
    #         continue
    #     if temp3 in i:
    #         pass
    #     else:
    #         logging.debug('irregularity ehh')
    # secondfunction = basejs.text.find(f"var {temp3}=")
    secondfunction = re.findall(fr'(var {secondfunctionname}=([\s\S]*?));var', basejs.text[basejs.text.find(f'var {secondfunctionname}=')-50:basejs.text.find(f'var {secondfunctionname}=')+len(f'var {secondfunctionname}=') + 200])[0][0]
    logging.debug(secondfunction)
    # def _extract_n_function_name(jscode):
    #         target = r'(?P<nfunc>[a-zA-Z_$][\w$]*)(?:\[(?P<idx>\d+)\])?'
    #         nfunc_and_idx = re.search(r'\.get\("n"\)\)&&\(b=(%s)\([\w$]+\)' % target, jscode)
    #         nfunc, idx = re.match(target, nfunc_and_idx.group(1)).group('nfunc', 'idx')
    #         if not idx:
    #             return nfunc

    #         VAR_RE_TMPL = r'var\s+%s\s*=\s*(?P<name>\[(?P<alias>%s)\])[;,]'
    #         note = 'Initial JS player n function {0} (%s[%s])' % (nfunc, idx)

    #         def search_function_code(needle, group):
    #             return re.search(VAR_RE_TMPL % (re.escape(nfunc), needle), jscode).group(group)

    #         if int(idx) == 0:
    #             real_nfunc = search_function_code(r'[a-zA-Z_$][\w$]*', group='alias')
    #             if real_nfunc:
    #                 return real_nfunc
    #         return json.loads(search_function_code('.+?', group='name'))[int(idx)]
    # thirdfunctionname = _extract_n_function_name(basejs.text)
    # logging.debug(thirdfunctionname)

    # maybethirdfunction = basejs.text[basejs.text.find(f'{thirdfunctionname}=function(a)'):basejs.text.find(f'{thirdfunctionname}=function(a)')+6000]
    # thirdfunction = maybethirdfunction[:maybethirdfunction.rfind('return b.join("")};')+20]
    thirdfunctionpattern = r'((.*?)=function\(a\)\{var b=([\s\S]*?)return b.join\(\"\"\)};)'
    matches = re.findall(thirdfunctionpattern, basejs.text[basejs.text.find('return b.join("")};')-8000:basejs.text.find('return b.join("")};')+len('return b.join("")};')])
    thirdfunction = matches[0][0]
    thirdfunctionname = matches[0][1]
    logging.debug(thirdfunctionname)

    return {'secondfunction': secondfunction, 'wholefunctionsig': wholefunctionsig, 
                                'functioname': functionname, 'thirdfunction': thirdfunction, 
                                'thirdfunctionname': thirdfunctionname}
