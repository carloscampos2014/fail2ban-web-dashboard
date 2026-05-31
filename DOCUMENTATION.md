# 📚 Documentação Técnica Completa - Fail2Ban Web Dashboard

## Índice
1. [Arquitetura](#arquitetura)
2. [API Endpoints](#api-endpoints)
3. [Parsing de Logs](#parsing-de-logs)
4. [Frontend](#frontend)
5. [Configuração Avançada](#configuração-avançada)
6. [Exemplos de Uso](#exemplos-de-uso)

---

## Arquitetura

### Visão Geral do Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    FAIL2BAN WEB DASHBOARD                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────┐         ┌──────────────────────┐ │
│  │   BROWSER (Client)   │◄────────►│  Python HTTP Server  │ │
│  │  - Dashboard HTML    │  AJAX    │   (Porta 15000)      │ │
│  │  - Fetch API         │  Requests│                      │ │
│  │  - Real-time Updates │          │  - SimpleHTTPServer  │ │
│  └──────────────────────┘          │  - Regex Parser      │ │
│                                     └──────────────────────┘ │
│                                              │               │
│                                              │ Lê            │
│                                              ▼               │
│                                   ┌──────────────────────┐  │
│                                   │ /var/log/fail2ban.log│  │
│                                   │                      │  │
│                                   │  - Ban Events        │  │
│                                   │  - Unban Events      │  │
│                                   │  - Found Attempts    │  │
│                                   └──────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Fluxo de Dados

1. **Requisição do Cliente**
   - Browser faz fetch para `/api/stats`
   - A cada 5 segundos (ou manual via botão)

2. **Processamento no Servidor**
   - Lê ficheiro de log completo
   - Parse com regex de eventos Ban/Unban/Found
   - Sincroniza estado (remove IP de banidos se foi unbanned)
   - Retorna JSON com listas organizadas

3. **Resposta da API**
   ```json
   {
     "banned": ["1.2.3.4", "5.6.7.8", ...],
     "unbanned": ["10.11.12.13", ...],
     "failures": [
       {
         "time": "2026-05-31 18:27:53",
         "jail": "sshd",
         "ip": "192.168.1.100",
         "detail": "..."
       }
     ]
   }
   ```

4. **Atualização da UI**
   - Atualiza contadores
   - Reconstrói tabelas
   - Preserva filtros de pesquisa

---

## API Endpoints

### GET /
Retorna o dashboard HTML completo.

**Resposta:** `text/html` com a interface web

---

### GET /api/stats
Retorna estatísticas atualizadas em JSON.

**Resposta:**
```json
{
  "banned": [
    "101.47.155.9",
    "101.96.203.52",
    "103.158.40.65"
  ],
  "unbanned": [
    "1.1.1.1",
    "78.73.8.212"
  ],
  "failures": [
    {
      "time": "2026-05-31 18:27:53",
      "jail": "sshd",
      "ip": "192.168.1.100",
      "detail": "Failed password for root from 192.168.1.100 port 54321 ssh2"
    }
  ]
}
```

**Parâmetros:** Nenhum

**Status Codes:**
- `200` - Sucesso
- `404` - Endpoint não encontrado

---

## Parsing de Logs

### Regex Patterns Utilizadas

#### 1. Unban Events
```regex
Unban\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})
```

**Exemplo de linha:**
```
2026-05-31 18:27:53,123 fail2ban.actions    [5612]: INFO    [sshd] Unban 192.168.1.100
```

**Resultado:**
- IP extraído: `192.168.1.100`
- Ação: Remove de `banned_ips` se presente, adiciona a `unbanned_ips`

---

#### 2. Ban Events
```regex
\bBan\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})
```

**Exemplo de linha:**
```
2026-05-31 18:27:53,456 fail2ban.actions    [5612]: INFO    [sshd] Ban 192.168.1.100
```

**Resultado:**
- IP extraído: `192.168.1.100`
- Ação: Adiciona a `banned_ips`, remove de `unbanned_ips` se presente

---

#### 3. Found (Failure) Events
```regex
^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})   # Timestamp
\[(.*?)\]\s+Found                         # Jail
Found\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})  # IP
```

**Exemplo de linha:**
```
2026-05-31 18:27:53,789 fail2ban.filter   [5612]: INFO    [sshd] Found 192.168.1.100 - 2026-05-31 18:27:53
```

**Resultado:**
- Timestamp: `2026-05-31 18:27:53`
- Jail: `sshd`
- IP: `192.168.1.100`
- Detalhe: Linha completa do log (sem INFO prefix)

---

### Ordem de Processamento

O parser processa nesta ordem para evitar conflitos:

1. **Unbans primeiro** - Remove IPs do estado de banido
2. **Bans depois** - Adiciona novos IPs banidos
3. **Found por fim** - Registra as tentativas

Isto garante que a sincronização de estados seja sempre correta.

---

## Frontend

### Arquitetura JavaScript

```javascript
// Global State
let timeLeft = 5;                    // Contador regressivo
let countdownInterval;               // Timer
let allBannedIps = [];               // Cache local
let allUnbannedIps = [];             // Cache local

// Core Functions
updateDashboard()                    // Fetch API + atualiza UI
buildBannedTable()                   // Renderiza tabela de banidos
buildUnbannedTable()                 // Renderiza tabela de liberados
switchTab(tab)                       // Alterna entre abas
filterIPs()                          // Busca em tempo real
startCountdown()                     // Timer de refresh
forceRefresh()                       // Manual refresh
```

### Ciclo de Atualização

```
setInterval(updateDashboard, 5000)
        │
        ▼
fetch('/api/stats')
        │
        ├─► Atualiza contadores no topo
        ├─► Atualiza allBannedIps
        ├─► Atualiza allUnbannedIps
        │
        ▼
buildBannedTable()
buildUnbannedTable()
        │
        ├─► Constrói HTML novo
        ├─► Preserva filtros de pesquisa
        │
        ▼
UI Atualizada Visualmente
```

### Componentes da Interface

#### Dashboard Header
- Título e descrição
- Contador regressivo (5s)
- Botão de refresh manual

#### Métricas (3 Cards)
```
┌─────────────────────┬─────────────────────┬─────────────────────┐
│ IPs Banidos         │ IPs Liberados       │ Total de Falhas     │
│ (Vermelho)          │ (Verde)             │ (Âmbar)             │
│ 58                  │ 2                   │ 100                 │
└─────────────────────┴─────────────────────┴─────────────────────┘
```

#### Abas e Painéis
- **Aba Banidos:** Tabela com IP | Status
- **Aba Liberados:** Tabela com IP | Status
- **Aba Falhas:** Tabela com Hora | Jail | IP | Detalhe

#### Tabelas
- Cabeçalho fixo (sticky)
- Linhas com hover effect
- Scroll vertical interno (max-h-[700px])
- Contadores "Exibindo: X/Y"

---

## Configuração Avançada

### Parâmetros de Linha de Comando

```bash
python3 app.py --port 15000 --log /var/log/fail2ban.log
```

| Parâmetro | Padrão | Descrição |
|-----------|--------|-----------|
| `--port` | 15000 | Porta do servidor web |
| `--log` | /var/log/fail2ban.log | Caminho do ficheiro de log |

### Configuração do Systemd

**Ficheiro:** `/etc/systemd/system/fail2ban-webui.service`

```ini
[Unit]
Description=Interface Web Customizada para o Fail2Ban
After=network.target fail2ban.service

[Service]
Type=simple
User=root
WorkingDirectory=/home/ubuntu/fail2ban-webui
ExecStart=/usr/bin/python3 app.py --port 15000 --log /var/log/fail2ban.log
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Comandos Úteis:**
```bash
# Recarregar configurações
sudo systemctl daemon-reload

# Iniciar
sudo systemctl start fail2ban-webui

# Ativar on-boot
sudo systemctl enable fail2ban-webui

# Ver logs
sudo journalctl -u fail2ban-webui -f

# Parar
sudo systemctl stop fail2ban-webui
```

### Personalização da Interface

#### Cores
Dentro do `<style>` ou classes Tailwind:

```css
/* Mudar cor de scroll */
::-webkit-scrollbar-thumb { background: #334155; }

/* Mudar cores dos badges */
.bg-red-500/10  /* Fundo do BANNED */
.text-red-400   /* Texto do BANNED */
```

#### Tempos
No JavaScript:

```javascript
// Alterar intervalo de refresh
setInterval(updateDashboard, 5000)  // Mude 5000 para ms desejados

// Alterar tempo do countdown
}, 1000);  // Atualmente em segundos
```

#### Altura da Tabela
Na div principal:

```html
<div class="max-h-[700px]">  <!-- Altere 700px -->
```

---

## Exemplos de Uso

### Cenário 1: Monitorar Servidor SSH

**Setup:**
```bash
sudo systemctl start fail2ban
sudo systemctl start fail2ban-webui
curl http://127.0.0.1:15000
```

**Observar:**
1. Tentativas falhadas aparecem em "Histórico de Falhas"
2. Após X falhas, IP aparece em "IPs Banidos"
3. Quando ban expira, IP move para "IPs Liberados"

---

### Cenário 2: Analisar Reincidência

**Procedimento:**
1. Abra aba "IPs Liberados"
2. Procure por IPs que aparecem frequentemente em "Histórico de Falhas"
3. Estes são atacantes reincidentes (podem estar em jail "recidive")

---

### Cenário 3: Pesquisar Range de IPs

**Pesquisa:**
- Digite `192.168.` na barra de pesquisa
- Filtra todos os IPs desse range

---

### Cenário 4: Monitorar Múltiplas Jails

**Na aba de Falhas:**
- Veja a coluna "Alvo (Jail)"
- Identificar qual serviço está sendo atacado:
  - `sshd` = SSH
  - `nginx-http-auth` = HTTP
  - `postfix` = SMTP
  - `recidive` = Reincidentes em múltiplas jails

---

## Debugging

### Ativar Modo Verbose

Edite `app.py` e procure por `print()`:

```python
# Já ativa prints de debug automáticos no console
print("\n================ [DEBUG MEMÓRIA FAIL2BAN] ================")
print(f"-> IPs ATIVAMENTE BANIDOS ({len(lista_banidos)}): {lista_banidos}")
print(f"-> HISTÓRICO DE LIBERADOS ({len(lista_liberados)}): {lista_liberados}")
```

**Ver logs:**
```bash
sudo journalctl -u fail2ban-webui -n 50
```

### Verificar Parser

**Teste manual:**
```python
import re

# Simular linha de log
line = "2026-05-31 18:27:53,123 fail2ban.actions [5612]: INFO [sshd] Ban 192.168.1.100"

# Testar regex
match = re.search(r'\bBan\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
if match:
    print(f"IP encontrado: {match.group(1)}")
```

---

## Performance

### Otimizações Implementadas

| Otimização | Detalhes |
|------------|----------|
| Sets para IPs | Evita duplicatas e permite operações rápidas |
| Regex pré-compiladas | Matching eficiente |
| Fetch AJAX | Carrega apenas dados, não HTML completo |
| Scroll nativo | Sem bibliotecas externas |
| Cache local | `allBannedIps` e `allUnbannedIps` |

### Capacidade

- ✅ Até 10,000 IPs banidos - rápido
- ✅ Até 100 últimas falhas - excelente performance
- ✅ Ficheiros de log até 100MB - sem problemas
- ⚠️ Além disso, considere arquivar logs antigos

---

## Troubleshooting Técnico

### Log não encontrado
```bash
sudo find / -name "*fail2ban*" -type f 2>/dev/null
```

### Permissões do ficheiro
```bash
ls -la /var/log/fail2ban.log
sudo chmod 644 /var/log/fail2ban.log
```

### Processo não inicia
```bash
python3 /home/ubuntu/fail2ban-webui/app.py --port 15000
# Veja erro direct
```

### Porta já em uso
```bash
sudo lsof -i :15000
sudo kill -9 <PID>
```

---

## Roadmap Futuro

- [ ] Suporte para múltiplos ficheiros de log
- [ ] Banco de dados para histórico persistente
- [ ] Alertas em tempo real via WebSocket
- [ ] Estatísticas e gráficos
- [ ] Integração com APIs (Telegram, Discord)
- [ ] Whitelist automática
- [ ] Geolocalização de IPs

---

**Última Atualização:** Maio 2026 | **Versão:** 2.0
