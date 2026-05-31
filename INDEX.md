# 📖 Índice de Documentação - Fail2Ban Web Dashboard

Bem-vindo! Este ficheiro ajuda a navegar toda a documentação do projeto.

---

## 🚀 Começar Rápido

**Novo no projeto?** Comece aqui:

1. [README.md](README.md) - Visão geral e instalação
2. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Se algo não funcionar
3. [API.md](API.md) - Como usar a API

---

## 📚 Documentos

### [README.md](README.md)
**O que é e como usar**
- O que é o Fail2Ban Web Dashboard
- Funcionalidades principais
- Como instalar
- Requisitos do sistema
- Guia de utilização
- FAQ rápido

**Para quem:** Administradores, novos utilizadores

---

### [DOCUMENTATION.md](DOCUMENTATION.md)
**Documentação técnica completa**
- Arquitetura do sistema
- Parsing de logs (regex patterns)
- Componentes do frontend (JavaScript)
- Configuração avançada
- Exemplos de uso
- Debugging técnico
- Performance e capacidade

**Para quem:** Desenvolvedores, SysAdmins técnicos

---

### [API.md](API.md)
**Referência completa da API**
- Endpoints HTTP (`/` e `/api/stats`)
- Estrutura JSON
- Exemplos de requisição/resposta
- Integração com terceiros
- Rate limiting
- CORS

**Para quem:** Integradores, desenvolvedores

---

### [CHANGELOG.md](CHANGELOG.md)
**Histórico de versões**
- O que foi adicionado em cada versão
- O que foi alterado/corrigido
- Roadmap futuro
- Como contribuir

**Para quem:** Utilizadores interessados em atualizações

---

### [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
**Resolução de problemas**
- Problemas de acesso
- Dados não atualizam
- Erros de permissão
- Performance lenta
- Checklist de diagnóstico
- Contato para suporte

**Para quem:** Utilizadores com problemas

---

## 🎯 Procurar por Tópico

### Instalação e Setup
- [README.md - Instalação Rápida](README.md#⚙️-instalação-rápida)
- [DOCUMENTATION.md - Configuração do Systemd](DOCUMENTATION.md#configuração-do-systemd)

### Como Usar
- [README.md - Guia de Utilização](README.md#📖-guia-de-utilização)
- [DOCUMENTATION.md - Exemplos de Uso](DOCUMENTATION.md#exemplos-de-uso)

### Problemas
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Todo o documento
- [README.md - Troubleshooting](README.md#🚨-troubleshooting)

### API e Integração
- [API.md](API.md) - Completo
- [API.md - Integração com Terceiros](API.md#integração-com-terceiros)

### Desenvolvimento
- [DOCUMENTATION.md - Parsing de Logs](DOCUMENTATION.md#parsing-de-logs)
- [DOCUMENTATION.md - Frontend](DOCUMENTATION.md#frontend)
- [DOCUMENTATION.md - Debugging](DOCUMENTATION.md#debugging)

### Versões e Atualizações
- [CHANGELOG.md](CHANGELOG.md) - Completo
- [README.md - Versão & Changelog](README.md#📈-versão--changelog)

---

## 💡 Guias Temáticos

### Cenário 1: Monitorar SSH
```
README.md → Funcionalidades (IPs Banidos)
DOCUMENTATION.md → Exemplos de Uso (Cenário 1)
```

### Cenário 2: Analisar Reincidência
```
README.md → Guia de Utilização (Pesquisar IP)
DOCUMENTATION.md → Exemplos de Uso (Cenário 2)
```

### Cenário 3: Integrar com Monitoring
```
API.md → Integração com Terceiros
DOCUMENTATION.md → Debugging (Testar parser)
```

### Cenário 4: Performance Lenta
```
TROUBLESHOOTING.md → Problemas de Performance
DOCUMENTATION.md → Performance e Limites
README.md → Troubleshooting
```

### Cenário 5: Contribuir / Modificar
```
DOCUMENTATION.md → Arquitetura completa
DOCUMENTATION.md → Frontend (JavaScript)
CHANGELOG.md → Como Contribuir
```

---

## 🔄 Fluxo de Leitura Recomendado

**Por Experiência do Utilizador:**

### Iniciante
1. [README.md](README.md) - 10 min
2. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) (se necessário)
3. Pronto para usar!

### Intermédio
1. [README.md](README.md) - 10 min
2. [API.md](API.md) - 10 min (skim)
3. [DOCUMENTATION.md](DOCUMENTATION.md) - 20 min (Exemplos)
4. Pronto para integrar/customizar

### Avançado
1. [DOCUMENTATION.md](DOCUMENTATION.md) - Completo (30 min)
2. [API.md](API.md) - Completo (15 min)
3. [CHANGELOG.md](CHANGELOG.md) - Roadmap futuro
4. Pronto para contribuir/estender

---

## 📊 Estrutura de Ficheiros

```
fail2ban-webui/
├── README.md                 ← COMECE AQUI
├── INDEX.md                  ← Este ficheiro
├── DOCUMENTATION.md          ← Técnico completo
├── API.md                    ← Endpoints HTTP
├── CHANGELOG.md              ← Versões
├── TROUBLESHOOTING.md        ← Problemas
├── app.py                    ← Código principal
├── CONTRIBUTING.md           ← (Futuro)
└── LICENSE                   ← (MIT)
```

---

## 🔍 Busca Rápida

### Tenho uma pergunta sobre...

| Pergunta | Documento | Secção |
|----------|-----------|--------|
| Como instalar? | README.md | Instalação Rápida |
| Como usar? | README.md | Guia de Utilização |
| Como customizar? | DOCUMENTATION.md | Configuração Avançada |
| Como integrar? | API.md | Integração com Terceiros |
| O que mudou? | CHANGELOG.md | Versões |
| Algo não funciona | TROUBLESHOOTING.md | Problema específico |
| Detalhes técnicos? | DOCUMENTATION.md | Arquitetura |
| Endpoints da API? | API.md | Endpoints |

---

## 🎓 Aprender Conceitos

### Compreender o Sistema
1. DOCUMENTATION.md → [Arquitetura](#arquitetura)
2. DOCUMENTATION.md → [Fluxo de Dados](#fluxo-de-dados)

### Parsing de Logs
1. DOCUMENTATION.md → [Parsing de Logs](#parsing-de-logs)
2. Teste manual: `grep "Ban" /var/log/fail2ban.log`

### Frontend JavaScript
1. DOCUMENTATION.md → [Frontend](#frontend)
2. DOCUMENTATION.md → [Arquitetura JavaScript](#arquitetura-javascript)

### API
1. API.md → [Endpoint /api/stats](#endpoint-get-apistats)
2. Teste: `curl http://127.0.0.1:15000/api/stats | jq .`

---

## ⚡ Atalhos Úteis

```bash
# Ver status
sudo systemctl status fail2ban-webui

# Ver logs em tempo real
sudo journalctl -u fail2ban-webui -f

# Testar API
curl http://127.0.0.1:15000/api/stats | jq .

# Ver IPs banidos
curl -s http://127.0.0.1:15000/api/stats | jq '.banned'

# Reiniciar serviço
sudo systemctl restart fail2ban-webui
```

---

## 📞 Suporte

**Algo não está claro?**

1. Verifique [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Verifique a secção relevante em [README.md](README.md)
3. Abra issue no GitHub com detalhes completos

---

## 🎁 Contribuir

Quer melhorar a documentação ou o código?

Veja: [CHANGELOG.md - Como Contribuir](CHANGELOG.md#como-contribuir)

---

**Versão:** 2.0 | **Última Atualização:** Maio 2026

---

## Sumário Executivo (1 min read)

- **Ficheiro:** [README.md](README.md) - Comece aqui
- **Técnico:** [DOCUMENTATION.md](DOCUMENTATION.md) - Aprofundar
- **API:** [API.md](API.md) - Integrar
- **Problemas:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Corrigir
- **Versões:** [CHANGELOG.md](CHANGELOG.md) - Estar atualizado
