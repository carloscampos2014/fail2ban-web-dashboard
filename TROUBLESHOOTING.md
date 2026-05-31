# 🔧 Guia de Troubleshooting - Fail2Ban Web Dashboard

## 📋 Índice Rápido

- [Problemas de Acesso](#problemas-de-acesso)
- [Dados Não Atualizam](#dados-não-atualizam)
- [Erros de Permissão](#erros-de-permissão)
- [Problemas de Performance](#problemas-de-performance)
- [Logs e Debugging](#logs-e-debugging)

---

## Problemas de Acesso

### "Conexão recusada" ou "Não consegue alcançar"

**Sintomas:**
```
refused to connect / ERR_CONNECTION_REFUSED
```

**Causas Possíveis:**

1. **Serviço não está a correr**
   ```bash
   sudo systemctl status fail2ban-webui
   ```
   
   **Solução:**
   ```bash
   sudo systemctl start fail2ban-webui
   sudo systemctl enable fail2ban-webui
   ```

2. **Porta errada ou em uso**
   ```bash
   sudo netstat -tlnp | grep 15000
   ```
   
   **Se porta está em uso:**
   ```bash
   sudo lsof -i :15000
   sudo kill -9 <PID>
   ```
   
   **Se quer usar porta diferente:**
   ```bash
   sudo systemctl stop fail2ban-webui
   sudo systemctl edit fail2ban-webui
   # Altere: ExecStart=/usr/bin/python3 app.py --port 12345
   sudo systemctl daemon-reload
   sudo systemctl start fail2ban-webui
   ```

3. **Firewall bloqueando**
   ```bash
   # Verificar iptables
   sudo iptables -L -n | grep 15000
   
   # Abrir porta
   sudo iptables -A INPUT -p tcp --dport 15000 -j ACCEPT
   sudo iptables-save > /etc/iptables/rules.v4
   ```

4. **Binding a interface errada**
   ```bash
   # Verificar onde está binding
   sudo netstat -tlnp | grep python
   
   # Se não mostra 127.0.0.1:15000, problema no app
   ```

---

## Dados Não Atualizam

### Contador regressivo funciona, mas dados não mudam

**Sintomas:**
- Dashboard carrega OK
- Botão refresh funciona visualmente
- Mas números não mudam
- Ou sempre mostra "0 banidos"

**Diagnóstico:**

1. **Verificar resposta da API**
   ```bash
   curl http://127.0.0.1:15000/api/stats | jq .
   ```
   
   - Se retorna `{"banned":[], "unbanned":[], "failures":[]}` → Ver logs
   - Se retorna dados → Problema no frontend JavaScript

2. **Verificar console do browser**
   - Abra DevTools (F12)
   - Aba "Console"
   - Procure por erros

3. **Verificar ficheiro de log**
   ```bash
   ls -la /var/log/fail2ban.log
   sudo tail -f /var/log/fail2ban.log
   ```
   
   - Se ficheiro não existe → Criar ou usar path correto
   - Se vazio → Fail2Ban não registou nada ainda

4. **Teste manual da leitura do log**
   ```bash
   sudo grep "Ban\|Unban\|Found" /var/log/fail2ban.log | head -5
   ```

### A API retorna dados mas frontend mostra 0

**Causa:** Erro no JavaScript

**Solução:**
1. Abra DevTools (F12)
2. Aba Network
3. Clique em refresh
4. Procure por `GET /api/stats`
5. Verifique se resposta é válido JSON
6. Verifique tab Console para erros

---

## Erros de Permissão

### "Permission denied" ao iniciar serviço

**Sintomas:**
```
ExecStart command returned code 13
```

**Causas:**

1. **Sem permissão para ler ficheiro de log**
   ```bash
   ls -la /var/log/fail2ban.log
   sudo chmod 644 /var/log/fail2ban.log
   ```

2. **Sem permissão na diretoria do projeto**
   ```bash
   ls -la /home/ubuntu/fail2ban-webui/
   sudo chown -R ubuntu:ubuntu /home/ubuntu/fail2ban-webui/
   ```

3. **Ficheiro de log não existe**
   ```bash
   # Se Fail2Ban ainda não criou o log
   sudo touch /var/log/fail2ban.log
   sudo chmod 644 /var/log/fail2ban.log
   ```

**Verificação Final:**
```bash
# Testar se consegue ler
sudo cat /var/log/fail2ban.log | head
```

---

## Problemas de Performance

### Dashboard muito lento ou congela

**Diagnóstico:**

1. **Verificar tamanho do log**
   ```bash
   du -sh /var/log/fail2ban.log
   wc -l /var/log/fail2ban.log
   ```
   
   - Se > 1GB → Arquivo muito grande, rotacionar
   - Se > 1 milhão linhas → Considerar limpeza

2. **Reduzir altura do container** (em `app.py`)
   ```html
   <!-- Altere de 700px para 500px -->
   <div class="max-h-[500px]">
   ```

3. **Aumentar intervalo de refresh**
   ```javascript
   // Altere de 5000 para 10000 (10 segundos)
   setInterval(updateDashboard, 10000)
   ```

4. **Monitorar recursos**
   ```bash
   top -p $(pgrep -f "python3.*app.py")
   ```

### Solução de Longo Prazo: Rotação de Logs

**Criar ficheiro `/etc/logrotate.d/fail2ban-webui`:**
```
/var/log/fail2ban.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
    sharedscripts
    postrotate
        /usr/lib/fail2ban/fail2ban-client set logtarget SYSLOG
    endscript
}
```

**Testar:**
```bash
sudo logrotate -f /etc/logrotate.d/fail2ban-webui
```

---

## Logs e Debugging

### Ver logs do serviço

**Logs em tempo real:**
```bash
sudo journalctl -u fail2ban-webui -f
```

**Últimas 50 linhas:**
```bash
sudo journalctl -u fail2ban-webui -n 50
```

**Desde a última boot:**
```bash
sudo journalctl -u fail2ban-webui -b
```

**Entre datas específicas:**
```bash
sudo journalctl -u fail2ban-webui --since "2026-05-31 10:00:00" --until "2026-05-31 11:00:00"
```

### Ativar debug output

**Método 1: Ver output direto**
```bash
# Parar serviço
sudo systemctl stop fail2ban-webui

# Correr com output visível
cd /home/ubuntu/fail2ban-webui
sudo python3 app.py --port 15000 --log /var/log/fail2ban.log

# Ctrl+C para parar
```

**Método 2: Ver logs de stdout**
```bash
sudo journalctl -u fail2ban-webui -n 100 | grep "IPs ATIVAMENTE"
```

---

## Checklist de Troubleshooting

Quando algo não funciona, verifique nesta ordem:

- [ ] Serviço está a correr? `sudo systemctl status fail2ban-webui`
- [ ] Porta está aberta? `sudo netstat -tlnp | grep 15000`
- [ ] Ficheiro de log existe? `ls -la /var/log/fail2ban.log`
- [ ] Ficheiro é legível? `sudo tail /var/log/fail2ban.log`
- [ ] API responde? `curl http://127.0.0.1:15000/api/stats`
- [ ] JSON é válido? `curl http://127.0.0.1:15000/api/stats | jq .`
- [ ] Console do browser mostra erros? F12 → Console
- [ ] Fail2Ban está ativo? `sudo systemctl status fail2ban`
- [ ] Há bans no log? `sudo grep "Ban" /var/log/fail2ban.log | head`

---

## Problemas Específicos

### "Unban 1.1.1.1" não aparece em IPs Liberados

**Causa:** IP nunca foi banido antes do unban

**Comportamento Esperado:** Se aparece "Unban" mas IP nunca teve "Ban", será ignorado

**Verificação:**
```bash
sudo grep "1.1.1.1" /var/log/fail2ban.log
```

**Solução:** Esperar por novo ciclo de Ban/Unban natural do Fail2Ban

---

### Mesmo IP aparece em ambas as listas

**Isto não deve acontecer.** Se ocorrer, é um bug.

**Reportar com:**
```bash
curl http://127.0.0.1:15000/api/stats | jq '.'
sudo grep -E "(Ban|Unban).*<IP>" /var/log/fail2ban.log
```

---

### "Histórico de Falhas" sempre mostra 100 itens

**Isto é Normal.** O sistema limita a 100 últimas falhas por performance.

**Para ver mais:**
```bash
sudo grep "Found" /var/log/fail2ban.log | wc -l
```

---

## Reinstalar / Reset Completo

Se tudo falhar:

```bash
# Parar serviço
sudo systemctl stop fail2ban-webui

# Remover ficheiros
rm -rf /home/ubuntu/fail2ban-webui

# Re-clonar
cd /home/ubuntu
git clone https://github.com/carloscampos2014/fail2ban-webui.git
cd fail2ban-webui

# Re-criar serviço
sudo cp fail2ban-webui.service /etc/systemd/system/

# Reiniciar
sudo systemctl daemon-reload
sudo systemctl start fail2ban-webui

# Verificar
sudo systemctl status fail2ban-webui
```

---

## Contato e Suporte

**Para reportar problemas:**

1. Recolha informações:
   ```bash
   sudo systemctl status fail2ban-webui
   sudo journalctl -u fail2ban-webui -n 20
   curl http://127.0.0.1:15000/api/stats | jq .
   python3 --version
   ```

2. Abra issue no GitHub com:
   - Erro específico (completo)
   - Passos para reproduzir
   - Output dos comandos acima

---

**Última Atualização:** Maio 2026 | **Versão:** 2.0
