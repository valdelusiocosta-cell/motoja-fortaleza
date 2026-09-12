# PRD — MotoJá Fortaleza

**Versão:** 0.1  
**Status:** Especificação inicial  
**Área inicial:** Fortaleza e Região Metropolitana  
**Plataformas:** Android primeiro; iOS na fase seguinte; painel web para operação

---

## 1. Visão geral do produto

### 1.1 Proposta de valor

O MotoJá conecta passageiros a motociclistas verificados para viagens rápidas, acessíveis e seguras em Fortaleza e na Região Metropolitana. O produto deve combinar a agilidade da moto com uma operação local mais próxima, transparente e comprometida com a regulamentação municipal.

**Promessa principal:** pedir uma moto em poucos toques, saber o preço antes de confirmar e acompanhar a viagem com segurança do início ao fim.

### 1.2 Público-alvo

**Passageiros**

- Pessoas que precisam se deslocar rapidamente em horários de trânsito intenso.
- Usuários sensíveis a preço, especialmente em trajetos curtos e médios.
- Trabalhadores, estudantes e clientes de comércio e serviços.
- Pessoas que valorizam suporte local e previsibilidade de preço.

**Motociclistas**

- Condutores que já trabalham ou desejam trabalhar com transporte por aplicativo.
- Profissionais que buscam mais transparência sobre comissão, ganhos e regras.
- Motociclistas da capital e dos municípios atendidos na Região Metropolitana.

**Operação**

- Equipe responsável por análise documental, suporte, segurança, pagamentos e qualidade.

### 1.3 Posicionamento e diferenciais

O MotoJá não deve competir apenas por menor preço. Seu posicionamento será **mobilidade local, segura e transparente**.

| Dimensão | MotoJá | Grandes apps de moto |
|---|---|---|
| Foco geográfico | Fortaleza e RM, com operação e suporte locais | Cobertura ampla e operação padronizada |
| Segurança | Verificação documental, botão de emergência, compartilhamento e trilha de ocorrências | Recursos de segurança já conhecidos pelo mercado |
| Transparência para o motociclista | Comissão, ganhos e repasses exibidos antes e depois da corrida | Diferenciar pela clareza de ganhos e suporte próximo |
| Atendimento | Suporte humanizado e contextualizado para a região | Canais de maior escala |
| Oferta local | Campanhas, pontos de alta demanda e parcerias com comércios locais | Campanhas nacionais ou por grande região |
| Relacionamento | Programa de fidelidade e benefícios para passageiros e motociclistas | Incentivos definidos pela plataforma |
| Conformidade | Cadastro alinhado às exigências municipais e nacionais aplicáveis | Seguir requisitos próprios de cada operação |

**Diferenciais prioritários:** segurança verificável, preço claro, melhor experiência para o motociclista, suporte local e expansão por bairros/municípios com densidade suficiente.

---

## 2. Objetivos e métricas

### Objetivos do MVP

- Permitir cadastro e aprovação de passageiros e motociclistas.
- Concluir corridas reais em uma área-piloto.
- Ter preço estimado antes da confirmação.
- Acompanhar status e localização da corrida.
- Processar pagamento e repasse com conciliação.
- Registrar avaliações, suporte e incidentes.

### Indicadores principais

- Taxa de conclusão de cadastro.
- Tempo médio até encontrar motociclista.
- Taxa de aceitação e cancelamento.
- Corridas concluídas por dia.
- Retenção de passageiros em 7 e 30 dias.
- Ganho líquido médio por motociclista/hora online.
- Nota média e taxa de incidentes.
- Custo de aquisição e margem por corrida.

---

## 3. Fluxo do passageiro

### 3.1 Cadastro e entrada

1. Splash com marca e carregamento.
2. Login por telefone com código OTP.
3. Nome, CPF, data de nascimento e aceite dos termos.
4. Permissão de localização.
5. Cadastro opcional de cartão e contato de confiança.
6. Entrada na Home com mapa.

### 3.2 Solicitação de corrida

1. Passageiro toca em “Para onde vamos?”.
2. Informa destino por busca, mapa ou endereço salvo.
3. Confirma local de embarque e observa pontos de referência.
4. Vê modalidade Moto, tarifa estimada, distância e tempo.
5. Escolhe pagamento e aplica cupom, se houver.
6. Confirma “Solicitar moto”.
7. Sistema busca motociclistas elegíveis por proximidade, status e segurança.
8. Passageiro recebe identificação do condutor e previsão de chegada.

### 3.3 Corrida ativa

- Mapa com posição do motociclista.
- Status: procurando, a caminho, chegou, em viagem e concluída.
- Nome, foto, nota, moto e placa.
- Botões de chat, ligação protegida, compartilhar corrida e emergência.
- Código de embarque opcional para confirmar o passageiro.
- Finalização automática/manual e recibo.

### 3.4 Pagamento e avaliação

1. Gateway autoriza ou registra a forma de pagamento.
2. Ao finalizar, calcula-se o valor final conforme regras de tarifa.
3. Plataforma retém comissão e gera repasse do motociclista.
4. Passageiro vê recibo detalhado.
5. Avalia de 1 a 5 estrelas e escolhe motivos rápidos.
6. Pode abrir suporte ou contestar cobrança.

---

## 4. Fluxo do motociclista

### 4.1 Cadastro e aprovação

1. Login por telefone e validação de identidade.
2. Dados pessoais, endereço e dados bancários.
3. Envio de CNH, comprovante de EAR, documento do veículo, fotos e demais documentos exigidos.
4. Declaração de ciência das regras de segurança e operação.
5. Análise automática de validade e análise humana quando necessário.
6. Aprovação, pendência com motivo claro ou recusa fundamentada.
7. Treinamento rápido sobre app, atendimento, segurança e incidentes.

Para transporte de passageiros em Fortaleza, o fluxo deve considerar os requisitos municipais divulgados, incluindo idade mínima, CNH categoria A com EAR, tempo mínimo de habilitação, equipamentos de segurança, cilindrada mínima e documentação regularizada. A validação jurídica e operacional deve ser atualizada antes do lançamento.

### 4.2 Operação de corridas

1. Motociclista fica offline por padrão.
2. Ao ficar online, o app verifica localização, documentos, conectividade e condições de operação.
3. Recebe chamada com origem, destino aproximado, distância, estimativa de valor e ganho líquido.
4. Aceita ou recusa dentro do prazo.
5. Navega até o ponto de embarque.
6. Confirma chegada e embarque por botão/código.
7. Inicia a corrida e segue navegação integrada.
8. Finaliza no destino e visualiza o valor e o repasse.

### 4.3 Ganhos

- Resumo diário, semanal e mensal.
- Valor bruto, comissão, incentivos, gorjetas, ajustes e valor líquido.
- Histórico de repasses e status de saque.
- Metas e campanhas sempre com regras explícitas.
- Carteira com Pix de recebimento e conciliação.

---

## 5. Telas principais e wireframes em texto

### 5.1 Passageiro — Splash

```text
[logo MotoJá]
Fortaleza e região

                 Carregando...
```

### 5.2 Login

```text
[logo]
Entre para pedir sua moto
[ +55 (  ) _____-____ ]
[Continuar]

Ao continuar, você aceita Termos e Privacidade.
```

### 5.3 Home com mapa

```text
[☰]                         [avatar]

[ Para onde você vai?                         ]

              MAPA / posição atual

[Casa] [Trabalho] [Favoritos]

[Contato de confiança]       [Ajuda]
```

### 5.4 Solicitação de corrida

```text
[←] Solicitar moto

Embarque
[ localização atual                         ]

Destino
[ endereço ou ponto de interesse              ]

Moto             6 min       R$ 00,00–00,00

Pagamento: Pix                         [Trocar]
Cupom: [Adicionar]

[Confirmar solicitação]
```

### 5.5 Busca de motociclista

```text
Procurando motociclista...

              MAPA / área de busca

Estimativa: R$ 00,00    •    até 8 min

[Cancelar solicitação]
```

### 5.6 Corrida ativa

```text
[←] Corrida em andamento       [SOS]

              MAPA / rota e posição

[foto] Nome do motociclista
       ★ 4,9 · Honda CG 160 · ABC-1D23

Status: motociclista a caminho

[Chat] [Ligar] [Compartilhar]
```

### 5.7 Histórico

```text
[←] Minhas corridas

Hoje
Aldeota → Centro                 R$ 12,40
Ontem
Messejana → Parangaba            R$ 18,90

[Ver detalhes]
```

### 5.8 Perfil

```text
[avatar] Nome do passageiro
         telefone verificado

Dados pessoais                  >
Contatos de confiança            >
Formas de pagamento              >
Segurança                        >
Ajuda e suporte                  >
Termos e privacidade             >
```

### 5.9 Carteira

```text
[←] Carteira

Formas de pagamento
[Pix] Principal                  >
[Cartão final 1234]              >

Cupons e créditos                >
Histórico financeiro              >
```

### 5.10 Motociclista — Home operacional

```text
[avatar]                         [Ajuda]

Você está OFFLINE
[ Ficar online ]

Hoje
Ganhos R$ 00,00   Corridas 0   Nota 4,9

[Carteira] [Documentos] [Histórico]
```

### 5.11 Oferta de corrida

```text
Nova corrida
Origem: bairro / referência
Destino: bairro / referência
Distância: 5,2 km   Previsão: 18 min
Seu ganho estimado: R$ 9,80

[Recusar]                 [Aceitar]
```

### 5.12 Documentos

```text
[←] Meus documentos

CNH + EAR                  Aprovado
Documento da moto          Aprovado
Seguro / comprovante       Pendente

[Enviar documento]

Não fique online se algum documento obrigatório estiver vencido.
```

---

## 6. Identidade visual

### 6.1 Direção

Visual limpo, forte e urbano, com alto contraste, leitura rápida e sensação de energia. A interface deve parecer confiável, sem copiar a identidade visual de 99 ou Uber.

### 6.2 Paleta sugerida

- **Verde elétrico — #12B879:** ação principal, confirmação e marca.
- **Azul petróleo — #123B4A:** confiança, textos fortes e cabeçalhos.
- **Amarelo sol — #FFC928:** alerta positivo, promoções e destaque de tarifa.
- **Creme — #FFF9EE:** fundos e áreas de descanso visual.
- **Cinza grafite — #1E2928:** texto principal.
- **Cinza claro — #E8EFEC:** bordas e superfícies.
- **Vermelho segurança — #D84C4C:** emergência e ações destrutivas.

### 6.3 Tipografia e componentes

- **Tipografia:** Inter ou Manrope; pesos 400, 600 e 700.
- Cantos arredondados de 12–16 px.
- Botões grandes, com área mínima de toque confortável.
- Ícones simples, contorno consistente e poucos elementos por tela.
- Amarelo apenas como destaque; verde como ação principal para diferenciar a marca.

---

## 7. Funcionalidades essenciais

### P0 — obrigatórias no MVP

- Cadastro/login por telefone e OTP.
- Geolocalização e seleção de origem/destino.
- Cálculo de rota, distância, duração e tarifa estimada.
- Despacho por proximidade e disponibilidade.
- Localização em tempo real durante aceite e corrida.
- Estados da corrida com sincronização entre passageiro e motociclista.
- Pagamento por Pix e cartão via gateway compatível com marketplace/split.
- Comissão e repasse calculados por corrida.
- Chat ou contato mascarado entre as partes.
- Avaliação e motivos de denúncia.
- Histórico e recibo.
- Suporte, emergência e compartilhamento da corrida.
- Painel administrativo para documentos, usuários, corridas, tarifas e incidentes.

### P1 — após validação do MVP

- Agendamento de corrida.
- Corridas recorrentes para trabalho/estudo.
- Cupons, carteira de créditos e programa de indicação.
- Destinos favoritos e múltiplas paradas.
- Programa de benefícios para motociclistas.
- Relatórios avançados e previsão de demanda.
- Notificações por push, SMS e WhatsApp transacional.

### Requisitos não funcionais

- Disponibilidade e monitoramento da API.
- Criptografia em trânsito e em repouso.
- LGPD: consentimento, finalidade, acesso, exclusão e retenção mínima.
- Logs de auditoria para pagamentos, documentos e suporte.
- Controle antifraude e detecção de comportamento anômalo.
- Acessibilidade, baixo consumo de dados e tolerância a conexão instável.

---

## 8. Arquitetura técnica sugerida

### 8.1 Stack recomendada

- **Apps:** Flutter para compartilhar código entre Android e iOS.
- **Painel:** React/Next.js ou Flutter Web.
- **Backend:** Node.js com NestJS ou Fastify, API REST e WebSocket para eventos em tempo real.
- **Banco principal:** PostgreSQL com PostGIS para consultas geográficas.
- **Cache e filas:** Redis para disponibilidade, despacho e jobs.
- **Arquivos:** armazenamento compatível com S3 para documentos, com acesso privado e URLs temporárias.
- **Autenticação:** OTP por provedor de SMS/e-mail, tokens de curta duração e refresh seguro.
- **Mapas:** Google Maps Platform ou Mapbox para geocodificação, rotas e mapa; separar a camada de fornecedor para permitir troca futura.
- **Pagamentos:** gateway brasileiro com Pix, cartão, antifraude, split e repasse para marketplace.
- **Push:** Firebase Cloud Messaging e Apple Push Notification Service.
- **Observabilidade:** logs centralizados, métricas, rastreamento de erros e alertas.

### 8.2 Domínios do backend

- Identidade e autenticação.
- Passageiros e perfis.
- Motociclistas, veículos e documentos.
- Tarifas e promoções.
- Corridas e máquina de estados.
- Despacho e localização.
- Pagamentos, split, repasses e conciliação.
- Avaliações e suporte.
- Notificações.
- Administração e auditoria.

### 8.3 Entidades principais

`User`, `PassengerProfile`, `DriverProfile`, `Vehicle`, `Document`, `Ride`, `RideEvent`, `LocationPing`, `FareRule`, `Payment`, `Payout`, `Rating`, `SupportTicket`, `Promotion`.

### 8.4 Fluxo de despacho

1. Receber solicitação e validar tarifa/pagamento.
2. Buscar motociclistas online, aprovados e dentro da área.
3. Ordenar por distância, tempo estimado, qualidade e regras de equilíbrio.
4. Ofertar em ondas curtas, sem expor dados desnecessários.
5. Confirmar o primeiro aceite válido.
6. Atualizar passageiro e demais candidatos em tempo real.
7. Escalar para suporte quando não houver oferta ou houver falhas repetidas.

---

## 9. Modelo de monetização

### Modelo principal

- Comissão percentual por corrida, exibida com transparência ao motociclista.
- Tarifa mínima e regras de preço dinâmico controladas pela operação.
- Repasse automático após conclusão, sujeito a antifraude e contestação.

### Receitas complementares

- Plano opcional para motociclistas com menor comissão e benefícios, se houver volume suficiente.
- Taxa de conveniência em determinados meios de pagamento, quando legal e claramente informada.
- Parcerias com empresas, universidades, hotéis, clínicas e comércios.
- Corridas corporativas com faturamento mensal.
- Espaços de promoção locais, sem comprometer segurança ou experiência.

### Princípios

- Nunca esconder a comissão.
- Não cobrar assinatura antes de provar valor.
- Evitar incentivos que pressionem direção insegura.
- Manter margem para suporte, antifraude, mapas, pagamentos e seguros/reservas necessárias.

---

## 10. Roadmap

### Fase 0 — Descoberta e conformidade (2–4 semanas)

- Entrevistas com passageiros e motociclistas.
- Definição da área-piloto e municípios atendidos.
- Validação jurídica, termos, privacidade e requisitos de cadastro.
- Definição da tarifa inicial e modelo de comissão.
- Escolha de mapas, pagamentos, hospedagem e suporte.

### Fase 1 — MVP operacional (8–12 semanas)

- App passageiro e app motociclista Android.
- Login, documentos, mapa, solicitação e despacho.
- Corrida com estados em tempo real.
- Pix/cartão, comissão, repasse e recibo.
- Avaliação, emergência, suporte básico e painel administrativo.
- Testes internos e piloto controlado.

### Fase 2 — Piloto público controlado (4–8 semanas)

- Operação em bairros selecionados de Fortaleza.
- Grupo inicial de motociclistas aprovados.
- Monitoramento diário de segurança, cancelamentos e suporte.
- Ajustes de tarifa, despacho e onboarding.
- Expansão progressiva para mais bairros.

### Fase 3 — Região Metropolitana

- Avaliar cada município antes da ativação.
- Adaptar áreas, regras, suporte e pontos de alta demanda.
- Campanhas locais e parcerias.
- Melhorias de disponibilidade e prevenção de fraude.

### Fase 4 — Versão completa

- iOS, agendamento, recorrência, corporativo e carteira de benefícios.
- Inteligência de demanda e otimização de despacho.
- Centro de segurança e suporte ampliado.
- Programa estruturado de fidelidade e indicação.

---

## 11. Riscos e decisões pendentes

- Regulamentação pode variar por município e sofrer atualização.
- Acidentes e segurança exigem protocolos, treinamento, suporte e avaliação jurídica de seguros.
- Pagamento com split depende de provedor que aceite marketplace e repasses a múltiplos motociclistas.
- A operação precisa de equipe para validar documentos e tratar incidentes.
- A qualidade depende de densidade mínima de motociclistas em cada área.
- O nome, marca, empresa responsável, tarifa inicial e comissão ainda precisam ser definidos.

## 12. Critério de pronto para o piloto

O piloto só começa quando um passageiro e um motociclista aprovados conseguirem concluir uma corrida ponta a ponta, com rota, tarifa, pagamento/repasse, localização, recibo, avaliação, registro de suporte e trilha de auditoria funcionando.
