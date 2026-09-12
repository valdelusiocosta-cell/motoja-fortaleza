# MotoJá Fortaleza — MVP local full-stack

MVP executável de mobilidade urbana por motocicleta para Fortaleza e Região Metropolitana. O projeto roda sem Node.js e sem dependências externas: **Python 3 + biblioteca padrão + SQLite**, com uma API JSON e uma interface web responsiva mobile-first.

> Este é um ambiente de desenvolvimento/demonstração. Ele não deve ser usado para transportar passageiros reais antes das integrações, validações legais e controles de segurança da lista ao final.

## O que está implementado

### Passageiro

- Cadastro e login local por e-mail/telefone e senha (OTP é um placeholder).
- Origem e destino, botão de geolocalização do navegador e estimativa de distância, tempo e tarifa.
- Seleção de Pix, cartão ou dinheiro (sem cobrança real).
- Solicitação persistida no SQLite, acompanhamento do estado e atualização automática.
- Identificação do motorista, cancelamento, compartilhamento placeholder e emergência registrada como incidente.
- Avaliação de 1 a 5, histórico, perfil, carteira e suporte placeholder.

### Motorista

- Cadastro com estado documental pendente.
- Perfil, aprovação, status online/offline e formulário de envio de documento (nome/metadata; nenhum arquivo real é armazenado).
- Lista de ofertas abertas, aceite, início e conclusão da corrida.
- Resumo de corridas, bruto, comissão configurada e líquido.

### Administração

- Dashboard com passageiros, motoristas, pendências, corridas e incidentes.
- Lista de motoristas e documentos, aprovação e suspensão.
- Lista de corridas persistidas.
- Configuração de tarifa base, preço por km, preço por minuto, mínimo e comissão.
- Lista e resolução de incidentes de suporte.

### API e dados

- API REST JSON com validação de entrada, autenticação por token de sessão, autorização por papel e transições explícitas:
  `searching → accepted → in_progress → finished` ou `cancelled`.
- SQLite com tabelas de usuários, perfis, documentos, tarifas, corridas, eventos, avaliações, incidentes e sessões.
- `server.py` serve também os arquivos estáticos de `public/`.
- Adaptadores claramente isolados para cotação/rotas e marcadores de integração futura.

## Como executar

Requer Python 3.10+ (foi desenvolvido/testado com Python 3.13). Não requer `pip`, Node ou banco separado.

```bash
cd moto-fortaleza
python3 server.py
```

Abra no navegador: <http://localhost:3000>

Variáveis opcionais:

```bash
PORT=3100 MOTOJA_DB=/caminho/motoja.sqlite3 python3 server.py
```

A base `motoja.sqlite3` é criada automaticamente no primeiro início. Para reiniciar o ambiente local, pare o servidor e remova esse arquivo.

### Contas de demonstração

Todas usam a senha `demo1234`:

| Perfil | E-mail |
|---|---|
| Passageiro | `passageiro@demo.motoja.local` |
| Motorista já aprovado | `motorista@demo.motoja.local` |
| Administração | `admin@demo.motoja.local` |

A tela de entrada tem botões para preencher os acessos. Para testar uma corrida ponta a ponta:

1. Entre como **passageiro**, faça uma cotação e solicite a corrida.
2. Em outra janela anônima (ou depois de sair), entre como **motorista**.
3. Fique online, aceite a oferta, depois use a API ou a interface de operação para evoluir o estado. A interface de passageiro atualiza automaticamente; a evolução de início/fim pode ser feita pelo endpoint abaixo durante o MVP.
4. Entre como administrador para ver a corrida e os indicadores.

## API principal

Todas as rotas protegidas usam `Authorization: Bearer <token>`.

| Método | Rota | Uso |
|---|---|---|
| GET | `/api/health` | Saúde do serviço |
| POST | `/api/auth/signup` | Criar passageiro/motorista |
| POST | `/api/auth/login` | Entrar |
| GET | `/api/me` | Sessão atual |
| POST | `/api/quote` | Cotação local estimada |
| POST/GET | `/api/rides` | Criar/listar corridas do papel atual |
| GET | `/api/rides/:id` | Detalhes e eventos (participantes/admin) |
| POST | `/api/rides/:id/accept` | Aceite do motorista online/aprovado |
| POST | `/api/rides/:id/start` | Iniciar corrida |
| POST | `/api/rides/:id/finish` | Finalizar corrida |
| POST | `/api/rides/:id/cancel` | Cancelar dentro da máquina de estados |
| POST | `/api/rides/:id/rate` | Avaliar corrida concluída |
| POST | `/api/rides/:id/share` | Registrar compartilhamento placeholder |
| POST | `/api/rides/:id/emergency` | Registrar incidente de emergência |
| GET/POST | `/api/driver/profile`, `/api/driver/online` | Perfil/status do motorista |
| GET | `/api/driver/offers` | Ofertas de corridas abertas |
| GET | `/api/driver/earnings` | Ganhos e histórico |
| POST | `/api/driver/documents` | Enviar metadata de documento |
| GET | `/api/admin/summary` | Indicadores operacionais |
| GET | `/api/admin/users`, `/api/admin/drivers`, `/api/admin/rides` | Listas administrativas |
| GET/POST | `/api/admin/fare-config` | Ler/alterar tarifa |
| GET | `/api/admin/incidents` | Incidentes e suporte |
| POST | `/api/admin/drivers/:id/approve` | Aprovar motorista |
| POST | `/api/admin/drivers/:id/suspend` | Suspender motorista |
| POST | `/api/admin/incidents/:id/resolve` | Resolver incidente |

Exemplo de cotação:

```bash
curl -X POST http://localhost:3000/api/quote \
  -H 'Content-Type: application/json' \
  -d '{"origin":"Aldeota","destination":"Centro"}'
```

## Testes locais

Há um smoke test sem dependências em `test_mvp.py`. Ele usa sockets locais em memória, cria um SQLite temporário e verifica health, login, cotação, criação da corrida, online do motorista, aceite, início, conclusão, transição inválida e resumo administrativo:

```bash
cd moto-fortaleza
python3 -m py_compile server.py
python3 test_mvp.py
```

Resultado esperado:

```text
OK: health, auth, quote, ride state machine, driver and admin endpoints
```

## Checklist para produção

### Produto, operação e jurídico

- [ ] Constituir empresa responsável, termos de uso, política de privacidade, consentimentos e canal LGPD.
- [ ] Validar com assessoria jurídica e órgãos competentes as regras nacionais e municipais de transporte individual remunerado, incluindo Fortaleza e cada município metropolitano.
- [ ] Definir área-piloto, horários, pontos de apoio, atendimento humano, SLA e protocolo de acidentes/incidentes.
- [ ] Confirmar requisitos de idade, CNH categoria A com EAR, tempo de habilitação, equipamentos, cilindrada, veículo e documentos.
- [ ] Contratar/validar seguros e responsabilidade civil aplicáveis.

### Integrações obrigatórias

- [ ] **Mapas e rotas:** geocodificação, rota real, ETA, mapa e cálculo de distância via Google Maps, Mapbox ou fornecedor equivalente; substituir `quote()` por adaptador real.
- [ ] **Identidade/OTP:** telefone, OTP, CPF, prova de vida e verificação antifraude; nunca usar senha/demo em produção.
- [ ] **Documentos:** upload privado, antivírus, URLs temporárias, OCR/verificação, validade e revisão humana.
- [ ] **Pagamentos:** Pix/cartão, antifraude, autorização/captura, estorno, conciliação, split marketplace, comissão e repasse.
- [ ] **Notificações:** push Android/iOS, SMS e eventualmente WhatsApp transacional; implementar retry e preferências.
- [ ] **Contato e segurança:** ligação/chat mascarados, compartilhamento por link com expiração, central de emergência e localização em tempo real.

### Segurança e infraestrutura

- [ ] TLS obrigatório, domínio, gestão de segredos e backups criptografados.
- [ ] Trocar SQLite por PostgreSQL/PostGIS, com migrações, pool, backups e recuperação testada.
- [ ] Tokens curtos com refresh/revogação, rate limit, proteção contra abuso, MFA para administração e RBAC granular.
- [ ] Criptografar dados sensíveis em repouso, minimizar retenção, exclusão/exportação LGPD e trilha de auditoria imutável.
- [ ] Logs estruturados sem senha/documento, métricas, tracing, alertas, Sentry/observabilidade e monitoramento de disponibilidade.
- [ ] CI/CD, testes de unidade/integração/e2e, revisão de dependências, pentest e deploy com rollback.
- [ ] Publicação e operação dos apps Android/iOS, políticas das lojas, suporte e plano de continuidade.

### Limitações intencionais deste MVP

A estimativa é determinística e não representa rota real; não há cobrança, split, repasse, OTP, push, upload de arquivo, identidade, navegação, posição GPS do motorista ou despacho geográfico real. O botão de emergência apenas registra um incidente local e não contata serviços públicos. Os dados e contas demo são apropriados somente para desenvolvimento.
