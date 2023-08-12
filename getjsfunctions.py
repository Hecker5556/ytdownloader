import requests, logging, re, json
def getfunctions(link: str, verbose: bool = False):
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")
    basejs = requests.get(link)
    returna = basejs.text.find('return a.join("")') + 20
    closestfunction = basejs.text[returna-150:returna]
    pattern = r'\b(\w+)\s*=\s*function\(a\)'
    functionname = re.findall(pattern, closestfunction)
    wholefunctionsig = closestfunction[closestfunction.find(functionname[0]):returna]
    temp2 = wholefunctionsig.split(';')
    temp3 = None
    for index, i in enumerate(temp2[1:-3]):
        if index == 0:
            temp3 = i.split('.')[0]
            continue
        if temp3 in i:
            pass
        else:
            logging.debug('irregularity ehh')
    secondfunction = basejs.text.find(f"var {temp3}=")
    maybesecondfunction = basejs.text[secondfunction:secondfunction+150]
    secondfunction = maybesecondfunction.split('}};')[0] + '}};'
    def _extract_n_function_name(jscode):
            target = r'(?P<nfunc>[a-zA-Z_$][\w$]*)(?:\[(?P<idx>\d+)\])?'
            nfunc_and_idx = re.search(r'\.get\("n"\)\)&&\(b=(%s)\([\w$]+\)' % target, jscode)
            nfunc, idx = re.match(target, nfunc_and_idx.group(1)).group('nfunc', 'idx')
            if not idx:
                return nfunc

            VAR_RE_TMPL = r'var\s+%s\s*=\s*(?P<name>\[(?P<alias>%s)\])[;,]'
            note = 'Initial JS player n function {0} (%s[%s])' % (nfunc, idx)

            def search_function_code(needle, group):
                return re.search(VAR_RE_TMPL % (re.escape(nfunc), needle), jscode).group(group)

            if int(idx) == 0:
                real_nfunc = search_function_code(r'[a-zA-Z_$][\w$]*', group='alias')
                if real_nfunc:
                    return real_nfunc
            return json.loads(search_function_code('.+?', group='name'))[int(idx)]
    thirdfunctionname = _extract_n_function_name(basejs.text)

    maybethirdfunction = basejs.text[basejs.text.find(f'{thirdfunctionname}=function(a)'):basejs.text.find(f'{thirdfunctionname}=function(a)')+6000]
    thirdfunction = maybethirdfunction[:maybethirdfunction.rfind('return b.join("")};')+20]

    return {'secondfunction': secondfunction, 'wholefunctionsig': wholefunctionsig, 
                                'functioname': functionname, 'thirdfunction': thirdfunction, 
                                'thirdfunctionname': thirdfunctionname}
