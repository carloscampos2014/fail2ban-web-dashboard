import os
import re
import argparse
import json
from http.server import SimpleHTTPRequestHandler, HTTPServer

class Fail2BanHandler(SimpleHTTPRequestHandler):
    def get_fail2ban_stats(self):
        # Acede ao caminho do log que foi passado dinamicamente para o servidor
        log_path = self.server.log_path
        banned_ips = set()
        recent_failures = []

        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    # 1. Capturar os BANIMENTOS
                    if 'Ban' in line:
                        match = re.search(r'Ban\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
                        if match:
                            banned_ips.add(match.group(1))

                    # 2. Capturar as FALHAS
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

        return {
            "banned": sorted(list(banned_ips)),
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
                    ::-webkit-scrollbar { width: 6px; height: 6px; }
                    ::-webkit-scrollbar-track { background: #020617; }
                    ::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
                    ::-webkit-scrollbar-thumb:hover { background: #475569; }
                    .spin-once { animation: spin 0.6s ease-in-out; }
                    @keyframes spin { 100% { transform: rotate(360deg); } }
                </style>
            </head>
            <body class="bg-slate-900 text-slate-100 font-sans min-h-screen">
                <div class="max-w-5xl mx-auto px-4 py-8">

                    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-slate-800 pb-6 mb-8 gap-4">
                        <div>
                            <h1 class="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
                                <span class="text-red-500">🛡️</span> Fail2Ban Dashboard
                            </h1>
                            <p class="text-slate-400 text-sm mt-1">Monitoramento de segurança da VPS em tempo real</p>
                        </div>

                        <div class="flex items-center gap-3 bg-slate-800/80 p-2 px-3 rounded-lg border border-slate-700 w-fit self-end sm:self-auto">
                            <div class="flex items-center gap-2 text-xs text-slate-300 border-r border-slate-700 pr-3">
                                <span class="relative flex h-2 w-2">
                                    <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                                    <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                                </span>
                                <span>Atualizando em: <b id="countdown-text" class="text-emerald-400 font-mono text-sm">5s</b></span>
                            </div>

                            <button id="btn-refresh" onclick="forceRefresh()" class="flex items-center justify-center p-1.5 rounded-md bg-slate-700 hover:bg-slate-600 active:scale-95 text-slate-200 hover:text-white transition-all focus:outline-none" title="Recarregar agora">
                                <svg id="svg-refresh" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.253 8H18"></path>
                                </svg>
                            </button>
                        </div>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                        <div class="bg-gradient-to-br from-slate-800 to-slate-900 p-6 rounded-xl border border-slate-800 shadow-xl">
                            <p class="text-sm font-medium text-slate-400 uppercase tracking-wider">IPs Banidos Atualmente</p>
                            <p id="total-count" class="text-4xl font-extrabold text-red-400 mt-2">0</p>
                        </div>

                        <div class="bg-gradient-to-br from-slate-800 to-slate-900 p-6 rounded-xl border border-slate-800 shadow-xl">
                            <p class="text-sm font-medium text-slate-400 uppercase tracking-wider">Total de Falhas / Tentativas</p>
                            <p id="failure-count" class="text-4xl font-extrabold text-amber-400 mt-2">0</p>
                        </div>
                    </div>

                    <div class="border-b border-slate-800 mb-6">
                        <nav class="flex space-x-8" aria-label="Tabs">
                            <button id="tab-banned" onclick="switchTab('banned')" class="border-b-2 border-red-500 text-red-400 px-1 pb-4 text-sm font-medium tracking-wide flex items-center gap-2 focus:outline-none">
                                <span>❌</span> IPs Banidos
                            </button>
                            <button id="tab-failures" onclick="switchTab('failures')" class="border-b-2 border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-300 px-1 pb-4 text-sm font-medium tracking-wide flex items-center gap-2 focus:outline-none">
                                <span>⚠️</span> Histórico de Falhas Detalhado
                            </button>
                        </nav>
                    </div>

                    <div class="bg-slate-950 rounded-xl border border-slate-800 shadow-2xl h-[480px] overflow-y-auto">

                        <div id="panel-banned" class="block">
                            <div class="sticky top-0 bg-slate-950 border-b border-slate-800 px-6 py-4 z-10">
                                <input type="text" id="search-ip" placeholder="🔍 Pesquisar IP..." class="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500 transition-all text-sm" />
                            </div>
                            <div class="overflow-x-auto">
                                <table class="w-full text-left border-collapse">
                                    <thead class="sticky top-[56px] bg-slate-950 shadow-md">
                                        <tr class="border-b border-slate-800 text-slate-400 text-xs uppercase tracking-wider bg-slate-900/40">
                                            <th class="py-3.5 px-6 font-semibold">Endereço IP</th>
                                            <th class="py-3.5 px-6 font-semibold">Status</th>
                                        </tr>
                                    </thead>
                                    <tbody id="ip-table-body" class="divide-y divide-slate-800/60 text-sm"></tbody>
                                </table>
                            </div>
                        </div>

                        <div id="panel-failures" class="hidden">
                            <div class="overflow-x-auto">
                                <table class="w-full text-left border-collapse">
                                    <thead class="sticky top-0 bg-slate-950 shadow-md">
                                        <tr class="border-b border-slate-800 text-slate-400 text-xs uppercase tracking-wider bg-slate-900/40">
                                            <th class="py-3.5 px-4 font-semibold">Horário</th>
                                            <th class="py-3.5 px-4 font-semibold">Alvo (Jail)</th>
                                            <th class="py-3.5 px-4 font-semibold">IP Origem</th>
                                            <th class="py-3.5 px-4 font-semibold">Registro do Log (Detalhamento)</th>
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

                    function filterIPs() {
                        const searchInput = document.getElementById('search-ip');
                        const searchValue = searchInput.value.toLowerCase().trim();
                        const tbodyBanned = document.getElementById('ip-table-body');

                        if (searchValue === '') {
                            // Reconstrói a tabela com todos os IPs quando o campo está vazio
                            if (allBannedIps.length === 0) {
                                tbodyBanned.innerHTML = `<tr><td colspan="2" class="py-8 text-center text-slate-500 italic">Nenhum IP banido encontrado.</td></tr>`;
                            } else {
                                tbodyBanned.innerHTML = allBannedIps.map(ip => `
                                    <tr class="hover:bg-slate-900/40 transition-colors">
                                        <td class="py-3.5 px-6 font-mono text-slate-200 font-medium">${ip}</td>
                                        <td class="py-3.5 px-6">
                                            <span class="inline-flex items-center px-2.5 py-0.5 rounded text-xs font-semibold bg-red-500/10 text-red-400 border border-red-500/20">BANNED</span>
                                        </td>
                                    </tr>
                                `).join('');
                            }
                            return;
                        }

                        const rows = tbodyBanned.querySelectorAll('tr');
                        let visibleCount = 0;
                        rows.forEach(row => {
                            const ipCell = row.querySelector('td');
                            if (ipCell) {
                                const ip = ipCell.textContent.trim();
                                if (ip.includes(searchValue)) {
                                    row.style.display = '';
                                    visibleCount++;
                                } else {
                                    row.style.display = 'none';
                                }
                            }
                        });

                        if (visibleCount === 0 && allBannedIps.length > 0) {
                            tbodyBanned.innerHTML = `<tr><td colspan="2" class="py-8 text-center text-slate-500 italic">Nenhum IP encontrado para "${searchValue}"</td></tr>`;
                        }
                    }

                    function switchTab(tab) {
                        const tabBanned = document.getElementById('tab-banned');
                        const tabFailures = document.getElementById('tab-failures');
                        const panelBanned = document.getElementById('panel-banned');
                        const panelFailures = document.getElementById('panel-failures');

                        if (tab === 'banned') {
                            tabBanned.className = "border-b-2 border-red-500 text-red-400 px-1 pb-4 text-sm font-medium tracking-wide flex items-center gap-2 focus:outline-none";
                            tabFailures.className = "border-b-2 border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-300 px-1 pb-4 text-sm font-medium tracking-wide flex items-center gap-2 focus:outline-none";
                            panelBanned.classList.remove('hidden');
                            panelFailures.classList.add('hidden');
                        } else {
                            tabFailures.className = "border-b-2 border-amber-500 text-amber-400 px-1 pb-4 text-sm font-medium tracking-wide flex items-center gap-2 focus:outline-none";
                            tabBanned.className = "border-b-2 border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-300 px-1 pb-4 text-sm font-medium tracking-wide flex items-center gap-2 focus:outline-none";
                            panelFailures.classList.remove('hidden');
                            panelBanned.classList.add('hidden');
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

                    async function updateDashboard() {
                        try {
                            // Salva o texto de pesquisa antes de atualizar
                            const searchInput = document.getElementById('search-ip');
                            const savedSearchValue = searchInput.value;

                            const response = await fetch('/api/stats');
                            const data = await response.json();

                            document.getElementById('total-count').innerText = data.banned.length;
                            document.getElementById('failure-count').innerText = data.failures.length;

                            const tbodyBanned = document.getElementById('ip-table-body');
                            allBannedIps = data.banned;
                            if (data.banned.length === 0) {
                                tbodyBanned.innerHTML = `<tr><td colspan="2" class="py-8 text-center text-slate-500 italic">Nenhum IP banido encontrado.</td></tr>`;
                            } else {
                                tbodyBanned.innerHTML = data.banned.map(ip => `
                                    <tr class="hover:bg-slate-900/40 transition-colors">
                                        <td class="py-3.5 px-6 font-mono text-slate-200 font-medium">${ip}</td>
                                        <td class="py-3.5 px-6">
                                            <span class="inline-flex items-center px-2.5 py-0.5 rounded text-xs font-semibold bg-red-500/10 text-red-400 border border-red-500/20">BANNED</span>
                                        </td>
                                    </tr>
                                `).join('');
                                // Restaura o texto de pesquisa e reaplica o filtro
                                searchInput.value = savedSearchValue;
                                filterIPs();
                            }

                            const tbodyFailures = document.getElementById('failure-table-body');
                            if (data.failures.length === 0) {
                                tbodyFailures.innerHTML = `<tr><td colspan="4" class="py-8 text-center text-slate-500 italic">Nenhuma falha detectada recentemente.</td></tr>`;
                            } else {
                                tbodyFailures.innerHTML = data.failures.map(f => `
                                    <tr class="hover:bg-slate-900/40 transition-colors">
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
                            console.error("Erro na atualização automática:", error);
                        }
                    }

                    updateDashboard();
                    startCountdown();

                    document.getElementById('search-ip').addEventListener('input', filterIPs);
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_error(404, "Not Found")

if __name__ == '__main__':
    # Configuração dos argumentos da aplicação CLI (Adeus hardcode!)
    parser = argparse.ArgumentParser(description="Fail2Ban Monitor Web Dashboard")
    parser.add_argument('--port', type=int, default=15000, help="Porta para o servidor web (Padrão: 15000)")
    parser.add_argument('--log', type=str, default='/var/log/fail2ban.log', help="Caminho do ficheiro de log do Fail2Ban")
    args = parser.parse_args()

    print(f"Iniciando painel Fail2Ban na porta {args.port}...")
    print(f"Monitorando o arquivo: {args.log}")

    # Inicializa o servidor e injeta o caminho do log para ser acessado pelo Handler
    server = HTTPServer(('127.0.0.1', args.port), Fail2BanHandler)
    server.log_path = args.log

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\\nServidor encerrado pelo utilizador.")
