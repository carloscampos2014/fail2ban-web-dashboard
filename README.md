# 🛡️ Fail2Ban Web Dashboard

Uma solução de monitorização em tempo real, leve e responsiva, para visualizar tentativas de intrusão e o estado de banimento do **Fail2Ban** em servidores Linux.


## 🚀 O que é?

Este projeto fornece uma interface web moderna para acompanhar, minuto a minuto, quem está a tentar forçar o acesso ao teu servidor SSH. Esquece a necessidade de executar comandos complexos no terminal para verificar logs; aqui tens toda a informação de forma visual e intuitiva.

**Novo na versão 2.0:** Rastreamento completo do ciclo de vida dos IPs com histórico de liberações!


## ✨ Principais Funcionalidades

- **Auto-Refresh Inteligente:** Atualização automática em segundo plano a cada 5 segundos com contador regressivo visual.

- **Controlo Manual:** Botão "Recarregar" para sincronização instantânea dos dados.

- **Interface Dark Mode:** Desenvolvido com Tailwind CSS para uma experiência visual limpa, profissional e focada nos dados.

- **Rastreamento Duplo de IPs:** 
  - Visualização de IPs **atualmente banidos**
  - Histórico de IPs **liberados** (unbanned)
  - Sincronização automática quando um IP passa entre estados

- **Dashboard com Métricas em Tempo Real:**
  - Total de IPs banidos atualmente
  - Total de IPs liberados únicos
  - Total de tentativas de falha registradas

- **Abas Navegáveis:**
  - **IPs Banidos:** Lista de endereços atualmente bloqueados
  - **IPs Liberados:** Histórico de IPs que foram desbloqueados
  - **Histórico de Falhas:** Detalhamento completo com timestamps, jails e logs

- **Contadores Dinâmicos:** Indicador "Exibindo: X/Y" em cada aba mostrando a quantidade de registos

- **Pesquisa em Tempo Real:** Filtro de IPs em cada aba para localização rápida

- **Detalhamento de Logs:** Visualização da mensagem bruta do log para cada tentativa de falha identificada com hover tooltip.

- **Interface Responsiva:** Layout adaptável para diferentes tamanhos de tela.

- **Scroll Otimizado:** Tabelas com cabeçalho fixo e barra de rolagem dedicada para gerir grandes volumes de dados (até 700px de altura) sem quebrar o layout.

- **Deployment como Serviço:** Integração nativa com `systemd` para garantir que o painel rode sempre em segundo plano.


## 🛠️ Tecnologias

- **Backend:** Python 3 (nativo, sem dependências externas adicionais).

- **Frontend:** HTML5, JavaScript (AJAX/Fetch) e Tailwind CSS (via CDN).

- **Integração:** `systemd` para gestão do processo em background.


## 📊 Arquitetura & Fluxo de Dados

### Backend (Python)
```
Log do Fail2Ban → Parser de Logs → Análise de Estados (Ban/Unban)
                                          ↓
                            Sincronização de Status de IPs
                                          ↓
                        JSON API (/api/stats) com:
                        - Lista de IPs Banidos
                        - Lista de IPs Liberados
                        - Últimas 100 Falhas
```

### Frontend (JavaScript + HTML)
```
Dashboard com 3 Métricas de Topo
           ↓
    3 Abas Navegáveis:
    ├─ IPs Banidos (com busca)
    ├─ IPs Liberados (com busca)
    └─ Histórico de Falhas (com timestamps)
           ↓
    Auto-refresh a cada 5s (com contador visual)
```

## 🔍 Funcionalidades Detalhadas

### 1. Rastreamento Inteligente de IPs
O sistema mantém dois registos separados e sincronizados:

- **Banidos:** IPs com ação "Ban" e que não têm "Unban" posterior
- **Liberados:** IPs com ação "Unban" registada (histórico completo)

Quando um IP é desbloqueado, é automaticamente removido da lista de banidos e adicionado ao histórico de liberados.

### 2. Três Métricas Principais
Exibidas em cards coloridos no topo:
- 🔴 **IPs Banidos Atualmente** (vermelho)
- 🟢 **IPs Liberados Únicos** (verde)
- 🟠 **Total de Falhas / Tentativas** (âmbar)

### 3. Abas de Navegação

#### IPs Banidos
- Lista de todos os IPs atualmente bloqueados
- Ordenados alfabeticamente
- Busca em tempo real
- Contador "Exibindo: X/Y"
- Status badge "BANNED"

#### IPs Liberados
- Histórico completo de IPs desbloqueados
- Permite analisar padrões de reincidência
- Busca em tempo real
- Status badge "UNBANNED / UNLOCKED"

#### Histórico de Falhas
- Últimas 100 tentativas de intrusão
- 4 colunas: Horário | Alvo (Jail) | IP Origem | Detalhes do Log
- Timestamps precisos (hora:minuto:segundo)
- Identificação de qual "jail" foi alvo do ataque
- Detalhe completo do registro com hover tooltip


## ⚙️ Instalação Rápida

1. **Clonar o repositório:**

       git clone [https://github.com/carloscampos2014/fail2ban-web-dashboard.git](https://github.com/carloscampos2014/fail2ban-web-dashboard.git)
       cd fail2ban-web-dashboard

2. **Configurar como serviço (Systemd):**

   Cria o ficheiro `/etc/systemd/system/fail2ban-webui.service`:

       [Unit]
       Description=Interface Web Customizada para o Fail2Ban
       After=network.target fail2ban.service

       [Service]
       Type=simple
       User=root
       WorkingDirectory=/caminho/do/seu/projeto
       ExecStart=/usr/bin/python3 app.py --port 15000 --log /var/log/fail2ban.log
       Restart=always
       RestartSec=5

       [Install]
       WantedBy=multi-user.target

3. **Iniciar o serviço:**

       sudo systemctl daemon-reload
       sudo systemctl enable --now fail2ban-webui.service


## 🔐 Requisitos

- Fail2Ban instalado e ativo no servidor.
- Python 3 instalado.
- Acesso ao ficheiro de log do Fail2Ban (normalmente `/var/log/fail2ban.log`)


## 📖 Guia de Utilização

### Aceder ao Dashboard
Após iniciar o serviço, aceda a:
```
http://127.0.0.1:15000
```

### Atualizar Dados Manualmente
Clique no botão 🔄 no canto superior direito para sincronizar os dados imediatamente.

### Pesquisar um IP Específico
1. Navegue até à aba desejada (IPs Banidos, Liberados ou Falhas)
2. Use o campo de pesquisa para filtrar (ex: "192.168.1.")
3. A tabela é filtrada em tempo real

### Interpretar os Dados

**Status Badges:**
- 🔴 `BANNED` - IP atualmente bloqueado
- 🟢 `UNBANNED / UNLOCKED` - IP que foi desbloqueado anteriormente

**Cores das Métricas:**
- Vermelho: IPs em risco (banidos)
- Verde: Situações resolvidas (liberados)
- Âmbar: Alertas (tentativas de falha)

**Jails Comuns:**
- `sshd` - Tentativas de SSH
- `recidive` - Reincidentes (múltiplas jails)
- `nginx-http-auth` - Falhas de autenticação HTTP
- `postfix` - Tentativas SMTP


## 🚨 Troubleshooting

### O dashboard não carrega
- Verifique se o serviço está a correr: `sudo systemctl status fail2ban-webui`
- Verifique a porta: `sudo netstat -tlnp | grep 15000`

### Os dados não atualizam
- Confirme que o Fail2Ban está ativo: `sudo systemctl status fail2ban`
- Verifique o caminho do log: `ls -la /var/log/fail2ban.log`
- Consulte os logs do serviço: `sudo journalctl -u fail2ban-webui -n 50`

### Permissões negadas
- O serviço precisa acesso ao log do Fail2Ban
- Execute com: `sudo systemctl restart fail2ban-webui`

### Muitos dados / Performance lenta
- O dashboard limita a 100 últimas falhas por padrão
- Rolagem é otimizada; se ainda estiver lenta, reduza `max-h-[700px]` no HTML

## 📈 Versão & Changelog

### v2.0 (Atual)
- ✅ Rastreamento de IPs liberados (unbanned)
- ✅ Dashboard com 3 métricas principais
- ✅ Contadores dinâmicos "Exibindo: X/Y"
- ✅ Abas navegáveis para melhor organização
- ✅ Interface expandida (700px vs 480px anterior)
- ✅ Sincronização automática de estados (ban/unban)

### v1.0
- Monitorização básica de IPs banidos
- Histórico de falhas
- Auto-refresh

## 🎯 Melhorias Futuras

- [ ] Exportar dados em CSV
- [ ] Gráficos de tendências
- [ ] Alertas via email/webhook
- [ ] Autenticação de painel
- [ ] Dark/Light mode toggle
- [ ] API de desbloqueio remoto
- [ ] Suporte para múltiplos servidores
- [ ] Whitelist de IPs confiáveis

## 🤝 Contribuições

Sente-te à vontade para abrir _Issues_ ou enviar _Pull Requests_ com melhorias.

## 📝 Licença

Este projeto está disponível sob licença MIT.

## 👨‍💻 Desenvolvedor

Desenvolvido com foco em segurança, performance e simplicidade.

---

**Última atualização:** Maio 2026 | **Versão:** 2.0
