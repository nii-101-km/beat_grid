#!/usr/bin/env python3
"""Локальный анализ интервалов музыкальных долей. Аудиофайлы не изменяет."""
import argparse
import csv
import io
import json
import math
import os
from pathlib import Path
import secrets
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

os.environ.setdefault('NUMBA_CACHE_DIR', str(Path(os.environ.get('TMPDIR', '/tmp')) / 'beat-grid-numba'))

PAGE = r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Beat Grid</title><style>
body{font:16px system-ui;background:#131722;color:#edf0f8;max-width:980px;margin:35px auto;padding:0 18px}h1{margin-bottom:4px}p{color:#b7c1d4;line-height:1.5}section{background:#202738;border:1px solid #39445b;border-radius:12px;padding:20px;margin:18px 0}.form{display:flex;gap:14px;flex-wrap:wrap;align-items:end}label{display:flex;flex-direction:column;gap:7px}input,button,select{font:inherit;color:#edf0f8;background:#111827;border:1px solid #64728d;border-radius:6px;padding:9px}input[type=number]{width:140px}button{background:#3b64c6;border:0;cursor:pointer}button:disabled{opacity:.5}table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}th,td{text-align:right;padding:9px;border-bottom:1px solid #384257}th:first-child,td:first-child{text-align:left}tr.warn{background:#593e28}#error,#align-error{color:#ffb4a8;white-space:pre-wrap}#status{color:#a8c3ff}small{color:#aab8ce}
</style></head><body><label>Language / Язык<select id="lang"><option value="en">English</option><option value="ru">Русский</option></select></label><h1 data-i="title">🥁 Beat Grid</h1><p data-i="intro"></p><section><div class="form"><label><span data-i="file"></span><input type="file" id="file" accept="audio/*,.wav,.flac,.mp3,.ogg,.aiff,.aif"></label><label><span data-i="offset"></span><input type="number" id="offset" value="0" step="0.001" min="0"></label><label><span data-i="bpm"></span><input type="number" id="bpm" step="0.1" min="20" max="400"></label><label><span data-i="threshold"></span><input type="number" id="threshold" value="15" step="1" min="0"></label><button id="go" data-i="analyze"></button></div><p><small data-i="offsetHelp"></small></p><div id="status"></div><div id="error"></div></section><section><h2 data-i="alignTitle"></h2><p data-i="alignHelp"></p><div class="form"><label><span data-i="start"></span><input type="number" id="selstart" step="0.001" min="0" placeholder="200.9"></label><label><span data-i="end"></span><input type="number" id="selend" step="0.001" min="0" placeholder="202.1"></label><label><span data-i="tolerance"></span><input type="number" id="tolerance" value="15" step="1" min="0"></label><button id="align" data-i="calculate"></button></div><p><small data-i="method"></small></p><p id="alignment"></p><div id="align-controls" hidden><label><span data-i="shift"></span><input type="number" id="shift" step="0.1"></label><p><button id="render" data-i="createWav"></button></p><small data-i="renderHelp"></small></div><p id="align-error"></p></section><section id="results" hidden><h2 data-i="results"></h2><p id="summary"></p><p id="selection-status"></p><button id="download" data-i="download"></button><p><small data-i="caveat"></small></p><table><thead><tr><th>#</th><th data-i="beat"></th><th data-i="nextBeat"></th><th data-i="interval"></th><th data-i="medianDiff"></th><th data-i="selection"></th></tr></thead><tbody id="rows"></tbody></table></section><script>
const translations={en:{title:'🥁 Beat Grid',intro:'Estimated beat intervals before and after repainting. Analysis runs locally.',file:'Audio file',offset:'Fragment start in project, seconds',bpm:'Tempo in BPM (optional)',auto:'Auto',threshold:'Highlight deviation from median, ms',analyze:'Analyze',offsetHelp:'Example: if the export starts at 3:16, enter 196 seconds. Use 0 for a complete track. Audio is not modified.',alignTitle:'Align grids around a selection',alignHelp:'Enter the project-time boundaries or choose them using the table below.',start:'Selection start, seconds',end:'Selection end, seconds',tolerance:'Alignment tolerance, ms',calculate:'Calculate shift',method:'Analyze first. The shift uses the same beats and median interval as the table. Within the tolerance, a zero shift is suggested.',shift:'Shift right-hand audio, ms (− left, + right)',createWav:'Create WAV',renderHelp:'Downloads a new WAV. A positive shift inserts silence in the middle of the selection; a negative shift removes audio there. Repair the join when repainting. The original is unchanged.',results:'Results',selectHelp:'Choose the start and end using the table buttons.',download:'Download CSV',caveat:'Beats are estimates from the full mix, not exact drum hits. Check the result by ear. Tempo may be detected at half or double speed. Include several seconds of music on both sides.',beat:'Beat, s',nextBeat:'Next beat, s',interval:'Interval',medianDiff:'From median',selection:'Selection',chooseFile:'Choose an audio file.',working:'Analyzing… The first run may take longer.',analysisError:'Analysis failed.',done:'Done.',begin:'Start',finish:'End',beginTitle:'Start selection at this beat',finishTitle:'End selection at the next beat',changed:'Settings changed. Analyze again.',invalidRange:'The selection start must be before its end.',invalidTolerance:'Tolerance must be non-negative.',noAnchors:'At least one beat is needed on each side of the selection. Expand the audio or change the selection.',analyzeFirst:'Analyze the selected audio file first.',bothBounds:'Enter both selection boundaries.',outside:'The selection must be inside the audio file.',error:'Error',autoPlaceholder:'Auto',estimated:'Estimated tempo',median:'Median interval',beatsFound:'Beats found',anchor:'Anchor beats',intervals:'Intervals',actual:'Actual',expected:'Expected from median',deviation:'Deviation',proposed:'Suggested shift',within:' (within tolerance)',csv:'Number;Beat s;Next beat s;Interval ms;Deviation from median ms'},ru:{title:'🥁 Сетка ударов',intro:'Интервалы между оценёнными долями до и после репеинта. Анализ выполняется на вашем компьютере.',file:'Аудиофайл',offset:'Начало фрагмента в проекте, сек.',bpm:'Темп BPM (необязательно)',auto:'Авто',threshold:'Выделить отклонение от медианы, мс',analyze:'Анализировать',offsetHelp:'Пример: если экспорт начинается с 3:16, укажите 196 секунд. Оставьте 0 для полного трека. Аудио не изменяется.',alignTitle:'Свести сетки вокруг выделения',alignHelp:'Укажите границы по шкале проекта или выберите их кнопками в таблице ниже.',start:'Начало выделения, сек.',end:'Конец выделения, сек.',tolerance:'Допуск совпадения, мс',calculate:'Рассчитать сдвиг',method:'Сначала нажмите «Анализировать». Сдвиг считается по тем же долям и медиане, что показаны в таблице. В пределах допуска предлагается нулевой сдвиг.',shift:'Сдвиг правой части, мс (− влево, + вправо)',createWav:'Создать WAV',renderHelp:'Скачивается новый WAV. При сдвиге вправо внутри выделения добавляется тишина, при сдвиге влево удаляется участок. Стык предназначен для репеинта; исходник не изменяется.',results:'Результат',selectHelp:'Выберите начало и конец выделения кнопками в таблице.',download:'Скачать таблицу CSV',caveat:'Доли оцениваются по всему миксу, а не по отдельным ударам барабанов. Проверяйте на слух. Темп может определиться вдвое быстрее или медленнее. Оставляйте несколько секунд музыки с обеих сторон.',beat:'Доля, с',nextBeat:'Следующая доля, с',interval:'Интервал',medianDiff:'От медианы',selection:'Выделение',chooseFile:'Выберите аудиофайл.',working:'Анализирую… Первый запуск может занять больше времени.',analysisError:'Ошибка анализа.',done:'Готово.',begin:'Начало',finish:'Конец',beginTitle:'Начать выделение с этой доли',finishTitle:'Закончить выделение следующей долей',changed:'Параметры изменились. Выполните анализ заново.',invalidRange:'Начало должно быть раньше конца выделения.',invalidTolerance:'Допуск должен быть неотрицательным.',noAnchors:'Нужна хотя бы одна доля слева и одна справа от выделения. Расширьте аудиофрагмент или измените выделение.',analyzeFirst:'Сначала выполните анализ выбранного аудиофайла.',bothBounds:'Укажите обе границы выделения.',outside:'Выделение должно находиться внутри аудиофайла.',error:'Ошибка',autoPlaceholder:'Авто',estimated:'Оценка темпа',median:'Медианный интервал',beatsFound:'Найдено долей',anchor:'Опорные доли',intervals:'Интервалов',actual:'Фактически',expected:'По медиане',deviation:'Расхождение',proposed:'Предлагаемый сдвиг',within:' (в пределах допуска)',csv:'Номер;Доля с;Следующая доля с;Интервал мс;Отклонение от медианы мс'}};
let result=null,proposal=null,revision=0;const $=id=>document.getElementById(id);const t=key=>translations[$('lang').value][key]||key;const fmt=x=>x.toFixed(3);const signed=x=>`${x>=0?'+':''}${x.toFixed(1)}`;
function selectionStatus(){ $('selection-status').textContent=($('selstart').value||$('selend').value)?`${t('begin')}: ${$('selstart').value||'—'} s · ${t('finish')}: ${$('selend').value||'—'} s`:t('selectHelp')}
function summary(){if(result)$('summary').textContent=`${t('estimated')}: ${result.bpm.toFixed(1)} BPM · ${t('median')}: ${result.median_ms.toFixed(1)} ms · ${t('beatsFound')}: ${result.beats.length}`}
function draw(){if(!result)return;summary();$('rows').replaceChildren();result.intervals.forEach((x,i)=>{let tr=document.createElement('tr');if(Math.abs(x.ms-result.median_ms)>=result.threshold)tr.className='warn';[i+1,fmt(x.start),fmt(x.end),`${x.ms.toFixed(1)} ms`,`${signed(x.delta)} ms`].forEach(v=>{let td=document.createElement('td');td.textContent=v;tr.appendChild(td)});let td=document.createElement('td'),begin=document.createElement('button'),end=document.createElement('button');begin.textContent=t('begin');begin.title=t('beginTitle');begin.onclick=()=>setBoundary('selstart',x.start);end.textContent=t('finish');end.title=t('finishTitle');end.onclick=()=>setBoundary('selend',x.end);td.append(begin,' ',end);tr.appendChild(td);$('rows').appendChild(tr)})}
function showProposal(){if(!proposal)return;let j=proposal;$('alignment').textContent=`${t('anchor')}: ${fmt(j.left)} / ${fmt(j.right)} s · ${t('intervals')}: ${j.count} · ${t('actual')}: ${j.actual.toFixed(1)} ms · ${t('expected')}: ${j.expected.toFixed(1)} ms · ${t('deviation')}: ${signed(j.phase_ms)} ms · ${t('proposed')}: ${signed(j.shift_ms)} ms${j.shift_ms===0?t('within'):''}.`}
function setLanguage(){document.documentElement.lang=$('lang').value;document.title=$('lang').value==='ru'?'Сетка ударов':'Beat Grid';document.querySelectorAll('[data-i]').forEach(el=>el.textContent=t(el.dataset.i));$('bpm').placeholder=t('auto');selectionStatus();draw();showProposal();$('status').textContent='';$('error').textContent='';$('align-error').textContent=''}
function resetProposal(){proposal=null;$('align-controls').hidden=true;$('alignment').textContent=''}
function setBoundary(id,value){$(id).value=value.toFixed(6);resetProposal();selectionStatus()}
$('lang').onchange=setLanguage;
$('go').onclick=async()=>{resetProposal();result=null;let f=$('file').files[0];if(!f){$('error').textContent=t('chooseFile');return}let current=revision;$('error').textContent='';$('status').textContent=t('working');$('go').disabled=true;$('results').hidden=true;try{let r=await fetch('/analyze',{method:'POST',headers:{'Content-Type':'application/octet-stream','X-Beat-Token':'TOKEN','X-Lang':$('lang').value,'X-Offset':$('offset').value,'X-Bpm':$('bpm').value,'X-Threshold':$('threshold').value},body:f});let j=await r.json();if(!r.ok)throw Error(j.error||t('analysisError'));if(current!==revision)return;result=j;draw();$('results').hidden=false;$('status').textContent=t('done')}catch(e){$('error').textContent=e.message;$('status').textContent=''}finally{$('go').disabled=false}};
const ah=()=>({'Content-Type':'application/octet-stream','X-Beat-Token':'TOKEN','X-Lang':$('lang').value,'X-Offset':$('offset').value,'X-Bpm':$('bpm').value,'X-Start':$('selstart').value,'X-End':$('selend').value});
['file','offset','bpm'].forEach(id=>$(id).addEventListener('input',()=>{revision++;resetProposal();result=null;$('results').hidden=true;$('status').textContent=t('changed')}));['selstart','selend','tolerance'].forEach(id=>$(id).addEventListener('input',()=>{resetProposal();selectionStatus()}));
function calculateAlignment(beats,median,start,end,tolerance){if(!Number.isFinite(start)||!Number.isFinite(end)||start>=end)throw Error(t('invalidRange'));if(!Number.isFinite(tolerance)||tolerance<0)throw Error(t('invalidTolerance'));let left=-1,right=-1;for(let i=0;i<beats.length;i++){if(beats[i]<=start+1e-7)left=i;if(right<0&&beats[i]>=end-1e-7)right=i}if(left<0||right<0||right<=left)throw Error(t('noAnchors'));const count=right-left,actual=(beats[right]-beats[left])*1000,expected=count*median,phase=actual-expected;return {left:beats[left],right:beats[right],count,actual,expected,phase_ms:phase,shift_ms:Math.abs(phase)<=tolerance?0:-phase,tolerance}}
$('align').onclick=()=>{try{if(!result)throw Error(t('analyzeFirst'));if(!$('selstart').value||!$('selend').value)throw Error(t('bothBounds'));let start=Number($('selstart').value),end=Number($('selend').value);if(start<Number($('offset').value)||end>Number($('offset').value)+result.duration)throw Error(t('outside'));proposal=calculateAlignment(result.beats,result.median_ms,start,end,Number($('tolerance').value));$('shift').value=proposal.shift_ms.toFixed(1);showProposal();$('align-error').textContent='';$('align-controls').hidden=false}catch(e){resetProposal();$('align-error').textContent=e.message}};
$('render').onclick=async()=>{if(!proposal)return;let f=$('file').files[0];$('render').disabled=true;$('align-error').textContent='';try{let h=ah();h['X-Shift']=$('shift').value;let r=await fetch('/render',{method:'POST',headers:h,body:f});if(!r.ok){let j=await r.json();throw Error(j.error||t('error'))}let a=document.createElement('a');a.href=URL.createObjectURL(await r.blob());a.download=f.name.replace(/\.[^.]*$/,'')+'_grid_aligned.wav';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}catch(e){$('align-error').textContent=e.message}finally{$('render').disabled=false}};
$('download').onclick=()=>{if(!result)return;let csv='\ufeff'+t('csv')+'\n'+result.intervals.map((x,i)=>[i+1,fmt(x.start),fmt(x.end),x.ms.toFixed(1),x.delta.toFixed(1)].join(';')).join('\n');let a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));a.download='beat_intervals.csv';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)};
setLanguage();
</script></body></html>
'''


def analyze(data, offset=0.0, bpm=None, threshold=15.0):
    import numpy as np
    import soundfile as sf
    import librosa
    if not all(math.isfinite(v) and v >= 0 for v in (offset, threshold)):
        raise ValueError('Offset and threshold must be non-negative numbers.')
    if bpm is not None and (not math.isfinite(bpm) or not 20 <= bpm <= 400):
        raise ValueError('Tempo must be between 20 and 400 BPM.')
    try:
        audio, sr = sf.read(io.BytesIO(data), dtype='float32', always_2d=True)
    except Exception as exc:
        raise ValueError('Could not read audio. Try WAV or FLAC.') from exc
    if len(audio) / sr < 3:
        raise ValueError('The audio must be at least 3 seconds long.')
    if len(audio) / sr > 900:
        raise ValueError('The audio must be no longer than 15 minutes.')
    y = np.mean(audio, axis=1)
    if not np.isfinite(y).all() or np.max(np.abs(y)) < 1e-7:
        raise ValueError('The audio is silent or contains invalid values.')
    target_sr = 22050
    if sr != target_sr:
        y = librosa.resample(y, orig_sr=sr, target_sr=target_sr)
    hop = 110
    onset = librosa.onset.onset_strength(y=y, sr=target_sr, hop_length=hop)
    kwargs = {'onset_envelope': onset, 'sr': target_sr, 'hop_length': hop, 'trim': False, 'units': 'time'}
    if bpm is not None:
        kwargs['bpm'] = bpm
    tempo, times = librosa.beat.beat_track(**kwargs)
    times = np.asarray(times, dtype=float)
    if len(times) < 2:
        raise ValueError('Not enough beats found. Try a longer excerpt or set the BPM.')
    diffs = np.diff(times) * 1000
    median = float(np.median(diffs))
    beats = (times + offset).tolist()
    return {'bpm': float(np.asarray(tempo).reshape(-1)[0]), 'median_ms': median, 'threshold': threshold, 'duration': len(audio) / sr,
            'beats': beats, 'intervals': [{'start': beats[i], 'end': beats[i+1], 'ms': float(v), 'delta': float(v-median)} for i,v in enumerate(diffs)]}


def _read_audio(data):
    import soundfile as sf
    import numpy as np
    try:
        audio, sr = sf.read(io.BytesIO(data), dtype='float32', always_2d=True)
    except Exception as exc:
        raise ValueError('Could not read audio. Try WAV or FLAC.') from exc
    if not 3 <= len(audio) / sr <= 900 or not np.isfinite(audio).all():
        raise ValueError('Audio must be valid and between 3 seconds and 15 minutes long.')
    return audio, sr


def _validate_selection(audio, sr, offset, start, end):
    if not all(math.isfinite(v) for v in (offset, start, end)) or offset < 0:
        raise ValueError('Check the fragment offset and selection boundaries.')
    a, b = start - offset, end - offset
    if not 0 <= a < b <= len(audio) / sr:
        raise ValueError('The selection must lie within the file, and its start must be before its end.')
    return a, b


def render_alignment(data, offset, start, end, shift_ms):
    import numpy as np
    import soundfile as sf
    audio, sr = _read_audio(data)
    a,b = _validate_selection(audio,sr,offset,start,end)
    if not math.isfinite(shift_ms): raise ValueError('The shift must be a finite number.')
    n=round(shift_ms*sr/1000)
    first,last=round(a*sr),round(b*sr)
    if abs(n) > last-first:
        raise ValueError('The shift exceeds the selection length.')
    mid=(first+last)//2
    if n > 0:
        output=np.concatenate((audio[:mid],np.zeros((n,audio.shape[1]),dtype=audio.dtype),audio[mid:]))
    elif n < 0:
        count=-n
        cut=max(first,min(mid-count//2,last-count))
        output=np.concatenate((audio[:cut],audio[cut+count:]))
    else:
        output=audio
    buf=io.BytesIO()
    sf.write(buf,output,sr,format='WAV',subtype='FLOAT')
    return buf.getvalue()


ERRORS_RU = {'Offset and threshold must be non-negative numbers.': 'Смещение и порог должны быть неотрицательными числами.', 'Tempo must be between 20 and 400 BPM.': 'Темп должен быть в диапазоне 20–400 BPM.', 'Could not read audio. Try WAV or FLAC.': 'Не удалось прочитать аудио. Попробуйте WAV или FLAC.', 'The audio must be at least 3 seconds long.': 'Фрагмент слишком короткий: нужно хотя бы 3 секунды.', 'The audio must be no longer than 15 minutes.': 'Для анализа выберите фрагмент не длиннее 15 минут.', 'The audio is silent or contains invalid values.': 'Аудио содержит тишину или некорректные значения.', 'Not enough beats found. Try a longer excerpt or set the BPM.': 'Не удалось найти достаточно долей. Попробуйте более длинный фрагмент или задайте темп.', 'Audio must be valid and between 3 seconds and 15 minutes long.': 'Нужен корректный аудиофайл длительностью от 3 секунд до 15 минут.', 'Check the fragment offset and selection boundaries.': 'Проверьте начало фрагмента и границы выделения.', 'The selection must lie within the file, and its start must be before its end.': 'Выделение должно целиком находиться внутри файла; начало должно быть раньше конца.', 'The shift must be a finite number.': 'Сдвиг должен быть конечным числом.', 'The shift exceeds the selection length.': 'Сдвиг превышает длину выделения.', 'The file size must be between 1 byte and 256 MB.': 'Размер файла должен быть не более 256 МБ.'}

def main():
    parser = argparse.ArgumentParser(description='Analyze beat intervals in audio locally')
    parser.add_argument('file', nargs='?', help='audio file to analyze in the terminal')
    parser.add_argument('--offset', type=float, default=0, help='fragment start in project, seconds')
    parser.add_argument('--bpm', type=float, help='optional BPM hint')
    parser.add_argument('--port', type=int, default=0, help='local interface port (default: auto)')
    args = parser.parse_args()
    if args.file:
        try:
            result = analyze(Path(args.file).read_bytes(), args.offset, args.bpm)
        except Exception as exc:
            print('Error:', exc, file=sys.stderr); return 1
        def fmt(t):
            return f'{t:.3f}'
        print(f"Tempo: {result['bpm']:.1f} BPM; median interval: {result['median_ms']:.1f} ms")
        print('Beat, s          Next beat, s     Interval    Deviation')
        for x in result['intervals']:
            print(f"{fmt(x['start']):<16} {fmt(x['end']):<16} {x['ms']:7.1f} ms  {x['delta']:+7.1f} ms")
        return 0
    token = secrets.token_urlsafe(24)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def respond(self, status, content, kind):
            self.send_response(status); self.send_header('Content-Type', kind); self.send_header('Content-Length', str(len(content))); self.send_header('X-Content-Type-Options','nosniff'); self.end_headers(); self.wfile.write(content)
        def do_GET(self):
            if self.path != '/': self.respond(404,b'Not found','text/plain'); return
            self.respond(200, PAGE.replace('TOKEN',token).encode(), 'text/html; charset=utf-8')
        def do_POST(self):
            if self.path not in ('/analyze', '/render') or self.headers.get('X-Beat-Token') != token:
                self.respond(403,b'Forbidden','text/plain'); return
            try:
                n = int(self.headers.get('Content-Length','0'))
                if not 0 < n <= 256*1024*1024: raise ValueError('The file size must be between 1 byte and 256 MB.')
                offset = float(self.headers.get('X-Offset') or 0)
                threshold = float(self.headers.get('X-Threshold') or 0)
                bpm = float(self.headers['X-Bpm']) if self.headers.get('X-Bpm') else None
                data = self.rfile.read(n)
                if self.path == '/analyze':
                    obj = analyze(data, offset, bpm, threshold)
                else:
                    start = float(self.headers.get('X-Start','nan'))
                    end = float(self.headers.get('X-End','nan'))
                    wav = render_alignment(data, offset, start, end, float(self.headers.get('X-Shift','nan')))
                    self.respond(200, wav, 'audio/wav'); return
                self.respond(200,json.dumps(obj,ensure_ascii=False).encode(),'application/json; charset=utf-8')
            except Exception as exc:
                self.respond(400,json.dumps({'error': ERRORS_RU.get(str(exc), str(exc)) if self.headers.get('X-Lang') == 'ru' else str(exc)},ensure_ascii=False).encode(),'application/json; charset=utf-8')
    try:
        server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    except OSError as exc:
        print(f'Could not start the local interface: {exc}', file=sys.stderr)
        print('Try the command line: ./start.sh audio.wav --offset 196', file=sys.stderr)
        return 1
    url = f'http://127.0.0.1:{server.server_port}/'
    print(f'Open {url}\nPress Ctrl+C to stop',flush=True)
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try: server.serve_forever()
    except KeyboardInterrupt: print('\nStopped.')
    finally: server.server_close()
    return 0

if __name__ == '__main__':
    sys.exit(main())
