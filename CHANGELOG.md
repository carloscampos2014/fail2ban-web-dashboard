# CHANGELOG - Fail2Ban Web Dashboard

Todas as mudanças notáveis neste projeto serão documentadas neste ficheiro.

## [2.0.0] - 2026-05-31

### ✨ Adicionado

- **Rastreamento de IPs Liberados (Unbanned)**
  - Nova aba "IPs Liberados" para visualizar histórico de desbloqueios
  - Sincronização automática entre ban/unban states
  - Card de métrica "IPs Liberados Únicos"

- **Melhorias na Interface**
  - Grid de métricas expandido de 2 para 3 colunas
  - Contadores dinâmicos "Exibindo: X/Y" em cada aba
  - Altura do container aumentada de 480px para 700px
  - Layout flexível para melhor distribuição de espaço

- **Funcionalidades Adicionadas**
  - Debug output formatado no console (já existia, mantido)
  - Métricas em tempo real com cores diferenciadas
  - Melhor handling de IPs duplicados via Sets

- **Documentação**
  - README.md atualizado com novas funcionalidades
  - DOCUMENTATION.md criado (guia técnico completo)
  - CHANGELOG.md criado (este ficheiro)

### 🔧 Alterado

- Backend: Ordem de processamento de logs (Unban → Ban → Found)
- Backend: Parser agora usa `elif` para evitar conflitos
- Backend: Retorno de API agora inclui campo "unbanned"
- Frontend: Tabelas reconstruem completamente em cada refresh
- Frontend: Filtros de pesquisa são preservados durante updates
- Frontend: Status badges com cores mais distintas

### 🎨 UI/UX

- Cores mais visuais:
  - Vermelho (#ef4444) para banidos
  - Verde (#10b981) para liberados
  - Âmbar (#f59e0b) para falhas
- Responsividade melhorada
- Hover effects em todas as linhas de tabela

### 📊 Performance

- Sets em vez de listas (O(1) lookup vs O(n))
- Regex otimizadas para matching rápido
- Scroll nativo sem bibliotecas externas
- Cache local de IPs reduz requisições

### 🐛 Corrigido

- IP removido de banidos quando é unbanned
- Header da tabela agora fica fixo durante scroll
- Contadores atualizam corretamente após filtros
- Detalhe do log não quebra layout com textos longos

---

## [1.0.0] - 2026-05-15

### ✨ Adicionado

- Dashboard web para monitorização de Fail2Ban
- Visualização de IPs banidos
- Histórico de tentativas falhadas
- Auto-refresh a cada 5 segundos
- Botão de refresh manual
- Interface dark mode com Tailwind CSS
- Tabelas com scroll otimizado
- Deployment como serviço systemd
- Suporte para portas e caminhos customizados

### 🏗️ Arquitetura

- Backend: Python 3 com SimpleHTTPRequestHandler
- Frontend: HTML5 + JavaScript AJAX + Tailwind CSS
- Parser: Regex para análise de logs
- API: JSON endpoint `/api/stats`

### 🔒 Segurança

- Binding apenas a 127.0.0.1 (localhost)
- Sem dependências externas (Python nativo)
- Tratamento de errors na leitura de ficheiros

---

## Notas de Versão

### v2.0 → v1.0
**Diferenças principais:**
- v2.0 adiciona rastreamento de unbans
- v2.0 melhora organização visual
- v2.0 inclui documentação técnica completa
- v1.0 era MVP com funcionalidade básica

### Compatibilidade
- Todos os scripts de deploy de v1.0 funcionam com v2.0
- API é retrocompatível (novo campo "unbanned" é adicional)

---

## Planeado para Futuras Versões

### v2.1
- [ ] Exportar dados em CSV
- [ ] Melhorias de performance para logs gigantes
- [ ] Cache persistente opcional

### v3.0
- [ ] Banco de dados (SQLite)
- [ ] Gráficos de tendências (Chart.js)
- [ ] Alertas via email/webhook
- [ ] Autenticação básica

### v4.0
- [ ] Multi-servidor
- [ ] Dark/Light mode toggle
- [ ] API de desbloqueio remoto
- [ ] WebSocket para real-time updates

---

## Como Reportar Issues

Encontrou um bug? Abra uma issue com:
- Versão do Fail2Ban Web Dashboard
- Versão do Fail2Ban
- Versão do Python
- Passos para reproduzir
- Logs relevantes

---

## Como Contribuir

1. Faça fork do repositório
2. Crie uma branch (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -am 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

---

**Responsável por Versão:** Carlos Campos | **Contacto:** github.com/carloscampos2014
