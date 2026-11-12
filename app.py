import os
import re
import argparse
import json
from http.server import SimpleHTTPRequestHandler, HTTPServer

class Fail2BanHandler(SimpleHTTPRequestHandler):
    def get_fail2ban_stats(self):
        log_path = self.server.log_path
        banned_ips = set()
        unbanned_ips = set()
        recent_failures = []

        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    # 1. Capturar os UNBANS
                    if 'Unban' in line:
                        match = re.search(r'Unban\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
                        if match:
                            ip = match.group(1)
                            unbanned_ips.add(ip)
                            if ip in banned_ips:
                                banned_ips.remove(ip)

                    # 2. Capturar os BANS ATIVOS
                    elif 'Ban' in line:
                        match = re.search(r'\bBan\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
                        if match:
                            ip = match.group(1)
                            banned_ips.add(ip)
                            if ip in unbanned_ips:
                                unbanned_ips.remove(ip)

                    # 3. Capturar as FALHAS
                    elif 'Found' in line:
                        match_time = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                        match_jail = re.search(r'\[(.*?)\]\s+Found', line)
                        match_ip = re.search(r'Found\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)

                        if match_ip:
                            time_str = match_time.group(1) if match_time else "Desconhecido"
                            jail_str = match_jail.group(1) if match_jail else "Geral"
                            ip_str = match_ip.group(1)

                            detail_str = line.strip()
                            if "INFO" in detail_str:
                                detail_str = detail_str.split("INFO")[-1].strip()

                            recent_failures.insert(0, {
                                "time": time_str,
                                "jail": jail_str,
                                "ip": ip_str,
                                "detail": detail_str
                            })

        lista_banidos = sorted(list(banned_ips))
        lista_liberados = sorted(list(unbanned_ips))

        # Mantém seu log de console que funcionou perfeitamente!
        print("\n================ [DEBUG MEMÓRIA FAIL2BAN] ================")
        print(f"-> IPs ATIVAMENTE BANIDOS ({len(lista_banidos)}): {lista_banidos}")
        print(f"-> HISTÓRICO DE LIBERADOS ({len(lista_liberados)}): {lista_liberados}")
        print("==========================================================\n")

        return {
            "banned": lista_banidos,
            "unbanned": lista_liberados,
            "failures": recent_failures[:100]
        }

    def do_GET(self):
        if self.path == '/api/stats':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            stats = self.get_fail2ban_stats()
            self.wfile.write(json.dumps(stats).encode('utf-8'))
            return

        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()

            html = """
            <!DOCTYPE html>
            <html lang="pt-BR">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Fail2Ban Monitor</title>
                <script src="https://cdn.tailwindcss.com"></script>
                <style>
                    :root { color-scheme: dark; }
                    ::-webkit-scrollbar { width: 8px; height: 8px; }
                    ::-webkit-scrollbar-track { background: #111827; }
                    ::-webkit-scrollbar-thumb { background: #475569; border-radius: 999px; }
                    ::-webkit-scrollbar-thumb:hover { background: #64748b; }
                    body { background: #080b18; }
                    .page-glow { background: radial-gradient(circle at 8% 0%, rgba(124, 58, 237, .22), transparent 32%), radial-gradient(circle at 94% 8%, rgba(14, 165, 233, .16), transparent 28%); }
                    .glass { background: rgba(15, 23, 42, .72); border: 1px solid rgba(148, 163, 184, .14); box-shadow: 0 24px 70px rgba(2, 6, 23, .28); backdrop-filter: blur(18px); }
                    .metric-card { position: relative; overflow: hidden; transition: transform .2s ease, border-color .2s ease, box-shadow .2s ease; }
                    .metric-card:hover { transform: translateY(-3px); border-color: rgba(148, 163, 184, .3); box-shadow: 0 18px 45px rgba(2, 6, 23, .42); }
                    .metric-card::after { content: ''; position: absolute; width: 130px; height: 130px; right: -42px; top: -50px; border-radius: 999px; background: var(--metric-glow); filter: blur(2px); opacity: .25; }
                    .spin-once { animation: spin 0.6s ease-in-out; }
                    .pulse-soft { animation: pulse-soft 2s ease-in-out infinite; }
                    @keyframes spin { 100% { transform: rotate(360deg); } }
                    @keyframes pulse-soft { 0%, 100% { opacity: 1; } 50% { opacity: .55; } }
                    @media (max-width: 640px) { .table-wrap { margin-left: -1rem; margin-right: -1rem; } }
                </style>
            </head>
            <body class="text-slate-100 font-sans min-h-screen page-glow">
                <div class="max-w-6xl mx-auto px-4 sm:px-6 py-6 sm:py-10">

                    <header class="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6 mb-10">
                        <div>
                            <div class="flex items-center gap-3 mb-4">
                                <span class="flex items-center justify-center w-11 h-11 rounded-2xl bg-gradient-to-br from-violet-500 to-fuchsia-500 shadow-lg shadow-violet-500/25 text-xl">🛡️</span>
                                <span class="text-xs font-bold uppercase tracking-[.24em] text-violet-300">Security command center</span>
                            </div>
                            <h1 class="text-3xl sm:text-4xl font-black tracking-tight text-white">Fail2Ban <span class="text-transparent bg-clip-text bg-gradient-to-r from-violet-400 via-fuchsia-400 to-sky-400">Dashboard</span></h1>
                            <p class="text-slate-400 text-sm mt-2 max-w-xl">Visão geral da proteção da sua VPS, com eventos e bloqueios monitorados em tempo real.</p>
                        </div>

                        <div class="glass rounded-2xl p-3 flex items-center gap-3 w-fit">
                            <div class="flex items-center gap-2.5 pr-3 border-r border-slate-700/70">
                                <span class="relative flex h-2.5 w-2.5">
                                    <span id="status-ping" class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                                    <span id="status-dot" class="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-400"></span>
                                </span>
                                <div class="leading-tight"><p class="text-[10px] uppercase tracking-wider text-slate-500">Status</p><p id="status-text" class="text-xs font-semibold text-emerald-300">Sistema online</p></div>
                            </div>
                            <div class="text-right leading-tight"><p class="text-[10px] uppercase tracking-wider text-slate-500">Próxima atualização</p><p id="countdown-text" class="text-sm font-bold text-white tabular-nums">5s</p></div>
                            <button id="btn-refresh" onclick="forceRefresh()" class="flex items-center justify-center w-9 h-9 rounded-xl bg-white/10 hover:bg-white/20 active:scale-95 text-slate-200 hover:text-white transition-all focus:outline-none focus:ring-2 focus:ring-violet-400/50" title="Recarregar agora">
                                <svg id="svg-refresh" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.253 8H18"></path>
                                </svg>
                            </button>
                        </div>
                    </header>

                    <section class="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-5 mb-10">
                        <div class="metric-card glass rounded-2xl p-5 sm:p-6" style="--metric-glow:#f43f5e">
                            <div class="flex items-start justify-between"><div class="flex items-center gap-2 text-rose-300"><span class="flex w-8 h-8 items-center justify-center rounded-lg bg-rose-500/15">⛔</span><p class="text-xs font-bold uppercase tracking-wider">IPs bloqueados</p></div><span class="text-[10px] font-bold uppercase tracking-widest text-rose-300/70">Ativos</span></div>
                            <p id="total-count" class="text-4xl font-black text-white mt-5 tabular-nums">0</p>
                            <p class="text-xs text-slate-500 mt-1">Ameaças atualmente contidas</p>
                        </div>
                        <div class="metric-card glass rounded-2xl p-5 sm:p-6" style="--metric-glow:#34d399">
                            <div class="flex items-start justify-between"><div class="flex items-center gap-2 text-emerald-300"><span class="flex w-8 h-8 items-center justify-center rounded-lg bg-emerald-500/15">✓</span><p class="text-xs font-bold uppercase tracking-wider">IPs liberados</p></div><span class="text-[10px] font-bold uppercase tracking-widest text-emerald-300/70">Histórico</span></div>
                            <p id="unbanned-count" class="text-4xl font-black text-white mt-5 tabular-nums">0</p>
                            <p class="text-xs text-slate-500 mt-1">Endereços únicos desbloqueados</p>
                        </div>
                        <div class="metric-card glass rounded-2xl p-5 sm:p-6" style="--metric-glow:#fbbf24">
                            <div class="flex items-start justify-between"><div class="flex items-center gap-2 text-amber-300"><span class="flex w-8 h-8 items-center justify-center rounded-lg bg-amber-500/15">⚡</span><p class="text-xs font-bold uppercase tracking-wider">Tentativas detectadas</p></div><span class="text-[10px] font-bold uppercase tracking-widest text-amber-300/70">Recentes</span></div>
                            <p id="failure-count" class="text-4xl font-black text-white mt-5 tabular-nums">0</p>
                            <p class="text-xs text-slate-500 mt-1">Falhas registradas no monitoramento</p>
                        </div>
                    </section>

                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
                        <div><h2 class="text-lg font-bold text-white">Atividade de segurança</h2><p class="text-xs text-slate-500 mt-1">Explore os eventos coletados pelo Fail2Ban</p></div>
                        <nav class="flex items-center gap-1 p-1 rounded-xl bg-slate-900/70 border border-slate-800/80" aria-label="Tabs">
                            <button id="tab-banned" onclick="switchTab('banned')" class="border-b-2 border-rose-400 bg-rose-500/10 text-rose-300 rounded-lg px-3 py-2 text-xs font-bold flex items-center gap-2 focus:outline-none transition-all"><span>⛔</span> Bloqueados</button>
                            <button id="tab-unbanned" onclick="switchTab('unbanned')" class="border-b-2 border-transparent text-slate-400 hover:text-slate-200 rounded-lg px-3 py-2 text-xs font-bold flex items-center gap-2 focus:outline-none transition-all"><span>✓</span> Liberados</button>
                            <button id="tab-failures" onclick="switchTab('failures')" class="border-b-2 border-transparent text-slate-400 hover:text-slate-200 rounded-lg px-3 py-2 text-xs font-bold flex items-center gap-2 focus:outline-none transition-all"><span>⚡</span> Falhas</button>
                        </nav>
                    </div>
                    <div class="glass rounded-2xl flex flex-col max-h-[700px] overflow-hidden">

                        <div id="panel-banned" class="block flex flex-col flex-1 overflow-hidden">
                            <div class="sticky top-0 bg-slate-950/85 backdrop-blur-md border-b border-slate-800/80 px-4 sm:px-6 py-4 z-10">
                                <div class="flex gap-3 items-center mb-3">
                                    <input type="text" id="search-ip" placeholder="🔍  Pesquisar endereço IP..." aria-label="Pesquisar IP bloqueado" class="flex-1 px-4 py-2.5 bg-slate-900/80 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-rose-400 focus:ring-2 focus:ring-rose-400/20 transition-all text-sm" />
                                    <span class="text-xs text-slate-400">Exibindo: <span id="banned-display-count" class="font-bold text-red-400">0</span>/<span id="banned-total-count" class="font-bold">0</span></span>
                                </div>
                            </div>
                            <div class="table-wrap overflow-x-auto overflow-y-auto flex-1">
                                <table class="w-full text-left border-collapse">
                                    <thead class="sticky top-0 bg-slate-950/95 shadow-md">
                                        <tr class="border-b border-slate-800/80 text-slate-500 text-[10px] uppercase tracking-[.18em] bg-slate-900/50">
                                            <th class="py-3.5 px-4 sm:px-6 font-bold">Endereço IP</th>
                                            <th class="py-3.5 px-4 sm:px-6 font-bold">Status</th>
                                        </tr>
                                    </thead>
                                    <tbody id="ip-table-body" class="divide-y divide-slate-800/60 text-sm"></tbody>
                                </table>
                            </div>
                        </div>

                        <div id="panel-unbanned" class="hidden flex flex-col flex-1 overflow-hidden">
                            <div class="sticky top-0 bg-slate-950/85 backdrop-blur-md border-b border-slate-800/80 px-4 sm:px-6 py-4 z-10">
                                <div class="flex gap-3 items-center mb-3">
                                    <input type="text" id="search-unbanned-ip" placeholder="🔍  Pesquisar endereço IP..." aria-label="Pesquisar IP liberado" class="flex-1 px-4 py-2.5 bg-slate-900/80 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-400 focus:ring-2 focus:ring-emerald-400/20 transition-all text-sm" />
                                    <span class="text-xs text-slate-400">Exibindo: <span id="unbanned-display-count" class="font-bold text-emerald-400">0</span>/<span id="unbanned-total-count" class="font-bold">0</span></span>
                                </div>
                            </div>
                            <div class="table-wrap overflow-x-auto overflow-y-auto flex-1">
                                <table class="w-full text-left border-collapse">
                                    <thead class="sticky top-0 bg-slate-950/95 shadow-md">
                                        <tr class="border-b border-slate-800/80 text-slate-500 text-[10px] uppercase tracking-[.18em] bg-slate-900/50">
                                            <th class="py-3.5 px-4 sm:px-6 font-bold">Endereço IP</th>
                                            <th class="py-3.5 px-4 sm:px-6 font-bold">Status</th>
                                        </tr>
                                    </thead>
                                    <tbody id="unbanned-table-body" class="divide-y divide-slate-800/60 text-sm"></tbody>
                                </table>
                            </div>
                        </div>

                        <div id="panel-failures" class="hidden flex flex-col flex-1 overflow-hidden">
                            <div class="sticky top-0 bg-slate-950/85 backdrop-blur-md border-b border-slate-800/80 px-4 sm:px-6 py-4 z-10">
                                <span class="text-xs text-slate-400">Exibindo <span id="failure-display-count" class="font-bold text-amber-300">0</span> de <span id="failure-total-count" class="font-bold text-slate-200">0</span> últimas falhas</span>
                            </div>
                            <div class="table-wrap overflow-x-auto overflow-y-auto flex-1">
                                <table class="w-full text-left border-collapse">
                                    <thead class="sticky top-0 bg-slate-950/95 shadow-md">
                                        <tr class="border-b border-slate-800/80 text-slate-500 text-[10px] uppercase tracking-[.18em] bg-slate-900/50">
                                            <th class="py-3.5 px-4 font-bold">Horário</th>
                                            <th class="py-3.5 px-4 font-bold">Alvo (Jail)</th>
                                            <th class="py-3.5 px-4 font-bold">IP Origem</th>
                                            <th class="py-3.5 px-4 font-bold">Registro do Log</th>
                                        </tr>
                                    </thead>
                                    <tbody id="failure-table-body" class="divide-y divide-slate-800/60 text-sm"></tbody>
                                </table>
                            </div>
                        </div>

                    </div>
                </div>

                <script>
                    let timeLeft = 5;
                    let countdownInterval;
                    let allBannedIps = [];
                    let allUnbannedIps = [];

                    function filterIPs() {
                        const searchInput = document.getElementById('search-ip');
                        const searchValue = searchInput.value.toLowerCase().trim();
                        const tbodyBanned = document.getElementById('ip-table-body');

                        const rows = tbodyBanned.querySelectorAll('tr');
                        let visibleCount = 0;
                        rows.forEach(row => {
                            const ipCell = row.querySelector('td');
                            if (ipCell) {
                                const ip = ipCell.textContent.trim();
                                const visible = ip.toLowerCase().includes(searchValue);
                                row.style.display = visible ? '' : 'none';
                                if (visible) visibleCount++;
                            }
                        });
                        document.getElementById('banned-display-count').innerText = visibleCount;
                    }

                    function filterUnbannedIPs() {
                        const searchInput = document.getElementById('search-unbanned-ip');
                        const searchValue = searchInput.value.toLowerCase().trim();
                        const tbodyUnbanned = document.getElementById('unbanned-table-body');

                        const rows = tbodyUnbanned.querySelectorAll('tr');
                        let visibleCount = 0;
                        rows.forEach(row => {
                            const ipCell = row.querySelector('td');
                            if (ipCell) {
                                const ip = ipCell.textContent.trim();
                                const visible = ip.toLowerCase().includes(searchValue);
                                row.style.display = visible ? '' : 'none';
                                if (visible) visibleCount++;
                            }
                        });
                        document.getElementById('unbanned-display-count').innerText = visibleCount;
                    }

                    // Forçando reconstrução limpa via iteração robusta
                    function buildBannedTable() {
                        const tbodyBanned = document.getElementById('ip-table-body');
                        tbodyBanned.innerHTML = '';
                        
                        const totalCount = allBannedIps.length;
                        document.getElementById('banned-total-count').innerText = totalCount;
                        
                        if (totalCount === 0) {
                            document.getElementById('banned-display-count').innerText = '0';
                            tbodyBanned.innerHTML = `<tr><td colspan="2" class="py-16 text-center"><div class="text-3xl mb-3 opacity-60">🛡️</div><p class="text-sm font-semibold text-slate-300">Nenhum IP bloqueado</p><p class="text-xs text-slate-500 mt-1">A sua rede está limpa neste momento.</p></td></tr>`;
                            return;
                        }

                        allBannedIps.forEach(ip => {
                            const tr = document.createElement('tr');
                            tr.className = "hover:bg-rose-500/[.04] transition-colors border-l-2 border-transparent hover:border-rose-400";
                            tr.innerHTML = `
                                    <td class="py-4 px-4 sm:px-6 font-mono text-slate-200 font-medium">${ip}</td>
                                    <td class="py-4 px-4 sm:px-6">
                                        <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] font-bold tracking-wider bg-rose-500/10 text-rose-300 border border-rose-500/20"><span class="w-1.5 h-1.5 rounded-full bg-rose-400"></span> BLOQUEADO</span>
                                </td>
                            `;
                            tbodyBanned.appendChild(tr);
                        });
                        
                        document.getElementById('banned-display-count').innerText = totalCount;
                    }

                    // Forçando reconstrução limpa para evitar pular itens do Array
                    function buildUnbannedTable() {
                        const tbodyUnbanned = document.getElementById('unbanned-table-body');
                        tbodyUnbanned.innerHTML = '';
                        
                        const totalCount = allUnbannedIps.length;
                        document.getElementById('unbanned-total-count').innerText = totalCount;
                        
                        if (totalCount === 0) {
                            document.getElementById('unbanned-display-count').innerText = '0';
                            tbodyUnbanned.innerHTML = `<tr><td colspan="2" class="py-16 text-center"><div class="text-3xl mb-3 opacity-60">✓</div><p class="text-sm font-semibold text-slate-300">Nenhum IP liberado</p><p class="text-xs text-slate-500 mt-1">O histórico de desbloqueios aparecerá aqui.</p></td></tr>`;
                            return;
                        }

                        allUnbannedIps.forEach(ip => {
                            const tr = document.createElement('tr');
                            tr.className = "hover:bg-emerald-500/[.04] transition-colors border-l-2 border-transparent hover:border-emerald-400";
                            tr.innerHTML = `
                                    <td class="py-4 px-4 sm:px-6 font-mono text-slate-200 font-medium">${ip}</td>
                                    <td class="py-4 px-4 sm:px-6">
                                        <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] font-bold tracking-wider bg-emerald-500/10 text-emerald-300 border border-emerald-500/20"><span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span> LIBERADO</span>
                                </td>
                            `;
                            tbodyUnbanned.appendChild(tr);
                        });
                        
                        document.getElementById('unbanned-display-count').innerText = totalCount;
                    }

                    function switchTab(tab) {
                        const tabBanned = document.getElementById('tab-banned');
                        const tabUnbanned = document.getElementById('tab-unbanned');
                        const tabFailures = document.getElementById('tab-failures');
                        
                        const panelBanned = document.getElementById('panel-banned');
                        const panelUnbanned = document.getElementById('panel-unbanned');
                        const panelFailures = document.getElementById('panel-failures');

                        tabBanned.className = tabUnbanned.className = tabFailures.className = "border-b-2 border-transparent text-slate-400 hover:text-slate-200 rounded-lg px-3 py-2 text-xs font-bold flex items-center gap-2 focus:outline-none transition-all";
                        panelBanned.classList.add('hidden');
                        panelUnbanned.classList.add('hidden');
                        panelFailures.classList.add('hidden');

                        if (tab === 'banned') {
                            tabBanned.className = "border-b-2 border-rose-400 bg-rose-500/10 text-rose-300 rounded-lg px-3 py-2 text-xs font-bold flex items-center gap-2 focus:outline-none transition-all";
                            panelBanned.classList.remove('hidden');
                        } else if (tab === 'unbanned') {
                            tabUnbanned.className = "border-b-2 border-emerald-400 bg-emerald-500/10 text-emerald-300 rounded-lg px-3 py-2 text-xs font-bold flex items-center gap-2 focus:outline-none transition-all";
                            panelUnbanned.classList.remove('hidden');
                        } else {
                            tabFailures.className = "border-b-2 border-amber-400 bg-amber-500/10 text-amber-300 rounded-lg px-3 py-2 text-xs font-bold flex items-center gap-2 focus:outline-none transition-all";
                            panelFailures.classList.remove('hidden');
                        }
                    }

                    function forceRefresh() {
                        const svg = document.getElementById('svg-refresh');
                        svg.classList.remove('spin-once');
                        void svg.offsetWidth;
                        svg.classList.add('spin-once');

                        timeLeft = 5;
                        document.getElementById('countdown-text').innerText = timeLeft + "s";
                        updateDashboard();
                    }

                    function startCountdown() {
                        clearInterval(countdownInterval);
                        countdownInterval = setInterval(() => {
                            timeLeft--;
                            if (timeLeft <= 0) {
                                timeLeft = 5;
                                updateDashboard();
                            }
                            document.getElementById('countdown-text').innerText = timeLeft + "s";
                        }, 1000);
                    }

                    function setConnectionStatus(online) {
                        const statusText = document.getElementById('status-text');
                        const statusDot = document.getElementById('status-dot');
                        const statusPing = document.getElementById('status-ping');
                        if (online) {
                            statusText.innerText = 'Sistema online';
                            statusText.className = 'text-xs font-semibold text-emerald-300';
                            statusDot.className = 'relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-400';
                            statusPing.className = 'animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75';
                        } else {
                            statusText.innerText = 'Falha de conexão';
                            statusText.className = 'text-xs font-semibold text-rose-300';
                            statusDot.className = 'relative inline-flex rounded-full h-2.5 w-2.5 bg-rose-400';
                            statusPing.className = 'absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-50';
                        }
                    }

                    async function updateDashboard() {
                        try {
                            const searchBannedInput = document.getElementById('search-ip');
                            const savedBannedSearch = searchBannedInput.value;

                            const searchUnbannedInput = document.getElementById('search-unbanned-ip');
                            const savedUnbannedSearch = searchUnbannedInput.value;

                            const response = await fetch('/api/stats');
                            const data = await response.json();
                            setConnectionStatus(true);

                            document.getElementById('total-count').innerText = data.banned.length;
                            document.getElementById('unbanned-count').innerText = data.unbanned.length;
                            document.getElementById('failure-count').innerText = data.failures.length;

                            allBannedIps = data.banned;
                            allUnbannedIps = data.unbanned;

                            buildBannedTable();
                            buildUnbannedTable();

                            searchBannedInput.value = savedBannedSearch;
                            if (savedBannedSearch.trim() !== '') {
                                filterIPs();
                            }

                            searchUnbannedInput.value = savedUnbannedSearch;
                            if (savedUnbannedSearch.trim() !== '') {
                                filterUnbannedIPs();
                            }

                            const tbodyFailures = document.getElementById('failure-table-body');
                            const totalFailures = data.failures.length;
                            document.getElementById('failure-total-count').innerText = totalFailures;
                            
                            if (totalFailures === 0) {
                                document.getElementById('failure-display-count').innerText = '0';
                                tbodyFailures.innerHTML = `<tr><td colspan="4" class="py-16 text-center"><div class="text-3xl mb-3 opacity-60">✨</div><p class="text-sm font-semibold text-slate-300">Nenhuma falha recente</p><p class="text-xs text-slate-500 mt-1">Nenhuma tentativa suspeita foi detectada.</p></td></tr>`;
                            } else {
                                document.getElementById('failure-display-count').innerText = totalFailures;
                                tbodyFailures.innerHTML = data.failures.map(f => `
                                    <tr class="hover:bg-amber-500/[.04] transition-colors border-l-2 border-transparent hover:border-amber-400">
                                        <td class="py-3.5 px-4 text-slate-400 font-mono text-xs">${f.time.split(' ')[1]}</td>
                                        <td class="py-3.5 px-4">
                                            <span class="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 font-mono text-xs font-semibold">${f.jail}</span>
                                        </td>
                                        <td class="py-3.5 px-4 font-mono text-amber-400 font-medium">${f.ip}</td>
                                        <td class="py-3.5 px-4 font-mono text-slate-400 text-xs max-w-md truncate hover:text-slate-200 transition-colors" title="${f.detail}">
                                            ${f.detail}
                                        </td>
                                    </tr>
                                `).join('');
                            }

                        } catch (error) {
                            setConnectionStatus(false);
                            console.error("Erro na atualização automática:", error);
                        }
                    }

                    updateDashboard();
                    startCountdown();

                    document.getElementById('search-ip').addEventListener('input', filterIPs);
                    document.getElementById('search-unbanned-ip').addEventListener('input', filterUnbannedIPs);
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_error(404, "Not Found")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Fail2Ban Monitor Web Dashboard")
    parser.add_argument('--port', type=int, default=15000, help="Porta para o servidor web (Padrão: 15000)")
    parser.add_argument('--log', type=str, default='/var/log/fail2ban.log', help="Caminho do ficheiro de log do Fail2Ban")
    args = parser.parse_args()

    print(f"Iniciando painel Fail2Ban na porta {args.port}...")
    print(f"Monitorando o arquivo: {args.log}")

    server = HTTPServer(('127.0.0.1', args.port), Fail2BanHandler)
    server.log_path = args.log

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado pelo utilizador.")