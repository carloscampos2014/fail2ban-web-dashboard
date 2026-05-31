# 🛡️ Fail2Ban Web Dashboard

Uma dashboard minimalista, responsiva e em tempo real para monitoramento de segurança e tentativas de intrusão em servidores Linux protegidos pelo Fail2Ban.

## 🚀 Funcionalidades
- **Auto-refresh Inteligente:** Atualização em segundo plano (AJAX) a cada 5 segundos com contador regressivo.
- **Controle Manual:** Botão para forçar a sincronização instantânea dos logs.
- **Interface Organizada:** Layout em Abas (Tabs) separando IPs banidos de tentativas de falhas recentes.
- **Detalhamento de Logs:** Coluna com o log bruto explicativo do erro gerado pelo invasor.
- **Design Premium:** Desenvolvido com Tailwind CSS em modo escuro (Dark Mode) e scroll interno fixo.

## ⚙️ Arquitetura
O sistema funciona de forma leve rodando diretamente na VPS em Python nativo (utilizando o `http.server` para não precisar de dependências pesadas como Flask ou FastAPI) e exposto de forma segura para a máquina local através de um túnel SSH (`systemd --user`).
