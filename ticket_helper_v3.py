import json, os, threading, webbrowser, uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HOST, PORT = "127.0.0.1", 8765
DATA = os.path.join(os.path.expanduser("~"), "ticket_helper_tasks.json")
PAGE = r"""<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>演唱会抢票助手 V3</title>
<style>
body{font:16px -apple-system,BlinkMacSystemFont,sans-serif;background:#f2f5fa;color:#182337;margin:0;padding:22px}.wrap{max-width:850px;margin:auto}header{background:#204e86;color:white;padding:22px;border-radius:16px}main{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:14px}.card{background:white;padding:18px;border:1px solid #dde5ef;border-radius:14px}h1{margin:0 0 8px}h2{font-size:18px;margin-top:0}label{display:block;margin:12px 0 5px;font-weight:600}input,select{width:100%;box-sizing:border-box;padding:11px;border:1px solid #c6d1df;border-radius:8px;font:inherit}button{padding:10px 13px;border:0;border-radius:8px;background:#245eaa;color:white;font:inherit;cursor:pointer;margin:8px 5px 0 0}.secondary{background:#e7edf6;color:#1d3d69}.task{border:1px solid #dce4ef;border-radius:9px;padding:10px;margin:8px 0}.muted{color:#68778b;font-size:13px}#count{font-size:30px;font-weight:bold;color:#245eaa;margin:12px 0}.full{grid-column:1/-1}.check{display:flex;align-items:center;gap:8px;font-weight:400}.check input{width:auto}@media(max-width:650px){main{grid-template-columns:1fr}.full{grid-column:auto}body{padding:10px}}
</style><div class="wrap"><header><h1>🎫 演唱会抢票助手 V3</h1><div>浏览器界面 · 开售倒计时 · 购票准备提醒 · 官方页面跳转</div></header><main>
<section class="card"><h2>添加演出任务</h2><form id="form"><label>演出名称</label><input id="event" required placeholder="例如：某某巡回演唱会"><label>购票平台</label><select id="platform"><option>大麦</option><option>猫眼</option></select><label>开售时间</label><input id="sale" type="datetime-local" required><label>官方购票网址（选填）</label><input id="url" type="url" placeholder="没有网址就留空"><button>保存并开始提醒</button><button type="reset" class="secondary">清空表单</button></form></section>
<section class="card"><h2>当前倒计时</h2><div id="current">尚未选择任务</div><div id="count">--:--:--</div><p id="status">添加任务后，请保持此页面打开。</p><button id="open">打开官方页面 / 手机提示</button><button id="cancel" class="secondary">取消倒计时</button></section>
<section class="card"><h2>已保存任务</h2><div id="tasks">正在读取……</div></section><section class="card"><h2>购票准备清单</h2><label class="check"><input type="checkbox">已登录官方 App</label><label class="check"><input type="checkbox">已核对演出日期和场次</label><label class="check"><input type="checkbox">已确认观演人信息</label><label class="check"><input type="checkbox">已确认支付方式</label><label class="check"><input type="checkbox">已检查网络和预算</label><p class="muted">仅提供提醒与官方页面跳转，不自动下单、排队或绕过平台验证。</p></section></main></div>
<script>
let tasks=[],active=null,fired={};const $=x=>document.getElementById(x);const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function api(p,d){let r=await fetch(p,{method:d?'POST':'GET',headers:d?{'Content-Type':'application/json'}:{},body:d?JSON.stringify(d):undefined});return r.json()}
function chosen(){return tasks.find(t=>t.id===active)}
function render(){let b=$('tasks');b.innerHTML='';if(!tasks.length){b.textContent='暂无任务';return}tasks.forEach(t=>{let d=document.createElement('div');d.className='task';d.innerHTML='<b>'+esc(t.event)+' · '+esc(t.platform)+'</b><div class="muted">开售：'+esc(t.sale_time.replace('T',' '))+'</div><button class="secondary" data-s="'+t.id+'">设为当前</button><button data-d="'+t.id+'">删除</button>';b.append(d)});b.querySelectorAll('[data-s]').forEach(x=>x.onclick=()=>{active=x.dataset.s;update()});b.querySelectorAll('[data-d]').forEach(x=>x.onclick=async()=>{await api('/delete',{id:x.dataset.d});tasks=tasks.filter(t=>t.id!==x.dataset.d);if(active===x.dataset.d)active=null;render();update()})}
function update(){let t=chosen();$('current').textContent=t?t.event+' · '+t.platform:'尚未选择任务';if(!t)$('count').textContent='--:--:--'}
$('form').onsubmit=async e=>{e.preventDefault();let t={event:$('event').value.trim(),platform:$('platform').value,sale_time:$('sale').value,url:$('url').value.trim()};if(new Date(t.sale_time)<=new Date()){alert('开售时间必须晚于现在');return}if(t.url&&!t.url.startsWith('https://')){alert('请输入 HTTPS 官方网址，或留空');return}let r=await api('/add',t);if(!r.ok){alert(r.error);return}tasks=r.tasks;active=r.id;fired={};render();update();$('status').textContent='任务已保存，请保持页面打开。'};
$('open').onclick=()=>{let t=chosen();if(!t){alert('请先添加或选择任务');return}if(t.url)window.open(t.url,'_blank','noopener');else alert('请在手机上打开'+t.platform+' App，搜索：'+t.event+'，并核对场次与票价。')};
$('cancel').onclick=()=>{active=null;update();$('status').textContent='倒计时已取消，任务仍然保留。'};
async function init(){try{let r=await api('/tasks');tasks=r.tasks||[];if(tasks.length)active=tasks[0].id;render();update()}catch(e){$('status').textContent='本地程序连接失败，请重新运行 Python。'}}
function tick(){let t=chosen();if(t){let n=Math.floor((new Date(t.sale_time)-new Date())/1000);if(n>0){$('count').textContent=[Math.floor(n/3600),Math.floor(n%3600/60),n%60].map(x=>String(x).padStart(2,'0')).join(':');for(let [limit,key,msg] of [[300,'5','约 5 分钟后开售，请检查登录状态和购票信息。'],[60,'1','约 1 分钟后开售，请准备打开官方 App。']])if(n<=limit&&!fired[t.id+key]){fired[t.id+key]=1;$('status').textContent=msg;alert(msg)}}else{$('count').textContent='00:00:00';if(!fired[t.id+'sale']){fired[t.id+'sale']=1;$('status').textContent='开售时间到了！请在官方平台自行购票。';alert($('status').textContent);if(t.url)window.open(t.url,'_blank','noopener');else alert('请打开'+t.platform+' App，搜索：'+t.event)}}}setTimeout(tick,1000)}init();tick();
</script></html>"""

def load():
    try:
        with open(DATA, encoding="utf-8") as f: x=json.load(f)
        return x if isinstance(x,list) else []
    except (OSError, ValueError): return []
def save(x):
    with open(DATA,"w",encoding="utf-8") as f: json.dump(x,f,ensure_ascii=False,indent=2)
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def sendj(self,x,status=200):
        b=json.dumps(x,ensure_ascii=False).encode();self.send_response(status);self.send_header("Content-Type","application/json; charset=utf-8");self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
    def do_GET(self):
        p=urlparse(self.path).path
        if p=="/":
            b=PAGE.encode();self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8");self.send_header("Content-Length",str(len(b)));self.end_headers();self.wfile.write(b)
        elif p=="/tasks": self.sendj({"tasks":load()})
        else:self.send_error(404)
    def do_POST(self):
        try:d=json.loads(self.rfile.read(int(self.headers.get("Content-Length","0"))))
        except ValueError:self.sendj({"ok":False,"error":"请求数据无效"},400);return
        x=load();p=urlparse(self.path).path
        if p=="/add":
            try:s=datetime.strptime(d["sale_time"],"%Y-%m-%dT%H:%M")
            except (ValueError,KeyError,TypeError):self.sendj({"ok":False,"error":"开售时间无效"},400);return
            if not d.get("event","").strip() or d.get("platform") not in ("大麦","猫眼") or s<=datetime.now() or (d.get("url") and not d["url"].startswith("https://")):
                self.sendj({"ok":False,"error":"请检查演出名称、平台、未来开售时间和 HTTPS 网址"},400);return
            t={"id":uuid.uuid4().hex,"event":d["event"].strip(),"platform":d["platform"],"sale_time":d["sale_time"],"url":d.get("url","").strip()};x.append(t)
            try:save(x)
            except OSError as e:self.sendj({"ok":False,"error":str(e)},500);return
            self.sendj({"ok":True,"id":t["id"],"tasks":x})
        elif p=="/delete":
            x=[t for t in x if t.get("id")!=d.get("id")]
            try:save(x)
            except OSError as e:self.sendj({"ok":False,"error":str(e)},500);return
            self.sendj({"ok":True,"tasks":x})
        else:self.send_error(404)
def main():
    try:s=ThreadingHTTPServer((HOST,PORT),Handler)
    except OSError:print(f"端口 {PORT} 被占用。请关闭旧版本后重试。");return
    url=f"http://{HOST}:{PORT}";print("抢票助手已启动："+url);print("请保持此终端运行。按 Control+C 退出。")
    threading.Timer(1,lambda:webbrowser.open(url)).start()
    try:s.serve_forever()
    except KeyboardInterrupt:print("程序已停止。")
    finally:s.server_close()
if __name__=="__main__":main()
