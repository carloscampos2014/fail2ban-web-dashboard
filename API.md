# 📡 API Reference - Fail2Ban Web Dashboard

## Visão Geral

O Fail2Ban Web Dashboard expõe dois endpoints HTTP:

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/` | GET | Retorna dashboard HTML |
| `/api/stats` | GET | Retorna estatísticas em JSON |

---

## Endpoint: GET /

### Descrição
Retorna a interface web completa do dashboard.

### URL
```
GET http://127.0.0.1:15000/
```

### Parâmetros
Nenhum

### Resposta

**Status Code:** `200 OK`

**Content-Type:** `text/html; charset=utf-8`

**Body:** HTML completo com:
- Dashboard estruturado
- Estilos Tailwind CSS (via CDN)
- JavaScript embarcado para interatividade
- Componentes responsivos

### Exemplo de Requisição
```bash
curl http://127.0.0.1:15000/
```

### Exemplo de Resposta
```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Fail2Ban Monitor</title>
    ...
</head>
<body>
    ...
</body>
</html>
```

---

## Endpoint: GET /api/stats

### Descrição
Retorna as estatísticas atuais do Fail2Ban em formato JSON. É o endpoint utilizado pelo dashboard para atualizar os dados em tempo real a cada 5 segundos.

### URL
```
GET http://127.0.0.1:15000/api/stats
```

### Parâmetros
Nenhum

### Resposta

**Status Code:** `200 OK`

**Content-Type:** `application/json`

### Estrutura JSON

```json
{
  "banned": [
    "string",
    "string",
    ...
  ],
  "unbanned": [
    "string",
    "string",
    ...
  ],
  "failures": [
    {
      "time": "string",
      "jail": "string",
      "ip": "string",
      "detail": "string"
    },
    ...
  ]
}
```

### Descrição dos Campos

#### `banned` (Array de Strings)
- **Tipo:** Array
- **Conteúdo:** Lista de endereços IP atualmente banidos
- **Ordem:** Alfabética (ascendente)
- **Exemplo:**
  ```json
  "banned": [
    "101.47.155.9",
    "103.158.40.65",
    "107.150.103.12"
  ]
  ```

#### `unbanned` (Array de Strings)
- **Tipo:** Array
- **Conteúdo:** Histórico de endereços IP que foram desbloqueados
- **Ordem:** Alfabética (ascendente)
- **Nota:** Quando um IP é desbloqueado, é removido de `banned` e adicionado a `unbanned`
- **Exemplo:**
  ```json
  "unbanned": [
    "1.1.1.1",
    "78.73.8.212"
  ]
  ```

#### `failures` (Array de Objetos)
- **Tipo:** Array
- **Conteúdo:** Últimas até 100 tentativas de intrusão registadas
- **Ordem:** Cronológica reversa (mais recentes primeiro)
- **Limite:** Máximo 100 registos por requisição

#### `failures[].time` (String)
- **Formato:** `YYYY-MM-DD HH:MM:SS`
- **Exemplo:** `"2026-05-31 18:27:53"`
- **Nota:** Parsing pode falhar se formato diferente no log original

#### `failures[].jail` (String)
- **Descrição:** Nome do "jail" do Fail2Ban que detectou o evento
- **Valores Comuns:**
  - `sshd` - SSH
  - `nginx-http-auth` - Autenticação HTTP Nginx
  - `postfix` - SMTP Postfix
  - `recidive` - Reincidentes (múltiplas jails)
  - `apache-auth` - Autenticação Apache
  - Customizados pelo utilizador
- **Fallback:** `"Geral"` se não detectado
- **Exemplo:** `"sshd"`

#### `failures[].ip` (String)
- **Tipo:** IPv4 (padrão x.x.x.x)
- **Formato:** `\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}`
- **Exemplo:** `"192.168.1.100"`

#### `failures[].detail` (String)
- **Descrição:** Mensagem completa do log associada ao evento
- **Conteúdo:** Informações específicas da tentativa (usuário, porta, etc.)
- **Processamento:** Remove prefixo "INFO" se presente
- **Exemplo:** `"Failed password for root from 192.168.1.100 port 54321 ssh2"`

### Exemplo de Resposta Completa

```json
{
  "banned": [
    "101.47.155.9",
    "101.96.203.52",
    "103.158.40.65",
    "103.237.144.204"
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
    },
    {
      "time": "2026-05-31 18:27:52",
      "jail": "nginx-http-auth",
      "ip": "10.11.12.13",
      "detail": "failed login attempt [10.11.12.13]"
    }
  ]
}
```

### Exemplos de Requisição

#### cURL
```bash
curl http://127.0.0.1:15000/api/stats
```

#### JavaScript (Fetch API)
```javascript
fetch('/api/stats')
  .then(response => response.json())
  .then(data => {
    console.log('Banidos:', data.banned);
    console.log('Liberados:', data.unbanned);
    console.log('Falhas:', data.failures);
  });
```

#### Python
```python
import requests
import json

response = requests.get('http://127.0.0.1:15000/api/stats')
data = response.json()

print(f"IPs Banidos: {data['banned']}")
print(f"IPs Liberados: {data['unbanned']}")
print(f"Total Falhas: {len(data['failures'])}")
```

#### cURL com Pretty Print
```bash
curl http://127.0.0.1:15000/api/stats | jq .
```

---

## Comportamento em Casos Especiais

### Ficheiro de Log Não Encontrado
Se o ficheiro de log especificado não existir:
- **Resposta:** JSON válido com arrays vazios
  ```json
  {
    "banned": [],
    "unbanned": [],
    "failures": []
  }
  ```

### Erro de Leitura de Ficheiro
Se houver erro de permissão ou I/O:
- **Resultado:** Arrays vazios (silenciosamente)
- **Nota:** Verifique logs do systemd

### Linha de Log Malformada
Se uma linha não corresponder aos padrões regex:
- **Resultado:** Linha é ignorada
- **Próximas linhas:** Continuam sendo processadas

### IP Duplicado
- **Comportamento:** Sets evitam duplicatas
- **Resultado:** Cada IP aparece uma única vez

---

## Performance e Limites

| Métrica | Limite | Nota |
|---------|--------|------|
| Tamanho máximo do log | 100MB | Testado com sucesso |
| IPs únicos suportados | 10,000+ | Sem problemas |
| Falhas retornadas | 100 | Últimas 100 |
| Tempo de resposta | <1s | Típico com logs normais |
| Taxa de refresh | 5s | Configurável |

---

## Headers HTTP

### Requisição
```
GET /api/stats HTTP/1.1
Host: 127.0.0.1:15000
Accept: application/json
```

### Resposta
```
HTTP/1.1 200 OK
Content-type: application/json
Content-Length: 1234
Connection: close
```

---

## Códigos de Erro

| Código | Situação | Comportamento |
|--------|----------|---------------|
| 200 | Sucesso | JSON válido retornado |
| 404 | Endpoint não existe | Mensagem de erro padrão |
| 500 | Erro interno servidor | Raro; verifique logs |

---

## Integração com Terceiros

### Exemplos de Integração

#### Monitoring (Nagios/Icinga)
```bash
#!/bin/bash
BANNED=$(curl -s http://127.0.0.1:15000/api/stats | jq '.banned | length')
if [ $BANNED -gt 100 ]; then
  echo "CRITICAL: $BANNED IPs banidos"
  exit 2
fi
```

#### Alertas (Script Customizado)
```python
import requests
import json

response = requests.get('http://127.0.0.1:15000/api/stats')
data = response.json()

if len(data['banned']) > 50:
    # Enviar alerta por email/webhook
    send_alert(f"Threshold: {len(data['banned'])} IPs banidos")
```

#### Logging (ELK Stack)
```bash
curl -s http://127.0.0.1:15000/api/stats | \
  jq -c '.banned[] | {ip: ., status: "banned"}' | \
  while read line; do
    curl -X POST http://elasticsearch:9200/fail2ban/_doc -d "$line"
  done
```

---

## Rate Limiting

Atualmente **não implementado**. O servidor HTTP Python não tem rate limiting.

Para ambientes de produção, considere:
- Nginx reverse proxy com `limit_req`
- iptables rules
- Firewall da VPS

---

## CORS (Cross-Origin Requests)

Atualmente **não configurado**. O dashboard funciona no mesmo domínio/porta.

Se precisar de CORS, adicione headers:
```python
self.send_header('Access-Control-Allow-Origin', '*')
self.send_header('Access-Control-Allow-Methods', 'GET')
```

---

## Changelog da API

### v2.0 (2026-05-31)
- ✅ Campo "unbanned" adicionado
- ✅ Sincronização de ban/unban

### v1.0 (2026-05-15)
- 🎉 Versão inicial
- ✅ Campos "banned" e "failures"

---

**Última Atualização:** Maio 2026 | **Versão API:** 2.0
