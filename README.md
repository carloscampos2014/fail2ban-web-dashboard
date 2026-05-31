# 🛡️ Fail2Ban Web Dashboard

Uma solução de monitorização em tempo real, leve e responsiva, para visualizar tentativas de intrusão e o estado de banimento do **Fail2Ban** em servidores Linux.


## 🚀 O que é?

Este projeto fornece uma interface web moderna para acompanhar, minuto a minuto, quem está a tentar forçar o acesso ao teu servidor SSH. Esquece a necessidade de executar comandos complexos no terminal para verificar logs; aqui tens toda a informação de forma visual e intuitiva.


## ✨ Principais Funcionalidades

- **Auto-Refresh Inteligente:** Atualização automática em segundo plano a cada 5 segundos com contador regressivo visual.

- **Controlo Manual:** Botão "Recarregar" para sincronização instantânea dos dados.

- **Interface Dark Mode:** Desenvolvido com Tailwind CSS para uma experiência visual limpa, profissional e focada nos dados.

- **Detalhamento de Logs:** Visualização da mensagem bruta do log para cada tentativa de falha identificada.

- **Scroll Otimizado:** Tabelas com cabeçalho fixo e barra de rolagem dedicada para gerir grandes volumes de dados sem quebrar o layout.

- **Deployment como Serviço:** Integração nativa com `systemd` para garantir que o painel rode sempre em segundo plano.


## 🛠️ Tecnologias

- **Backend:** Python 3 (nativo, sem dependências externas adicionais).

- **Frontend:** HTML5, JavaScript (AJAX/Fetch) e Tailwind CSS (via CDN).

- **Integração:** `systemd` para gestão do processo em background.


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


## 🤝 Contribuições

Sente-te à vontade para abrir _Issues_ ou enviar _Pull Requests_ com melhorias.

Desenvolvido com foco em segurança, performance e simplicidade.
