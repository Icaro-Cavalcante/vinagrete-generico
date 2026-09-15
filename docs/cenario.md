# Cenário Industrial, Mercado de TCG e Encaixe da Solução

> **Documentação de Domínio e Contextualização do Projeto**  
> **Trabalho de Conclusão de Capacitação (TCC) — PNAAT 2026**  
> **Turma A – Tarde | Juazeiro do Norte – CE**  
> **Equipe Vinagrete:** Elilúcio Teixeira · Icaro Cavalcante · Gabriel Souza · Samuel Jackson  

---

## 1. Introdução e Visão Geral

Este documento detalha o embasamento contextual, mercadológico e industrial que orienta o desenvolvimento do **Sistema de Inspeção Visual de Cartas TCG por Edge AI e IoT**. 

O projeto surge da resolução do **Cenário 3 do PNAAT (Indústria de Bens de Consumo)**, instanciado com rigor técnico na cadeia de manufatura gráfica de alta precisão de **Cartas Colecionáveis (*Trading Card Games* — TCG)**, com ênfase no ecossistema de cartas colecionáveis Pokémon.

Aqui são exploradas as características do mercado de TCG, as dores industriais típicas da etapa final de corte e embalagem, a correlação analógica direta com o problema genérico proposto pela capacitação, a adequabilidade da solução desenvolvida e os vetores de escalabilidade para implantação fabril em larga escala.

---

## 2. O Cenário de Referência do PNAAT (Cenário 3: Bens de Consumo)

O programa de capacitação PNAAT estabeleceu cenários industriais baseados em desafios reais de manufatura 4.0. O **Cenário 3** foca nas etapas finais de **embalagem, rotulagem e expedição** em indústrias de bens de consumo, onde se observa um gargalo crítico:

* **O Problema:** Frascos, recipientes, caixas e produtos acabados chegam ao final da linha fabril com alto índice de não conformidades visuais — etiquetas ausentes, rótulos tortos, rasgados, decalques desalinhados ou impressões borradas.
* **Causa Raiz:** O desgaste mecânico de facas industriais, descalibração de aplicadores pneumáticos, oscilações térmicas em esteiras e a alta velocidade do maquinário impedem que inspeções humanas manuais mantenham consistência sem paralisar a linha.
* **Impactos Operacionais e Financeiros:**
  1. **Rejeição Sumária de Lotes:** Varejistas e grandes distribuidores recusam remessas completas mediante amostragem visual não conforme.
  2. **Custo Crítico de Logística Reversa:** Recolhimento, frete de devolução e reintegração de produtos refugados geram custos desproporcionais.
  3. **Retrabalho Oneroso:** Operadores humanos precisam ser alocados para triagem manual exaustiva pós-expedição.
  4. **Degradação da Marca:** A presença de produtos com acabamento defeituoso nas prateleiras prejudica a percepção de qualidade pelo consumidor final.

A diretiva central do Cenário 3 é conceber uma **solução automatizada, de baixo custo, não invasiva ao fluxo produtivo e de alta confiabilidade**, capaz de inspecionar individualmente os itens em movimento, acusar defeitos imediatamente e registrar a rastreabilidade do processo.

---

## 3. Instanciação do Problema: O Mercado de Cartas Colecionáveis (TCG)

A equipe escolheu instanciar o Cenário 3 na manufatura gráfica de **Cartas Colecionáveis (TCG)**. Trata-se de um setor singular onde o produto *é* a própria impressão gráfica cortada, e no qual desvios submilimétricos transformam um item valioso em refugo comercial.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   MERCADO GLOBAL DE TCG EM NÚMEROS                    │
│                                                                        │
│   US$ 4,5+ Bilhões/ano       60+ Bilhões de Cartas      Notas 1 a 10   │
│   Mercado Primário Global    Pokémon produzidas        Grading PSA/BGS │
│   (crescimento ~8% a.a.)     (escala massiva)          (multiplicador) │
└────────────────────────────────────────────────────────────────────────┘
```

### 3.1. Panorama e Economia do Mercado de Cartas Colecionáveis
O segmento de cartas colecionáveis (impulsionado por franquias consagradas como *Pokémon TCG*, *Magic: The Gathering*, *Yu-Gi-Oh!* e cartas esportivas) deixou de ser mero nicho de brinquedos infanto-juvenis e consolidou-se como um mercado financeiro de ativos alternativos, movimentando mais de **US$ 4,5 bilhões anuais globalmente**, com projeções de ultrapassar US$ 10 bilhões até 2030.

Nesse modelo de negócios, uma carta avulsa pode variar de alguns centavos de real até dezenas de milhares de dólares. Essa disparidade de valor é estritamente ditada pelo **estado de conservação e pela perfeição de manufatura original** do item no momento em que sai do pacote selado (*pack-fresh*).

### 3.2. A Cultura do *Grading* e a Sensibilidade Extrema à Geometria
A indústria colecionável é regulada por empresas independentes de certificação e graduação de autenticidade/qualidade (*Grading Companies*), como **PSA (*Professional Sports Authenticator*)**, **BGS (*Beckett Grading Services*)** e **CGC Cards**. 

Essas certificadoras submetem a carta a inspeção microscópica e atribuem notas de 1 a 10:
* Uma carta com nota **10 ("Gem Mint")** pode valer **10 a 50 vezes mais** do que o mesmo exemplar com nota **8 ou 9**.
* O critério mais rigoroso avaliado pelas mesas de grading é a **Centralização (*Centering*)**: a proporção matemática entre as bordas superior/inferior e esquerda/direita da carta. Para receber nota máxima, a tolerância de corte é de 55/45% na face frontal; qualquer desvio superior rebaixa a nota sumariamente.

### 3.3. A Anatomia do Defeito: O Fenômeno do *Miscut* (Erro de Guilhotinamento)
No fluxo fabril de TCG, as cartas são impressas em folhas industriais contínuas contendo centenas de exemplares (*uncut sheets*). A etapa seguinte consiste na passagem por guilhotinas rotativas e matrizes de corte-e-vinco (*die-cutting*), responsáveis por separar os cartões no padrão internacional de **63 x 88 mm** (padrão standard Pokémon/Magic) com cantos arredondados.

O **Miscut** ocorre quando a folha gráfica avança com desalinhamento mecânico, vibrando sobre a esteira ou entrando com rotação angular em relação ao eixo da guilhotina. O corte atinge a área de arte da carta ou expõe a borda branca de impressão (*alignment dot* / folha adjacente):

```
       CARTA CONFORME (GOOD)                   CARTA NÃO CONFORME (MISCUT)
  ┌──────────────────────────────┐          ┌──────────────────────────────┐
  │ ┌──────────────────────────┐ │          │┌──────────────────────────┐  │ ◄─ Margem
  │ │                          │ │          ││                          │  │    superior
  │ │                          │ │          ││                          │  │    ausente
  │ │      ARTE CENTRAL        │ │          ││      ARTE DESLOCADA      │  │
  │ │      CENTRALIZADA        │ │          ││                          │  │
  │ │                          │ │          ││                          │  │
  │ │                          │ │          ││                          │  │
  │ └──────────────────────────┘ │          │└──────────────────────────┘  │ ◄─ Arte cortada
  │                              │          │══════════════════════════════│ ◄─ Borda branca
  └──────────────────────────────┘          └──────────────────────────────┘    exposta
      Margens simétricas (50/50)                 Corte fora de registro
```

Se cartas com *miscut* forem seladas dentro de *booster packs* e distribuídas:
1. **Lotes inteiros de produtos lacrados são contestados**, gerando desconfiança sobre a integridade da linha da gráfica homologada (ex: Cartamundi, Millennium Print Group).
2. O consumidor final exige troca ou cancelamento direto no suporte da editora (The Pokémon Company / Wizards of the Coast), transferindo o passivo diretamente para a gráfica contratada.

---

## 4. Relação e Analogia entre o Cenário 3 PNAAT e a Produção Gráfica de TCG

A escolha de cartas colecionáveis não é apenas um estudo de caso atraente; ela representa uma **instanciação metodológica perfeita das restrições do Cenário 3 do PNAAT**, elevando o nível de exigência dos requisitos técnicos:

| Requisito Geral do Cenário 3 (PNAAT) | Problema Análogo na Indústria Geral | Instanciação em Cartas TCG (Equipe Vinagrete) |
| :--- | :--- | :--- |
| **Integridade da Identificação** | Rótulo rasgado, ausente ou ilegível em frasco de sabonete / xampu. | Falha de corte na arte e perda dos elementos informativos da carta (texto de jogo, borda). |
| **Alinhamento e Simetria** | Etiqueta colada em ângulo oblíquo ou deslocada no frasco. | **Miscut:** Deslocamento milimétrico da linha de corte em relação ao centro geométrico da arte. |
| **Critério de Tolerância** | Tolerância visual macroscópica (~2 a 5 mm de erro aceitável). | **Tolerância submilimétrica (< 0,5 mm):** Qualquer perda de simetria visível desclassifica o item. |
| **Resposta Operacional** | Sinalização para o operador remover a embalagem torta da esteira. | Interrupção imediata da esteira, sinal sonoro/luminoso e foto persistida em banco para auditoria. |
| **Gargalo de Cadência** | Linhas de alta velocidade onde o olho humano falha por fadiga. | Esteiras contínuas pós-corte onde milhares de cartas são empilhadas por hora. |

Assim, validar com sucesso a classificação visual de cartas TCG garante que os algoritmos de visão e a arquitetura de controle IoT são robustos o suficiente para serem replicados em aplicações industriais mais tolerantes (como rótulos em latas, garrafas ou caixas cartonadas).

---

## 5. Proposta da Solução e Encaixe no Mercado (Market Fit)

### 5.1. A Célula Automatizada de Inspeção na Borda (Edge AI + IoT)
Para resolver esse problema, a Equipe Vinagrete desenhou uma célula física automatizada de baixo custo composta por:
1. **Atuação Determinística (ESP32-S3 + FreeRTOS):** Controla o motor da esteira, gerencia botões industriais, lê interrupções físicas e comanda sinalizadores (LED vermelho industrial e Buzzer sonoro) afim de simular uma esteira industrial real.
2. **Olho Cognitivo de Borda (Raspberry Pi 5 + Pi Camera CSI):** Executa captura contínua de quadros em RAM via DMA (`Picamera2`) com latência inferior a 15 ms, garantindo a eliminação de *motion blur* através da coordenação com a esteira.
3. **Visão Computacional e Inteligência Artificial:**
   * **Detecção de Movimento por Subtração de Fundo (MOG2):** Monitora a Região de Interesse (ROI) da esteira, identificando quando o cartão atinge o enquadramento ideal.
   * **Classificação Binária Especializada (YOLOv8-cls):** Rede neural convolucional leve homologada com as classes exclusivas **`GOOD`** e **`MISCUT`**, treinada com dataset real proprietário de mais de 300 imagens em condições de bancada controlada.
4. **Supervisão e Rastreabilidade (FastAPI + SQLite WAL + Dashboard Web):** Cada desvio de corte gera gravação transacional de timestamp, nível de confiança estatística da rede e imagem anotada, exibidos em tempo real para os supervisores de turno.

```
       FLUXO INTEGRADO DE CONTROLE E VISÃO (MARKET SOLUTION)

    [ Esteira em Movimento ] ──► Carta entra na área de captura
                                          │
                                          ▼
                         [ Visão MOG2 na Raspberry Pi 5 ]
                         Detecta carta centralizada na ROI
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
         Envia "STOP\n" (UART)                        Captura Frame DMA (RAM)
                  │                                               │
                  ▼                                               ▼
         [ ESP32 para motor ]                         [ Inferência YOLOv8-cls ]
                  │                                               │
                  └───────────────────────┬───────────────────────┘
                                          │
                                 Classificação
                                  ┌───────┴───────┐
                                  ▼               ▼
                               [ GOOD ]       [ MISCUT ]
                                  │               │
                            Religa motor          ├─► Envia "DEFECT\n" (UART) ──► LED + Buzzer
                            sem gravar            ├─► Grava SQLite + Foto /uploads
                                                  └─► Alerta no Dashboard Web
```

### 5.2. Proposta de Valor Industrial e Retorno sobre Investimento (ROI)
A viabilidade comercial da solução se sustenta em três pilares principais:


* **Detecção Precoce de Desgaste de Ferramental:** Se uma faca de guilhotina perde o fio ou descalibra um dos rolamentos guia, ela não produz uma única carta com *miscut*, mas sim centenas de cartas com o mesmo corte deslocado. O mecanismo de **Controle de Danos** (que monitora uma quantidade configurável de cartas seguidas danificadas) alerta a manutenção antes que uma bobina ou resma completa de papel especial laminado seja descartada.
* **Preservação do Valor Agregado da Marca:** Elimina o risco de cartas não conformes chegarem ao mercado final, blindando o contrato entre a gráfica e as distribuidoras de jogos colecionáveis.

---

## 6. Escalabilidade e Aplicação em Casos Reais

### 6.1. Generalização para Outros Segmentos da Indústria de Bens de Consumo
A arquitetura de visão baseada em **Subtração de Fundo + Classificação Convolucional na Borda** foi projetada para ser modular e agnóstica ao produto. Sua aplicação estende-se diretamente a:

* **Indústria de Rótulos e Embalagens Adesivas:** Identificação de rótulos impressos fora de registro ou descolamento de liner em esteiras de frascos cosméticos e farmacêuticos.
* **Manufatura de Peças Técnicas de EVA e Borracha:** Verificação de rebarbas e desvios de corte em matrizes de corte-e-vinco para solados de calçados e isoladores industriais.
* **Indústria Gráfica Editorial e Promocional:** Controle de corte em baralhos comuns, cartões de visita de alta gramatura, cartões bancários de PVC e capas duras de livros.
* **Etiquetagem em Caixas de Papelão:** Validação de código de barras e alinhamento de etiquetas de rastreabilidade logística em centros de distribuição de e-commerce.

### 6.2. Escalabilidade Tecnológica e Evolução Arquitetural
Para transitar do protótipo de bancada para uma planta fabril contínua de grande porte, os seguintes caminhos de evolução técnica são previstos:

1. **Iluminação Estruturada e Cúpula Difusa (Dome Light):** Em ambiente fabril real com iluminação ambiente variável, a bancada deve receber cúpula difusa de iluminação LED polarizada, eliminando reflexos especulares causados pelo acabamento metalizado (*foil/holográfico*) de cartas raras.
2. **Integração com Mecanismo Físico de Rejeição (Pneumático):** Adição de um atuador solenoide ou bico de sopro de ar comprimido acionado por GPIO do ESP32 logo após a saída da câmera, desviando cartas defeituosas para um cesto de refugo sem intervenção humana.
3. **Cluster de Inspeção Multilinha com Gerenciamento Centralizado:** O backend FastAPI e o banco de dados podem ser centralizados em um servidor local da fábrica (on-premises via Docker), recebendo dados de telemetria de dezenas de células de corte simultaneamente via MQTT ou HTTP REST, com visualização unificada em dashboard industrial Grafana ou supervisório corporativo.
4. **Pipeline MLOps Fechado:** Coleta automatizada de imagens com baixa margem de confiança (ex: confiança entre 50% e 65%) para reenvio à nuvem (Roboflow), re-treinamento periódico e distribuição de novos pesos (`best.pt`) over-the-air (OTA) para as Raspberry Pis da fábrica.

---

## 7. Resumo de Atendimento aos Critérios de Avaliação

| Dimensão Avaliada | Como o Projeto Vinagrete Responde |
| :--- | :--- |
| **Alinhamento com o PNAAT** | Instanciação fiel do Cenário 3 (Bens de Consumo / Embalagem / Falha Visual). |
| **Complexidade e Desafio Técnico** | Integração de hardware heterogêneo (ESP32-S3 + FreeRTOS com Raspberry Pi 5 + Linux + Edge AI + Docker). |
| **Inovação Aplicada** | Combinação de parada sincronizada por Background Subtraction com classificação ultrarrápida YOLOv8-cls em substituição a sensores lentos ou câmeras industriais inacessíveis. |
| **Rastreabilidade e Governança** | Métricas operacionais em tempo real, auditoria por imagem armazenada, histórico por lote de produção e API REST aberta para integração. |
| **Viabilidade Econômica** | Proposta de alto valor industrial realizável com componentes acessíveis de prateleira (*commercial off-the-shelf* — COTS). |
