import os
import json
import shutil
import sqlite3
import csv
import webbrowser
import threading
import sys
import socket
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify


app = Flask(__name__)
app.config['SECRET_KEY'] = 'armix-webstudio-2026'


PROJECTS_DIR = os.path.join(os.path.expanduser('~'), 'ARMIX_WebStudio_Projects')
if not os.path.exists(PROJECTS_DIR):
    os.makedirs(PROJECTS_DIR)


HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="ru">
<head>
   <meta charset="UTF-8">
   <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
   <title>ARMIX WebStudio Pro</title>
   <style>
       * { margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
       :root {
           --bg-dark: #0a0a0f;
           --bg-sidebar: rgba(20, 20, 35, 0.95);
           --bg-editor: rgba(30, 30, 46, 0.9);
           --accent: #007acc;
           --accent-hover: #0098ff;
           --text: #e4e4e7;
           --text-dim: #888;
           --border: rgba(0, 122, 204, 0.3);
           --success: #6a9955;
           --error: #f48771;
           --warning: #ffa500;
       }
       body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif; background: var(--bg-dark); height: 100vh; overflow: hidden; color: var(--text); }
       .app { display: flex; flex-direction: column; height: 100vh; background: linear-gradient(135deg, #0a0a0f 0%, #0f0f1a 100%); }
       @media (max-width: 768px) {
           .sidebar { width: 100% !important; position: fixed; z-index: 200; height: 100%; transform: translateX(-100%); transition: transform 0.3s; }
           .sidebar.open { transform: translateX(0); }
           .right-panel { width: 100% !important; position: fixed; bottom: 0; z-index: 150; height: 50%; transform: translateY(100%); transition: transform 0.3s; }
           .right-panel.open { transform: translateY(0); }
           .toolbar { overflow-x: auto; white-space: nowrap; flex-wrap: nowrap; }
           .toolbar .btn { flex-shrink: 0; }
           .mobile-menu-btn { display: block !important; }
       }
       .mobile-menu-btn { display: none; position: fixed; bottom: 20px; right: 20px; width: 50px; height: 50px; border-radius: 50%; background: var(--accent); color: white; border: none; font-size: 24px; cursor: pointer; z-index: 300; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
       .toolbar { background: rgba(30, 30, 46, 0.95); backdrop-filter: blur(12px); border-bottom: 1px solid var(--border); padding: 8px 16px; display: flex; gap: 6px; flex-wrap: wrap; z-index: 100; overflow-x: auto; }
       .btn { background: linear-gradient(135deg, #2a2a3a 0%, #1e1e2e 100%); border: 1px solid var(--border); color: var(--text); padding: 6px 12px; border-radius: 8px; cursor: pointer; font-size: 12px; font-weight: 500; transition: all 0.2s; display: inline-flex; align-items: center; gap: 5px; white-space: nowrap; }
       .btn:hover { background: #3a3a4a; border-color: var(--accent); transform: translateY(-1px); }
       .btn-primary { background: linear-gradient(135deg, #007acc 0%, #005a9e 100%); border-color: #0098ff; }
       .btn-success { background: linear-gradient(135deg, #28a745 0%, #1e7e34 100%); }
       .btn-danger { background: linear-gradient(135deg, #dc3545 0%, #b02a37 100%); }
       .main { display: flex; flex: 1; overflow: hidden; gap: 1px; background: rgba(0,0,0,0.2); position: relative; }
       .sidebar { width: 280px; background: var(--bg-sidebar); backdrop-filter: blur(8px); display: flex; flex-direction: column; overflow: hidden; border-right: 1px solid var(--border); }
       .sidebar-header { padding: 10px 12px; background: rgba(0, 122, 204, 0.15); border-bottom: 1px solid var(--border); font-weight: 600; font-size: 11px; text-transform: uppercase; display: flex; justify-content: space-between; align-items: center; }
       .project-list, .file-tree { flex: 1; overflow-y: auto; padding: 6px; }
       .project-item, .file-tree-item { background: rgba(40, 40, 55, 0.5); border-radius: 8px; padding: 8px 10px; margin-bottom: 5px; cursor: pointer; transition: all 0.15s; border: 1px solid transparent; font-size: 12px; }
       .project-item:hover, .file-tree-item:hover { background: rgba(0, 122, 204, 0.2); border-color: var(--accent); transform: translateX(2px); }
       .project-name { font-weight: 600; font-size: 12px; }
       .project-date { font-size: 9px; color: var(--text-dim); }
       .editor-panel { flex: 1; display: flex; flex-direction: column; background: var(--bg-editor); overflow: hidden; }
       .tabs { background: rgba(0, 0, 0, 0.3); padding: 5px 10px; display: flex; gap: 3px; border-bottom: 1px solid var(--border); overflow-x: auto; }
       .tab { background: rgba(40, 40, 55, 0.8); padding: 5px 12px; border-radius: 6px 6px 0 0; cursor: pointer; font-size: 11px; display: flex; align-items: center; gap: 6px; white-space: nowrap; }
       .tab.active { background: var(--accent); color: white; }
       .tab-close { opacity: 0.6; cursor: pointer; font-size: 11px; padding: 0 3px; }
       .tab-close:hover { opacity: 1; }
       .editor-wrapper { flex: 1; display: flex; overflow: hidden; }
       .line-numbers { background: rgba(0, 0, 0, 0.3); padding: 12px 8px; font-family: 'Consolas', monospace; font-size: 12px; line-height: 1.5; text-align: right; color: #6a6a7a; user-select: none; overflow-y: hidden; width: 50px; white-space: pre; }
       .code-editor { flex: 1; background: transparent; border: none; padding: 12px; font-family: 'Consolas', monospace; font-size: 12px; line-height: 1.5; color: var(--text); resize: none; outline: none; background: rgba(0, 0, 0, 0.2); }
       .right-panel { width: 400px; background: var(--bg-sidebar); backdrop-filter: blur(8px); display: flex; flex-direction: column; border-left: 1px solid var(--border); }
       .preview-container { flex: 2; min-height: 150px; display: flex; flex-direction: column; overflow: hidden; }
       .resize-handle { height: 6px; background: var(--border); cursor: ns-resize; margin: 2px 8px; border-radius: 3px; }
       .resize-handle:hover { background: var(--accent); }
       .preview-frame { flex: 1; background: white; margin: 6px; border-radius: 10px; overflow: auto; }
       .preview-frame iframe { width: 100%; height: 100%; border: none; background: white; }
       .console { flex: 1; background: rgba(0, 0, 0, 0.5); margin: 6px; border-radius: 10px; padding: 8px; overflow-y: auto; font-family: 'Consolas', monospace; font-size: 10px; }
       .console-line { padding: 3px 0; border-bottom: 1px solid rgba(255,255,255,0.05); word-break: break-all; }
       .console-line.error { color: var(--error); }
       .console-line.success { color: var(--success); }
       .console-line.info { color: #569cd6; }
       .status-bar { background: rgba(0, 0, 0, 0.5); padding: 3px 12px; font-size: 10px; display: flex; justify-content: space-between; border-top: 1px solid var(--border); }
       .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); backdrop-filter: blur(12px); z-index: 1000; justify-content: center; align-items: center; }
       .modal-content { background: rgba(30,30,46,0.98); border-radius: 20px; padding: 20px; width: 90%; max-width: 450px; border: 1px solid var(--accent); }
       .modal-input { width: 100%; padding: 10px; margin: 12px 0; background: rgba(0,0,0,0.5); border: 1px solid var(--accent); border-radius: 10px; color: white; font-size: 14px; }
       .context-menu { position: fixed; background: #2d2d2d; border: 1px solid var(--accent); border-radius: 8px; padding: 4px 0; z-index: 2000; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
       .context-menu-item { padding: 6px 20px; cursor: pointer; font-size: 12px; }
       .context-menu-item:hover { background: var(--accent); }
       .folder-icon { color: #ffa500; }
       .file-icon { color: #4ec9b0; }
       .tree-indent { margin-left: 20px; }
       ::-webkit-scrollbar { width: 5px; height: 5px; }
       ::-webkit-scrollbar-track { background: rgba(0,0,0,0.3); }
       ::-webkit-scrollbar-thumb { background: var(--accent); border-radius: 3px; }
   </style>
</head>
<body>
   <button class="mobile-menu-btn" onclick="toggleMobileSidebar()">☰</button>
   <div class="app">
       <div class="toolbar" id="toolbar">
           <button class="btn" onclick="showNewProjectModal()">📁 Новый</button>
           <button class="btn" onclick="openProjectDialog()">📂 Открыть</button>
           <button class="btn btn-primary" onclick="saveFile()">💾 Сохранить</button>
           <button class="btn btn-success" onclick="runInBrowser()">▶ Запуск</button>
           <button class="btn" onclick="openInNewTab()">🪟 Вкладка</button>
           <button class="btn" onclick="showSearchReplace()">🔍 Поиск</button>
           <button class="btn" onclick="formatCode()">✨ Формат</button>
           <button class="btn" onclick="showSnippets()">📋 Сниппеты</button>
           <button class="btn" onclick="showDatabaseModal()">🗄️ SQL</button>
           <button class="btn" onclick="clearConsole()">🗑️ Очистить</button>
           <button class="btn" onclick="toggleFullscreenPreview()">🖥️ Full</button>
           <button class="btn" onclick="toggleDeviceMode()">📱 Моб</button>
       </div>
       <div class="main">
           <div class="sidebar" id="sidebar">
               <div class="sidebar-header"><span>📁 ПРОЕКТЫ</span><button class="btn" style="padding:2px 6px;font-size:10px;" onclick="loadProjects()">🔄</button></div>
               <div class="project-list" id="projectList"></div>
               <div class="sidebar-header"><span>📂 ФАЙЛЫ</span><div style="display:flex;gap:3px;"><button class="btn" style="padding:2px 6px;font-size:10px;" onclick="newFolder()">📁</button><button class="btn" style="padding:2px 6px;font-size:10px;" onclick="newFile()">📄</button><button class="btn" style="padding:2px 6px;font-size:10px;" onclick="expandAll()">⬇️</button><button class="btn" style="padding:2px 6px;font-size:10px;" onclick="collapseAll()">⬆️</button></div></div>
               <div class="file-tree" id="fileTree"></div>
           </div>
           <div class="editor-panel">
               <div class="tabs" id="tabs"></div>
               <div class="editor-wrapper">
                   <div class="line-numbers" id="lineNumbers"></div>
                   <textarea class="code-editor" id="codeEditor" onkeyup="updateLineNumbers()" onscroll="syncScroll()" onkeydown="handleKeydown(event)" spellcheck="false"></textarea>
               </div>
           </div>
           <div class="right-panel" id="rightPanel">
               <div class="preview-container" id="previewContainer">
                   <div class="resize-handle" id="resizeHandle" onmousedown="initResize(event)"></div>
                   <div class="preview-frame"><iframe id="previewIframe" srcdoc="<html><body style='background:#1e1e1e;color:white;display:flex;justify-content:center;align-items:center;height:100vh;'>✨ Предпросмотр</body></html>"></iframe></div>
               </div>
               <div class="console" id="console"><div class="console-line info">> ARMIX WebStudio Pro v9.0 готов</div></div>
           </div>
       </div>
       <div class="status-bar"><span id="statusText">✅ Готов</span><span id="cursorPos">Стр:1 Кол:1</span></div>
   </div>
   <div class="modal" id="newProjectModal"><div class="modal-content"><h3>✨ Новый проект</h3><input class="modal-input" id="projectNameInput" placeholder="Название"><div style="display:flex;gap:10px;justify-content:flex-end;"><button class="btn" onclick="closeModal('newProjectModal')">Отмена</button><button class="btn btn-primary" onclick="createProject()">Создать</button></div></div></div>
   <div class="modal" id="searchModal"><div class="modal-content"><h3>🔍 Поиск и замена</h3><input class="modal-input" id="searchInput" placeholder="Найти..."><input class="modal-input" id="replaceInput" placeholder="Заменить на..."><div style="display:flex;gap:8px;flex-wrap:wrap;"><button class="btn" onclick="findNext()">Найти</button><button class="btn" onclick="replaceNext()">Заменить</button><button class="btn btn-primary" onclick="replaceAll()">Заменить всё</button><button class="btn" onclick="closeModal('searchModal')">Закрыть</button></div></div></div>
   <div class="modal" id="snippetsModal"><div class="modal-content"><h3>📋 Сниппеты</h3><div id="snippetsList" style="max-height:300px;overflow-y:auto;"></div><button class="btn" style="margin-top:12px;" onclick="closeModal('snippetsModal')">Закрыть</button></div></div>
   <div class="modal" id="databaseModal"><div class="modal-content"><h3>🗄️ SQLite</h3><input class="modal-input" id="dbNameInput" placeholder="Имя БД"><textarea class="modal-input" id="sqlQueryInput" rows="4" placeholder="SELECT * FROM sqlite_master;">SELECT * FROM sqlite_master WHERE type='table';</textarea><div style="display:flex;gap:8px;"><button class="btn" onclick="closeModal('databaseModal')">Закрыть</button><button class="btn btn-primary" onclick="executeSQL()">Выполнить</button></div><div id="sqlResult" style="margin-top:12px;max-height:200px;overflow:auto;background:rgba(0,0,0,0.3);border-radius:8px;padding:8px;font-size:11px;"></div></div></div>
   <div class="modal" id="renameModal"><div class="modal-content"><h3>✏️ Переименовать</h3><input class="modal-input" id="renameInput" placeholder="Новое имя"><div style="display:flex;gap:10px;"><button class="btn" onclick="closeModal('renameModal')">Отмена</button><button class="btn btn-primary" onclick="confirmRename()">OK</button></div></div></div>
   <div id="contextMenu" class="context-menu" style="display:none;"></div>
   <script>
       let currentProject = null, activeTab = null, files = {}, contextMenuItem = null, previewHeight = 300, deviceMode = false;
       function addConsole(text, type='info') {
           const div = document.getElementById('console');
           const line = document.createElement('div');
           line.className = `console-line ${type}`;
           line.innerHTML = `> ${new Date().toLocaleTimeString()} - ${text}`;
           div.appendChild(line);
           div.scrollTop = div.scrollHeight;
           while(div.children.length > 200) div.removeChild(div.children[0]);
       }
       function updateLineNumbers() {
           const editor = document.getElementById('codeEditor');
           const lines = editor.value.split('\\n');
           let nums = '';
           for(let i=1; i<=lines.length; i++) nums += i + '\\n';
           document.getElementById('lineNumbers').innerHTML = nums;
           const pos = editor.selectionStart;
           const text = editor.value.substring(0, pos);
           document.getElementById('cursorPos').innerHTML = `Стр:${text.split('\\n').length} Кол:${text.length - text.lastIndexOf('\\n') - 1}`;
       }
       function syncScroll() { document.getElementById('lineNumbers').scrollTop = document.getElementById('codeEditor').scrollTop; }
       function initResize(e) {
           const startY = e.clientY, container = document.getElementById('previewContainer'), startH = container.offsetHeight;
           document.onmousemove = (me) => { let nh = startH + (me.clientY - startY); if(nh>80 && nh<window.innerHeight-150) container.style.height = nh+'px'; };
           document.onmouseup = () => { document.onmousemove = null; };
       }
       function toggleFullscreenPreview() { document.getElementById('previewIframe').requestFullscreen?.(); addConsole('🖥️ Полноэкранный режим','info'); }
       function toggleDeviceMode() {
           deviceMode = !deviceMode;
           const f = document.getElementById('previewIframe');
           if(deviceMode) { f.style.width='375px'; f.style.height='667px'; f.style.margin='0 auto'; addConsole('📱 Мобильный режим','info'); }
           else { f.style.width='100%'; f.style.height='100%'; f.style.margin='0'; addConsole('💻 Десктоп режим','info'); }
       }
       function toggleMobileSidebar() { document.getElementById('sidebar').classList.toggle('open'); }
       function closeModal(id) { document.getElementById(id).style.display = 'none'; }
       function showSearchReplace() { document.getElementById('searchModal').style.display = 'flex'; }
       function findNext() {
           const s = document.getElementById('searchInput').value;
           if(!s) return;
           const e = document.getElementById('codeEditor');
           const p = e.selectionEnd;
           const idx = e.value.indexOf(s, p);
           if(idx!==-1) { e.selectionStart=idx; e.selectionEnd=idx+s.length; e.focus(); }
           else addConsole('Больше не найдено','warning');
       }
       function replaceNext() {
           const s = document.getElementById('searchInput').value, r = document.getElementById('replaceInput').value;
           if(!s) return;
           const e = document.getElementById('codeEditor');
           const start=e.selectionStart, end=e.selectionEnd;
           if(e.value.substring(start,end)===s) {
               e.value = e.value.substring(0,start)+r+e.value.substring(end);
               e.selectionStart = start+r.length;
               updateLineNumbers();
           }
           findNext();
       }
       function replaceAll() {
           const s = document.getElementById('searchInput').value, r = document.getElementById('replaceInput').value;
           if(!s) return;
           const e = document.getElementById('codeEditor');
           e.value = e.value.split(s).join(r);
           updateLineNumbers();
           addConsole(`✅ Заменено всё: ${s} → ${r}`,'success');
       }
       function showSnippets() {
           const snippets = {'HTML5':'<!DOCTYPE html>\\n<html>\\n<head>\\n    <meta charset=\"UTF-8\">\\n    <title>Document</title>\\n</head>\\n<body>\\n    \\n</body>\\n</html>','CSS Reset':'*{margin:0;padding:0;box-sizing:border-box;}','Flex Center':'.container{display:flex;justify-content:center;align-items:center;min-height:100vh;}','Fetch JS':'fetch(\"/api/data\")\\n    .then(res=>res.json())\\n    .then(data=>console.log(data))\\n    .catch(err=>console.error(err));'};
           const cont = document.getElementById('snippetsList');
           cont.innerHTML = '';
           Object.entries(snippets).forEach(([n,c]) => {
               const d = document.createElement('div');
               d.className = 'context-menu-item';
               d.innerHTML = n;
               d.onclick = () => {
                   const e = document.getElementById('codeEditor');
                   const p = e.selectionStart;
                   e.value = e.value.substring(0,p) + c + e.value.substring(p);
                   updateLineNumbers();
                   closeModal('snippetsModal');
                   addConsole(`📋 Вставлен сниппет: ${n}`,'success');
               };
               cont.appendChild(d);
           });
           document.getElementById('snippetsModal').style.display = 'flex';
       }
       function handleKeydown(e) {
           if(e.ctrlKey && e.key==='s') { e.preventDefault(); saveFile(); }
           else if(e.ctrlKey && e.key==='o') { e.preventDefault(); openProjectDialog(); }
           else if(e.ctrlKey && e.key==='n') { e.preventDefault(); showNewProjectModal(); }
           else if(e.ctrlKey && e.key==='f') { e.preventDefault(); showSearchReplace(); }
           else if(e.key==='F5') { e.preventDefault(); runInBrowser(); }
           else if(e.key==='Tab') {
               e.preventDefault();
               const ed = document.getElementById('codeEditor');
               const s = ed.selectionStart;
               ed.value = ed.value.substring(0,s) + '    ' + ed.value.substring(s);
               ed.selectionStart = ed.selectionEnd = s+4;
               updateLineNumbers();
           }
       }
       function showNewProjectModal() { document.getElementById('newProjectModal').style.display = 'flex'; }
       function createProject() {
           const name = document.getElementById('projectNameInput').value;
           if(!name) return addConsole('Введите имя проекта','error');
           fetch('/api/create_project',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:name})})
               .then(()=>{ addConsole(`✅ Создан: ${name}`,'success'); closeModal('newProjectModal'); loadProjects(); });
       }
       function openProjectDialog() {
           const inp = document.createElement('input');
           inp.type = 'file';
           inp.webkitdirectory = true;
           inp.onchange = (e) => {
               const fls = Array.from(e.target.files);
               if(!fls.length) return;
               const pn = fls[0].webkitRelativePath.split('/')[0];
               const fd = new FormData();
               fd.append('name', pn);
               fls.forEach(f => fd.append('files', f));
               fetch('/api/import_project',{method:'POST',body:fd}).then(()=>{ addConsole(`📁 Импортирован: ${pn}`,'success'); loadProjects(); });
           };
           inp.click();
       }
       function loadProjects() {
           fetch('/api/get_projects').then(r=>r.json()).then(projs => {
               const cont = document.getElementById('projectList');
               cont.innerHTML = projs.length ? '' : '<div style=\"padding:20px;text-align:center;color:#888;\">Нет проектов</div>';
               projs.forEach(p => {
                   const d = document.createElement('div');
                   d.className = 'project-item';
                   d.onclick = () => openProject(p.name);
                   d.innerHTML = `<div class=\"project-name\">📁 ${p.name}</div><div class=\"project-date\">📅 ${p.date}</div>`;
                   cont.appendChild(d);
               });
           });
       }
       function openProject(name) {
           currentProject = name;
           document.getElementById('statusText').innerHTML = `📁 ${name}`;
           fetch(`/api/open_project/${name}`).then(r=>r.json()).then(data => {
               files = data;
               renderFileTree();
               renderTabs();
               const first = Object.keys(files).find(f=>f.endsWith('.html')||f==='index.html') || Object.keys(files)[0];
               if(first) openFile(first);
               addConsole(`📂 Открыт: ${name} (${Object.keys(files).length} файлов)`,'info');
           });
       }
       function renderFileTree() {
           const cont = document.getElementById('fileTree');
           cont.innerHTML = '';
           const tree = {};
           Object.keys(files).sort().forEach(p => {
               const parts = p.split('/');
               let cur = tree;
               parts.forEach((pt,i) => { if(!cur[pt]) cur[pt] = i===parts.length-1 ? null : {}; if(typeof cur[pt]==='object') cur=cur[pt]; });
           });
           function build(obj, indent=0, parent='') {
               Object.keys(obj).sort().forEach(k => {
                   const full = parent ? parent+'/'+k : k;
                   const d = document.createElement('div');
                   d.style.marginLeft = indent+'px';
                   d.className = 'file-tree-item';
                   if(obj[k]===null) {
                       d.innerHTML = `<span class=\"file-icon\">📄 ${k}</span>`;
                       d.onclick = () => openFile(full);
                       d.oncontextmenu = (e) => { e.preventDefault(); showContextMenu(e,full,false); return false; };
                   } else {
                       d.innerHTML = `<span class=\"folder-icon\">📁 ${k}</span>`;
                       d.onclick = (e) => { e.stopPropagation(); const ch = document.getElementById(`f-${full.replace(/\\//g,'-')}`); if(ch) { ch.style.display = ch.style.display==='none'?'block':'none'; } };
                       d.oncontextmenu = (e) => { e.preventDefault(); showContextMenu(e,full,true); return false; };
                       cont.appendChild(d);
                       const chDiv = document.createElement('div');
                       chDiv.id = `f-${full.replace(/\\//g,'-')}`;
                       chDiv.className = 'tree-indent';
                       chDiv.style.display = 'none';
                       cont.appendChild(chDiv);
                       const old = cont;
                       cont = chDiv;
                       build(obj[k], indent+18, full);
                       cont = old;
                   }
                   cont.appendChild(d);
               });
           }
           build(tree);
       }
       function expandAll() { document.querySelectorAll('[id^=\"f-\"]').forEach(el=>el.style.display='block'); }
       function collapseAll() { document.querySelectorAll('[id^=\"f-\"]').forEach(el=>el.style.display='none'); }
       function renderTabs() {
           const cont = document.getElementById('tabs');
           cont.innerHTML = '';
           Object.keys(files).sort().forEach(f => {
               const t = document.createElement('div');
               t.className = 'tab' + (activeTab===f ? ' active' : '');
               t.innerHTML = `${f.split('/').pop()} <span class=\"tab-close\" onclick=\"closeTab('${f.replace(/'/g,\"\\\\'\")}')\">✕</span>`;
               t.onclick = (e) => { if(e.target!==t.querySelector('.tab-close')) openFile(f); };
               cont.appendChild(t);
           });
       }
       function openFile(f) {
           activeTab = f;
           document.getElementById('codeEditor').value = files[f]||'';
           updateLineNumbers();
           renderTabs();
           updatePreview();
           document.getElementById('statusText').innerHTML = `✏️ ${f}`;
       }
       function updatePreview() {
           if(activeTab && activeTab.endsWith('.html')) document.getElementById('previewIframe').srcdoc = document.getElementById('codeEditor').value;
           else if(activeTab && activeTab.endsWith('.css')) document.getElementById('previewIframe').srcdoc = `<html><head><style>${document.getElementById('codeEditor').value}</style></head><body style=\"background:#1e1e1e;color:white;display:flex;justify-content:center;align-items:center;\"><div><h1>🎨 CSS Preview</h1></div></body></html>`;
           else if(activeTab && activeTab.endsWith('.js')) {
               const js = document.getElementById('codeEditor').value;
               document.getElementById('previewIframe').srcdoc = `<html><body style=\"background:#1e1e1e;color:white;padding:20px;\"><pre id=\"out\" style=\"background:#000;padding:15px;\"></pre><script>const out=document.getElementById('out');const oldLog=console.log;console.log=(...a)=>{out.innerHTML+=a.join(' ')+'\\n';oldLog(...a);};${js}<\\/script></body></html>`;
           }
       }
       function saveFile() {
           if(activeTab && currentProject) {
               const content = document.getElementById('codeEditor').value;
               files[activeTab] = content;
               fetch('/api/save_file',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({project:currentProject,filename:activeTab,content:content})})
                   .then(()=>addConsole(`💾 Сохранен: ${activeTab}`,'success'));
           }
       }
       function runInBrowser() {
           if(activeTab && activeTab.endsWith('.html')) {
               const blob = new Blob([document.getElementById('codeEditor').value],{type:'text/html'});
               window.open(URL.createObjectURL(blob));
               addConsole(`🌐 Запущен: ${activeTab}`,'success');
           } else addConsole('Откройте HTML файл','warning');
       }
       function openInNewTab() {
           if(activeTab && activeTab.endsWith('.html')) {
               const blob = new Blob([document.getElementById('codeEditor').value],{type:'text/html'});
               window.open(URL.createObjectURL(blob));
           } else addConsole('Откройте HTML файл','warning');
       }
       function formatCode() {
           let txt = document.getElementById('codeEditor').value;
           if(activeTab && activeTab.endsWith('.html')) {
               let ind=0;
               txt = txt.split('\\n').map(l=>{ l=l.trim(); if(!l) return ''; if(l.startsWith('</')) ind--; const r='  '.repeat(Math.max(0,ind))+l; if(l.endsWith('>')&&!l.endsWith('/>')&&!l.startsWith('</')&&!l.startsWith('<!')) ind++; return r; }).join('\\n');
           } else if(activeTab && activeTab.endsWith('.css')) {
               let ind=0;
               txt = txt.split('\\n').map(l=>{ l=l.trim(); if(!l) return ''; if(l.includes('}')) ind--; const r='  '.repeat(Math.max(0,ind))+l; if(l.includes('{')) ind++; return r; }).filter(l=>l).join('\\n');
           } else if(activeTab && activeTab.endsWith('.js')) {
               let ind=0;
               txt = txt.split('\\n').map(l=>{ l=l.trim(); if(!l) return ''; if(l.includes('}')&&!l.includes('{')) ind--; const r='  '.repeat(Math.max(0,ind))+l; if(l.includes('{')) ind++; return r; }).filter(l=>l).join('\\n');
           }
           document.getElementById('codeEditor').value = txt;
           updateLineNumbers();
           addConsole('✨ Код отформатирован','success');
       }
       function clearConsole() { document.getElementById('console').innerHTML = '<div class=\"console-line info\">> Консоль очищена</div>'; }
       function closeTab(f) {
           delete files[f];
           if(activeTab===f) { const ks=Object.keys(files); activeTab=ks.length?ks[0]:null; document.getElementById('codeEditor').value=activeTab?files[activeTab]:''; updateLineNumbers(); updatePreview(); }
           renderTabs(); renderFileTree();
       }
       function newFolder() { const n=prompt('Имя папки:'); if(n&&currentProject) fetch('/api/create_folder',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({project:currentProject,path:n})}).then(()=>{addConsole(`📁 Создана: ${n}`,'success'); openProject(currentProject);}); }
       function newFile() { const n=prompt('Имя файла (с расширением):','new.html'); if(n&&currentProject) fetch('/api/create_file',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({project:currentProject,filename:n})}).then(()=>{addConsole(`📄 Создан: ${n}`,'success'); openProject(currentProject);}); }
       function showContextMenu(e,path,isFolder) {
           e.preventDefault();
           contextMenuItem={path,isFolder};
           const m=document.getElementById('contextMenu');
           m.innerHTML=`<div class=\"context-menu-item\" onclick=\"renameItem()\">✏️ Переименовать</div><div class=\"context-menu-item\" onclick=\"deleteItem()\">🗑️ Удалить</div>${isFolder?'<div class=\"context-menu-item\" onclick=\"newFileInFolder()\">📄 Новый файл</div><div class=\"context-menu-item\" onclick=\"newFolderInFolder()\">📁 Новая папка</div>':''}`;
           m.style.display='block'; m.style.left=e.pageX+'px'; m.style.top=e.pageY+'px';
           setTimeout(()=>document.addEventListener('click',()=>m.style.display='none'),100);
       }
       function renameItem() { document.getElementById('renameInput').value=contextMenuItem.path.split('/').pop(); document.getElementById('renameModal').style.display='flex'; window.pendingRename=contextMenuItem; }
       function confirmRename() { const n=document.getElementById('renameInput').value; if(n&&window.pendingRename) fetch('/api/rename_item',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({project:currentProject,oldPath:window.pendingRename.path,newName:n,isFolder:window.pendingRename.isFolder})}).then(()=>{addConsole(`✏️ Переименовано`,'success'); closeModal('renameModal'); openProject(currentProject);}); }
       function deleteItem() { if(confirm(`Удалить ${contextMenuItem.path}?`)) fetch('/api/delete_item',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({project:currentProject,path:contextMenuItem.path,isFolder:contextMenuItem.isFolder})}).then(()=>{addConsole(`🗑️ Удалено`,'success'); openProject(currentProject);}); }
       function newFileInFolder() { const n=prompt('Имя файла:','new.html'); if(n) fetch('/api/create_item',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({project:currentProject,parentPath:contextMenuItem.path,name:n,type:'file'})}).then(()=>{addConsole(`📄 Создан: ${n}`,'success'); openProject(currentProject);}); }
       function newFolderInFolder() { const n=prompt('Имя папки:','new_folder'); if(n) fetch('/api/create_item',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({project:currentProject,parentPath:contextMenuItem.path,name:n,type:'folder'})}).then(()=>{addConsole(`📁 Создана: ${n}`,'success'); openProject(currentProject);}); }
       function executeSQL() {
           const db=document.getElementById('dbNameInput').value, q=document.getElementById('sqlQueryInput').value;
           if(!db||!q) return addConsole('Введите данные','error');
           fetch('/api/execute_sql',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({db_name:db,query:q,project:currentProject})}).then(r=>r.json()).then(d=>{
               const resDiv=document.getElementById('sqlResult');
               if(d.error) resDiv.innerHTML=`<div style=\"color:#f48771\">❌ ${d.error}</div>`;
               else if(d.result) {
                   if(!d.result.length) resDiv.innerHTML='<div style=\"color:#6a9955\">✅ Нет данных</div>';
                   else {
                       let html='<table style=\"width:100%;border-collapse:collapse;font-size:10px;\"><thead><tr>'+Object.keys(d.result[0]).map(k=>`<th style=\"border:1px solid #007acc;padding:4px;\">${k}</th>`).join('')+'</thead><tbody>';
                       d.result.slice(0,50).forEach(r=>{ html+='<tr>'+Object.values(r).map(v=>`<td style=\"border:1px solid #333;padding:4px;\">${v!==null?v:'NULL'}</td>`).join('')+'</tr>'; });
                       html+='</tbody></table>';
                       if(d.result.length>50) html+=`<div style=\"margin-top:5px;color:#888;\">Показано 50 из ${d.result.length}</div>`;
                       resDiv.innerHTML=html;
                   }
                   addConsole(`✅ SQL: ${d.result.length} строк`,'success');
               } else if(d.rowcount!==undefined) { resDiv.innerHTML=`<div style=\"color:#6a9955\">✅ Выполнено, затронуто строк: ${d.rowcount}</div>`; addConsole(`✅ Выполнено: ${d.rowcount} строк`,'success'); }
               else addConsole(`✅ Выполнено`,'success');
           });
       }
       loadProjects();
       setInterval(()=>{ if(currentProject&&activeTab) saveFile(); },30000);
       updateLineNumbers();
   </script>
</body>
</html>
'''

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/get_projects')
def get_projects():
    projs = []
    if os.path.exists(PROJECTS_DIR):
        for i in os.listdir(PROJECTS_DIR):
            p = os.path.join(PROJECTS_DIR, i)
            if os.path.isdir(p):
                projs.append(
                    {'name': i, 'date': datetime.fromtimestamp(os.path.getctime(p)).strftime('%Y-%m-%d %H:%M')})
    return jsonify(projs)


@app.route('/api/create_project', methods=['POST'])
def create_project():
    name = request.json.get('name')
    if name:
        path = os.path.join(PROJECTS_DIR, name)
        if not os.path.exists(path):
            os.makedirs(path)
            for fn, ct in [('index.html',
                           '<!DOCTYPE html>\n<html>\n<head><meta charset="UTF-8"><title>' + name + '</title><link rel="stylesheet" href="style.css"></head>\n<body>\n<div class="container"><h1>' + name + '</h1><p>Добро пожаловать!</p></div>\n<script src="script.js"></script>\n</body>\n</html>'),
                          ('style.css',
                           '*{margin:0;padding:0;box-sizing:border-box;}body{font-family:sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;display:flex;justify-content:center;align-items:center;}.container{background:white;border-radius:20px;padding:40px;text-align:center;}h1{color:#667eea;}'),
                          ('script.js', 'console.log("Проект ' + name + ' загружен");')]:
                with open(os.path.join(path, fn), 'w', encoding='utf-8') as f:
                    f.write(ct)
    return jsonify({'ok': True})


@app.route('/api/import_project', methods=['POST'])
def import_project():
    name = request.form.get('name')
    files_list = request.files.getlist('files')
    if name and files_list:
        path = os.path.join(PROJECTS_DIR, name)
        if not os.path.exists(path):
            os.makedirs(path)
        for f in files_list:
            rel = f.filename.replace(name + '/', '')
            if rel:
                full = os.path.join(path, rel)
                os.makedirs(os.path.dirname(full), exist_ok=True)
                f.save(full)
    return jsonify({'ok': True})


@app.route('/api/open_project/<name>')
def open_project(name):
    path = os.path.join(PROJECTS_DIR, name)
    files_dict = {}
    if os.path.exists(path):
        for root, _, files in os.walk(path):
            for f in files:
                if f.endswith(('.html', '.css', '.js', '.csv', '.txt', '.json', '.xml', '.sql', '.md')):
                    rel = os.path.relpath(os.path.join(root, f), path)
                    try:
                        with open(os.path.join(root, f), 'r', encoding='utf-8') as fp:
                            files_dict[rel] = fp.read()
                    except:
                        files_dict[rel] = ''
    return jsonify(files_dict)


@app.route('/api/save_file', methods=['POST'])
def save_file():
    data = request.json
    project = data.get('project')  # Исправлено: было 'projects'
    filename = data.get('filename')
    content = data.get('content')
    if project and filename and content is not None:
        path = os.path.join(PROJECTS_DIR, project, filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
    return jsonify({'ok': True})


@app.route('/api/create_folder', methods=['POST'])
def create_folder():
    data = request.json
    project = data.get('project')  # Исправлено: было 'projects'
    path = data.get('path')
    if project and path:
        folder = os.path.join(PROJECTS_DIR, project, path)
        if not os.path.exists(folder):
            os.makedirs(folder)
    return jsonify({'ok': True})


@app.route('/api/create_file', methods=['POST'])
def create_file():
    data = request.json
    project = data.get('project')  # Исправлено: было 'projects'
    filename = data.get('filename')
    if project and filename:
        path = os.path.join(PROJECTS_DIR, project, filename)
        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8') as f:
                ext = filename.split('.')[-1].lower()
                if ext == 'html':
                    f.write('<!DOCTYPE html>\n<html>\n<head>\n<title>New</title>\n</head>\n<body>\n   \n</body>\n</html>')
                elif ext == 'css':
                    f.write('/* Styles */\n')
                elif ext == 'js':
                    f.write('// JavaScript\n')
                else:
                    f.write('')
    return jsonify({'ok': True})


@app.route('/api/rename_item', methods=['POST'])
def rename_item():
    data = request.json
    project = data.get('project')
    old_path = data.get('oldPath')
    new_name = data.get('newName')
    if project and old_path and new_name:
        old = os.path.join(PROJECTS_DIR, project, old_path)
        new = os.path.join(PROJECTS_DIR, project, os.path.dirname(old_path), new_name)
        if os.path.exists(old):
            os.rename(old, new)
    return jsonify({'ok': True})


@app.route('/api/delete_item', methods=['POST'])
def delete_item():
    data = request.json
    project = data.get('project')
    path = data.get('path')
    is_folder = data.get('isFolder', False)
    if project and path:
        full = os.path.join(PROJECTS_DIR, project, path)
        if os.path.exists(full):
            if is_folder and os.path.isdir(full):
                shutil.rmtree(full)
            elif os.path.isfile(full):
                os.remove(full)
    return jsonify({'ok': True})


@app.route('/api/create_item', methods=['POST'])
def create_item():
    data = request.json
    project = data.get('project')
    parent_path = data.get('parentPath')
    name = data.get('name')
    typ = data.get('type')
    if project and parent_path and name:
        full = os.path.join(PROJECTS_DIR, project, parent_path, name)
        if typ == 'file':
            with open(full, 'w', encoding='utf-8') as f:
                ext = name.split('.')[-1].lower()
                if ext == 'html':
                    f.write('<!DOCTYPE html>\n<html>\n<head>\n<title>New</title>\n</head>\n<body>\n   \n</body>\n</html>')
                elif ext == 'css':
                    f.write('/* Styles */\n')
                elif ext == 'js':
                    f.write('// JavaScript\n')
                else:
                    f.write('')
        else:
            os.makedirs(full, exist_ok=True)
    return jsonify({'ok': True})


@app.route('/api/execute_sql', methods=['POST'])
def execute_sql():
    data = request.json
    db_name = data.get('db_name')
    query = data.get('query')
    project = data.get('project')
    if db_name and query:
        db_path = os.path.join(PROJECTS_DIR, project, f'{db_name}.db') if project else os.path.join(PROJECTS_DIR, f'{db_name}.db')
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(query)
            if query.strip().upper().startswith('SELECT'):
                rows = cur.fetchall()
                conn.close()
                return jsonify({'result': [dict(r) for r in rows], 'rowcount': len(rows)})
            else:
                conn.commit()
                rc = cur.rowcount
                conn.close()
                return jsonify({'rowcount': rc})
        except Exception as e:
            return jsonify({'error': str(e)})
    return jsonify({'error': 'No data'})


class ArmixWebStudio:
    def __init__(self):
        self.port = find_free_port()
        self.root = None

    def run_flask(self):
        app.run(host='127.0.0.1', port=self.port, debug=False, use_reloader=False)

    def create_gui(self):
        self.root = tk.Tk()
        self.root.title("ARMIX WebStudio Pro")
        self.root.geometry("520x420")
        self.root.configure(bg='#0a0a0f')
        self.root.resizable(False, False)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TLabel', background='#0a0a0f', foreground='white', font=('Segoe UI', 11))
        style.configure('TButton', background='#007acc', foreground='white', borderwidth=0, font=('Segoe UI', 10))

        main = tk.Frame(self.root, bg='#0a0a0f')
        main.pack(fill='both', expand=True, padx=25, pady=25)

        title = tk.Label(main, text=" ARMIX WebStudio Pro", font=('Segoe UI', 20, 'bold'), bg='#0a0a0f', fg='#007acc')
        title.pack(pady=10)

        tk.Label(main, text="Современная IDE для веб разработки", font=('Segoe UI', 10), bg='#0a0a0f', fg='#888').pack()
        status_frame = tk.Frame(main, bg='#1a1a2a', relief='flat', bd=1, highlightbackground='#007acc', highlightthickness=1)
        status_frame.pack(fill='x', pady=20, padx=15)
        status_frame.configure(highlightbackground='#007acc', highlightthickness=1)

        self.status = tk.Label(status_frame, text=" Запуск сервера...", font=('Consolas', 10), bg='#1a1a2a', fg='#569cd6')
        self.status.pack(pady=12, padx=15)

        self.progress = ttk.Progressbar(status_frame, mode='indeterminate', length=280)
        self.progress.pack(pady=8)
        self.progress.start(10)

        tk.Label(main, text=f"Порт: {self.port}", font=('Consolas', 9), bg='#0a0a0f', fg='#888').pack()

        threading.Thread(target=self.run_flask, daemon=True).start()
        self.root.after(2000, self.on_ready)

        btn_frame = tk.Frame(main, bg='#0a0a0f')
        btn_frame.pack(pady=20)

        self.open_btn = tk.Button(btn_frame, text=" Открыть в браузере", bg='#007acc', fg='white', font=('Segoe UI', 11, 'bold'), padx=25, pady=6, relief='flat', cursor='hand2', state='disabled', command=lambda: webbrowser.open(f'http://127.0.0.1:{self.port}'))
        self.open_btn.pack(side='left', padx=8)

        tk.Label(main, text=" 2026 ARMIX Studio", font=('Segoe UI', 8), bg='#0a0a0f', fg='#555').pack(side='bottom', pady=10)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    def on_ready(self):
        self.progress.stop()
        self.status.config(text=" Сервер запущен!", fg='#6a9955')
        self.open_btn.config(state='normal')
        splash = tk.Toplevel(self.root)
        splash.title("ARMIX")
        splash.geometry("280x130")
        splash.configure(bg='#0a0a0f')
        splash.overrideredirect(True)
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 140
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 65
        splash.geometry(f"+{x}+{y}")
        tk.Label(splash, text=" ARMIX WebStudio", font=('Segoe UI', 12, 'bold'), bg='#0a0a0f', fg='#007acc').pack(pady=15)
        tk.Label(splash, text="Готов к работе!", font=('Consolas', 9), bg='#0a0a0f', fg='#6a9955').pack()
        tk.Label(splash, text=f"http://127.0.0.1:{self.port}", font=('Consolas', 9), bg='#0a0a0f', fg='#569cd6').pack(pady=8)
        splash.after(2000, splash.destroy)

    def on_close(self):
        self.root.quit()
        os._exit(0)


if __name__ == '__main__':
    app_instance = ArmixWebStudio()
    app_instance.create_gui()