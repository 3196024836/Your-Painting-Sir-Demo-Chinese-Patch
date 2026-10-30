"""Extract candidate player-facing text, with exact Lua locations for review."""
import csv
from pathlib import Path
import re
import sys
import zipfile
from lua_strings import extract_literals

_FIELDS = {
    'data/dialog/': {'text'},
    'data/phone/': {'text', 'title', 'description'},
    'data/paintings/': {'title', 'description', 'name', 'last_name', 'born_died', 'year'},
    'data/menu_data.lua': {'title', 'description'},
    'data/newspaper_comments.lua': {'text'},
    'src/': {'text'},
}


def _masked(source, literals):
    chars=list(source)
    for literal in literals:
        for i in range(literal.start,literal.end):
            if chars[i] not in '\r\n': chars[i]=' '
    masked=''.join(chars)
    return re.sub(r'--[^\n]*',lambda m:' ' * len(m.group(0)),masked)


def _array_spans(masked):
    spans=[]
    for m in re.finditer(r'\b(text|description)\s*=\s*\{',masked):
        depth=1;i=m.end()
        while i<len(masked) and depth:
            if masked[i]=='{': depth+=1
            elif masked[i]=='}': depth-=1
            i+=1
        if not depth:spans.append((m.end(),i-1,m.group(1)))
    return spans


def _call_argument_spans(masked, function_name, target_argument):
    """Locate a positional argument without mistaking nested tables/calls for separators."""
    spans=[]
    for match in re.finditer(r'\b' + re.escape(function_name) + r'\s*\(', masked):
        depth=1
        braces=0
        argument=1
        start=match.end()
        i=start
        while i<len(masked) and depth:
            c=masked[i]
            if c in ',)' and depth==1 and braces==0:
                if argument==target_argument:
                    spans.append((start,i))
                    break
                if c==')': break
                argument+=1
                start=i+1
            if c=='(': depth+=1
            elif c==')': depth-=1
            elif c=='{': braces+=1
            elif c=='}': braces-=1
            i+=1
    return spans


def _note_text_spans(masked):
    return _call_argument_spans(masked, 'Note', 4)


def _field(source, masked, literal, array_spans):
    prefix=masked[max(0,literal.start-180):literal.start]
    direct=re.search(r'\b([A-Za-z_][A-Za-z_0-9]*)\s*=\s*$',prefix)
    if direct:return direct.group(1)
    for start,end,key in array_spans:
        if start<=literal.start<end:return key
    return None


def _src_candidate(name, text, preceding, field):
    if field=='text' and not text.startswith('['): return True
    if name=='src/cutting/solution_data.lua': return bool(re.search('[A-Za-z]',text))
    if name=='src/screens/menu/main/menu.lua' and field=='text': return True
    if name.startswith('src/locale/') or 'debug' in name or 'pixel_data/' in name: return False
    # Include descriptive sentence fragments for manual review; exclude asset paths and code.
    if re.search(r'[A-Za-z]{2}',text) and (' ' in text or re.search(r'[!?]',text)):
        if re.search(r'[/\\]|\.lua|\.png|\.ogg|^(core|src|data|libs)[./]',text): return False
        if text in ('return ',): return False
        return True
    if re.search(r'(?:Text\s*\(|:write\s*\(|:setText\s*\()\s*$',preceding) and re.search(r'[A-Za-z]',text):
        return True
    return False


def candidates(path, source):
    prefix=next((p for p in _FIELDS if path.startswith(p)),None)
    if not prefix:return []
    literals=extract_literals(source)
    masked=_masked(source,literals)
    spans=_array_spans(masked)
    note_spans=_note_text_spans(masked) if prefix=='src/' else []
    text_spans=_call_argument_spans(masked, 'Text', 3) if prefix=='src/' else []
    results=[]
    for lit in literals:
        field=_field(source,masked,lit,spans)
        allowed=field in _FIELDS[prefix]
        if path=='data/phone/characters.lua' and field=='name': allowed=True
        if path=='data/phone/crab_lines.lua' and re.search('[A-Za-z]',lit.value): allowed=True
        if path=='data/dialog/workshop/butler/comments/missing.lua' and re.search('[A-Za-z]',lit.value):allowed=True
        if prefix=='src/':
            in_note=any(start <= lit.start < end for start,end in note_spans)
            in_text=any(start <= lit.start < end for start,end in text_spans)
            allowed=in_note or in_text or _src_candidate(path,lit.value,masked[max(0,lit.start-100):lit.start],field)
            if in_note: field='note_text'
            elif in_text: field='display_text'
        if not allowed or not lit.value:continue
        prev=source[max(0,lit.start-700):lit.start]
        roles=re.findall(r'\bcharacter\s*=\s*["\']([^"\']+)["\']',prev)
        column=lit.start - (source.rfind('\n',0,lit.start)+1) + 1
        results.append({'path':path,'line':lit.line,'column':column,'speaker':roles[-1] if roles else '',
                        'field':field or '', 'original':lit.value,'translation':'','status':'待翻译','note':''})
    return results


def main():
    if len(sys.argv)!=3:
        raise SystemExit('usage: inventory.py GAME_EXE OUTPUT_CSV')
    output=Path(sys.argv[2])
    if output.exists():raise SystemExit('输出清单已存在；为避免覆盖审校结果，停止。')
    rows=[]
    with zipfile.ZipFile(sys.argv[1]) as z:
        for name in z.namelist():
            if name.endswith('.lua') and any(name.startswith(p) for p in _FIELDS):
                rows.extend(candidates(name,z.read(name).decode('utf-8-sig')))
    with output.open('x',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['path','line','column','speaker','field','original','translation','status','note'])
        w.writeheader();w.writerows(rows)
    print('已整理待审核候选文本：',len(rows), '条；文件：',output)
    print('该清单需再对照实际画面和图片文字补查，不能单独证明完整覆盖。')

if __name__=='__main__': main()
