import os
import re
import argparse
import json
import shutil
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit

class Fail2BanHandler(SimpleHTTPRequestHandler):
    def _get_fail2ban_status(self):
        if not shutil.which('fail2ban-client'):
            return {"state": "unavailable", "message": "fail2ban-client não encontrado", "jails": []}

        try:
            overview = subprocess.run(
                ['fail2ban-client', 'status'], capture_output=True, text=True,
                timeout=3, check=False
            )
            if overview.returncode != 0:
                return {"state": "unavailable", "message": overview.stderr.strip() or "Serviço indisponível", "jails": []}

            jail_match = re.search(r'Jail list:\s*(.*)', overview.stdout)
            jail_names = [name.strip() for name in (jail_match.group(1).split(',') if jail_match else []) if name.strip()]
            jails = []
            for jail in jail_names:
                result = subprocess.run(
                    ['fail2ban-client', 'status', jail], capture_output=True, text=True,
                    timeout=3, check=False
                )
                text = result.stdout
                def value(label):
                    match = re.search(rf'\b{re.escape(label)}:\s*(\d+)', text)
                    return int(match.group(1)) if match else 0

                banned_list_match = re.search(r'Banned IP list:\s*(.*)', text)
                jails.append({
                    "name": jail,
                    "currently_failed": value('Currently failed'),
                    "total_failed": value('Total failed'),
                    "currently_banned": value('Currently banned'),
                    "total_banned": value('Total banned'),
                    "banned_ips": banned_list_match.group(1).split() if banned_list_match else []
                })
            return {"state": "healthy", "message": "Serviço operacional", "jails": jails}
        except (OSError, subprocess.SubprocessError) as error:
            return {"state": "unavailable", "message": str(error), "jails": []}

    def get_fail2ban_stats(self, period_hours=24, jail_filter='all'):
        log_path = self.server.log_path
        banned_ips = set()
        unbanned_ips = set()
        events = []
        ip_jails = defaultdict(set)
        now = datetime.now()
        cutoff = now - timedelta(hours=period_hours)
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'

        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    timestamp_match = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    timestamp = None
                    if timestamp_match:
                        try:
                            timestamp = datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            pass
                    jail_match = re.search(r'\[([^\]]+)\]\s+(?:Found|Ban|Unban)', line)
                    jail = jail_match.group(1) if jail_match else 'Geral'
                    if 'Unban' in line:
                        match = re.search(rf'Unban\s+({ip_pattern})', line)
                        if match:
                            ip = match.group(1)
                            unbanned_ips.add(ip)
                            if ip in banned_ips:
                                banned_ips.remove(ip)
                    elif 'Ban' in line:
                        match = re.search(rf'\bBan\s+({ip_pattern})', line)
                        if match:
                            ip = match.group(1)
                            banned_ips.add(ip)
                            ip_jails[ip].add(jail)
                            if ip in unbanned_ips:
                                unbanned_ips.remove(ip)
                    elif 'Found' in line:
                        match_ip = re.search(rf'Found\s+({ip_pattern})', line)

                        if match_ip:
                            ip = match_ip.group(1)
                            detail_str = line.strip()
                            if "INFO" in detail_str:
                                detail_str = detail_str.split("INFO")[-1].strip()
                            if timestamp:
                                events.append({"type": "failure", "time": timestamp, "time_text": timestamp_match.group(1), "jail": jail, "ip": ip, "detail": detail_str})

                    if ('Ban' in line or 'Found' in line) and timestamp:
                        event_type = 'ban' if 'Ban' in line else 'failure'
                        ip_match = re.search(rf'(?:Ban|Found)\s+({ip_pattern})', line)
                        if ip_match and event_type == 'ban':
                            events.append({"type": event_type, "time": timestamp, "time_text": timestamp.strftime('%Y-%m-%d %H:%M:%S'), "jail": jail, "ip": ip_match.group(1), "detail": line.strip()})

        status = self._get_fail2ban_status()
        if status["jails"]:
            for jail in status["jails"]:
                for ip in jail["banned_ips"]:
                    banned_ips.add(ip)
                    ip_jails[ip].add(jail["name"])

        filtered_events = [event for event in events if event['time'] and event['time'] >= cutoff and (jail_filter == 'all' or event['jail'] == jail_filter)]
        failures = [event for event in filtered_events if event['type'] == 'failure']
        ban_events = [event for event in filtered_events if event['type'] == 'ban']
        failure_counts = Counter(event['ip'] for event in failures)
        jail_counts = Counter(event['jail'] for event in failures)
        hourly = Counter(event['time'].replace(minute=0, second=0, microsecond=0).isoformat() for event in failures)
        hourly_labels = []
        hourly_values = []
        for offset in range(period_hours - 1, -1, -1):
            bucket = (now - timedelta(hours=offset)).replace(minute=0, second=0, microsecond=0)
            hourly_labels.append(bucket.strftime('%d/%m %Hh'))
            hourly_values.append(hourly.get(bucket.isoformat(), 0))

        recent_failures = [{"time": event["time_text"], "jail": event["jail"], "ip": event["ip"], "detail": event["detail"]} for event in reversed(failures[-100:])]
        active_jails = status["jails"] if jail_filter == 'all' else [item for item in status["jails"] if item['name'] == jail_filter]

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
            "failures": recent_failures,
            "filters": {"period": period_hours, "jail": jail_filter},
            "health": status,
            "metrics": {
                "recent_bans": len(ban_events),
                "active_jails": len(active_jails),
                "attack_rate": round(len(failures) / max(period_hours, 1), 1),
                "total_failures": len(failures)
            },
            "charts": {
                "hourly": {"labels": hourly_labels, "values": hourly_values},
                "jails": {"labels": list(jail_counts.keys()), "values": list(jail_counts.values())}
            },
            "top_ips": [{"ip": ip, "count": count, "jails": sorted(ip_jails.get(ip, set()))} for ip, count in failure_counts.most_common(10)],
            "jails": active_jails
        }

    def do_GET(self):
        if urlsplit(self.path).path == '/api/stats':
            params = parse_qs(urlsplit(self.path).query)
            try:
                period_hours = max(1, min(int(params.get('period', ['24'])[0]), 168))
            except ValueError:
                period_hours = 24
            jail_filter = params.get('jail', ['all'])[0]
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            stats = self.get_fail2ban_stats(period_hours, jail_filter)
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
                <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
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

                    <section class="glass rounded-2xl p-4 sm:p-5 mb-6">
                        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                            <div><p class="text-xs font-bold uppercase tracking-wider text-violet-300">Análise de segurança</p><p class="text-xs text-slate-500 mt-1">Ajuste o período e o alvo para explorar os eventos.</p></div>
                            <div class="flex flex-col sm:flex-row gap-2">
                                <label class="flex items-center gap-2 text-xs text-slate-400">Período
                                    <select id="period-filter" class="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-violet-400">
                                        <option value="24">Últimas 24 horas</option><option value="48">Últimas 48 horas</option><option value="168">Últimos 7 dias</option>
                                    </select>
                                </label>
                                <label class="flex items-center gap-2 text-xs text-slate-400">Jail
                                    <select id="jail-filter" class="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-violet-400"><option value="all">Todas as jails</option></select>
                                </label>
                            </div>
                        </div>
                    </section>

                    <section class="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-5 mb-6">
                        <div class="metric-card glass rounded-2xl p-5" style="--metric-glow:#fb7185"><div class="flex items-center justify-between"><span class="text-xs font-bold uppercase tracking-wider text-rose-300">Bans recentes</span><span class="text-lg">🚫</span></div><p id="recent-bans" class="text-3xl font-black text-white mt-4 tabular-nums">0</p><p class="text-xs text-slate-500 mt-1">No período selecionado</p></div>
                        <div class="metric-card glass rounded-2xl p-5" style="--metric-glow:#a78bfa"><div class="flex items-center justify-between"><span class="text-xs font-bold uppercase tracking-wider text-violet-300">Jails ativas</span><span class="text-lg">🔒</span></div><p id="active-jails" class="text-3xl font-black text-white mt-4 tabular-nums">0</p><p class="text-xs text-slate-500 mt-1">Proteções monitoradas</p></div>
                        <div class="metric-card glass rounded-2xl p-5" style="--metric-glow:#38bdf8"><div class="flex items-center justify-between"><span class="text-xs font-bold uppercase tracking-wider text-sky-300">Taxa de ataques</span><span class="text-lg">📈</span></div><p id="attack-rate" class="text-3xl font-black text-white mt-4 tabular-nums">0<span class="text-base font-semibold text-slate-400">/h</span></p><p class="text-xs text-slate-500 mt-1">Média de falhas por hora</p></div>
                    </section>

                    <section class="grid grid-cols-1 lg:grid-cols-5 gap-4 sm:gap-5 mb-6">
                        <div class="glass rounded-2xl p-4 sm:p-5 lg:col-span-3"><div class="flex items-center justify-between mb-4"><div><h3 class="text-sm font-bold text-white">Bans por hora</h3><p class="text-xs text-slate-500 mt-1">Volume de tentativas detectadas</p></div><span class="text-xs text-sky-300">⏱</span></div><div class="h-56"><canvas id="hourly-chart"></canvas><p id="hourly-empty" class="hidden text-center text-xs text-slate-500 pt-20">Sem eventos no período.</p></div></div>
                        <div class="glass rounded-2xl p-4 sm:p-5 lg:col-span-2"><div class="flex items-center justify-between mb-4"><div><h3 class="text-sm font-bold text-white">Distribuição por jail</h3><p class="text-xs text-slate-500 mt-1">Origem das falhas</p></div><span class="text-xs text-fuchsia-300">◉</span></div><div class="h-56 flex items-center justify-center"><canvas id="jail-chart"></canvas><p id="jail-empty" class="hidden text-center text-xs text-slate-500">Sem dados de jail.</p></div></div>
                    </section>

                    <section class="glass rounded-2xl p-4 sm:p-5 mb-10">
                        <div class="flex items-center justify-between mb-4"><div><h3 class="text-sm font-bold text-white">IPs mais ofensores</h3><p class="text-xs text-slate-500 mt-1">Endereços com maior número de falhas</p></div><span class="text-xs text-rose-300">TOP 10</span></div>
                        <div class="overflow-x-auto"><table class="w-full text-left"><thead><tr class="border-b border-slate-800 text-[10px] uppercase tracking-[.18em] text-slate-500"><th class="py-3 px-3">Endereço IP</th><th class="py-3 px-3">Jails</th><th class="py-3 px-3 text-right">Falhas</th></tr></thead><tbody id="top-ips-body" class="divide-y divide-slate-800/60"><tr><td colspan="3" class="py-8 text-center text-xs text-slate-500">Aguardando dados...</td></tr></tbody></table></div>
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
                    let hourlyChart;
                    let jailChart;

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

                    function updateServiceHealth(health) {
                        const healthy = health && health.state === 'healthy';
                        const statusText = document.getElementById('status-text');
                        const statusDot = document.getElementById('status-dot');
                        const statusPing = document.getElementById('status-ping');
                        statusText.innerText = healthy ? 'Fail2Ban saudável' : 'Fail2Ban indisponível';
                        statusText.className = healthy ? 'text-xs font-semibold text-emerald-300' : 'text-xs font-semibold text-amber-300';
                        statusDot.className = healthy ? 'relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-400' : 'relative inline-flex rounded-full h-2.5 w-2.5 bg-amber-400';
                        statusPing.className = healthy ? 'animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75' : 'absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-50';
                    }

                    function updateCharts(charts) {
                        if (typeof Chart === 'undefined') return;
                        const chartColors = ['#a78bfa', '#f472b6', '#38bdf8', '#34d399', '#fbbf24', '#fb7185'];
                        const hourlyCanvas = document.getElementById('hourly-chart');
                        const jailCanvas = document.getElementById('jail-chart');
                        const hourlyEmpty = document.getElementById('hourly-empty');
                        const jailEmpty = document.getElementById('jail-empty');
                        const hasHourly = charts.hourly.values.some(value => value > 0);
                        const hasJails = charts.jails.values.length > 0;
                        hourlyCanvas.classList.toggle('hidden', !hasHourly);
                        hourlyEmpty.classList.toggle('hidden', hasHourly);
                        jailCanvas.classList.toggle('hidden', !hasJails);
                        jailEmpty.classList.toggle('hidden', hasJails);

                        if (hourlyChart) hourlyChart.destroy();
                        if (jailChart) jailChart.destroy();
                        if (hasHourly) {
                            hourlyChart = new Chart(hourlyCanvas, { type: 'line', data: { labels: charts.hourly.labels, datasets: [{ data: charts.hourly.values, borderColor: '#38bdf8', backgroundColor: 'rgba(56,189,248,.14)', borderWidth: 2, pointRadius: 2, pointBackgroundColor: '#7dd3fc', fill: true, tension: .35 }] }, options: { maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { ticks: { color: '#64748b', maxTicksLimit: 8, font: { size: 10 } }, grid: { display: false } }, y: { beginAtZero: true, ticks: { color: '#64748b', precision: 0, font: { size: 10 } }, grid: { color: 'rgba(100,116,139,.12)' } } } } });
                        }
                        if (hasJails) {
                            jailChart = new Chart(jailCanvas, { type: 'doughnut', data: { labels: charts.jails.labels, datasets: [{ data: charts.jails.values, backgroundColor: chartColors, borderColor: '#0f172a', borderWidth: 3 }] }, options: { maintainAspectRatio: false, cutout: '68%', plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8', boxWidth: 10, padding: 14, font: { size: 10 } } } } } });
                        }
                    }

                    function updateTopIps(topIps) {
                        const tbody = document.getElementById('top-ips-body');
                        if (!topIps.length) {
                            tbody.innerHTML = '<tr><td colspan="3" class="py-10 text-center text-xs text-slate-500">Nenhum ofensor encontrado no período.</td></tr>';
                            return;
                        }
                        tbody.innerHTML = topIps.map((item, index) => `<tr class="hover:bg-rose-500/[.04] transition-colors"><td class="py-3 px-3 font-mono text-sm text-slate-200"><span class="inline-flex w-6 text-xs text-slate-500">#${index + 1}</span>${item.ip}</td><td class="py-3 px-3 text-xs text-slate-400">${item.jails.length ? item.jails.join(', ') : 'Geral'}</td><td class="py-3 px-3 text-right"><span class="inline-flex min-w-10 justify-center px-2 py-1 rounded-lg bg-rose-500/10 text-rose-300 font-bold text-xs">${item.count}</span></td></tr>`).join('');
                    }

                    function updateJailFilter(jails) {
                        const select = document.getElementById('jail-filter');
                        const selected = select.value;
                        const names = jails.map(jail => jail.name);
                        select.innerHTML = '<option value="all">Todas as jails</option>' + names.map(name => `<option value="${name}">${name}</option>`).join('');
                        select.value = names.includes(selected) ? selected : 'all';
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

                            const period = document.getElementById('period-filter').value;
                            const jail = document.getElementById('jail-filter').value;
                            const response = await fetch(`/api/stats?period=${encodeURIComponent(period)}&jail=${encodeURIComponent(jail)}`);
                            const data = await response.json();
                            setConnectionStatus(true);
                            updateServiceHealth(data.health);

                            document.getElementById('total-count').innerText = data.banned.length;
                            document.getElementById('unbanned-count').innerText = data.unbanned.length;
                            document.getElementById('failure-count').innerText = data.failures.length;
                            document.getElementById('recent-bans').innerText = data.metrics.recent_bans;
                            document.getElementById('active-jails').innerText = data.metrics.active_jails;
                            document.getElementById('attack-rate').innerHTML = `${data.metrics.attack_rate}<span class="text-base font-semibold text-slate-400">/h</span>`;
                            updateJailFilter(data.jails || []);
                            updateCharts(data.charts);
                            updateTopIps(data.top_ips || []);

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
                    document.getElementById('period-filter').addEventListener('change', forceRefresh);
                    document.getElementById('jail-filter').addEventListener('change', forceRefresh);
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