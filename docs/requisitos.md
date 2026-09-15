# Especificação de Requisitos, Regras de Negócio e Rastreabilidade

> **Documento de Engenharia de Requisitos de Software e Sistemas**  
> **Conforme Padrão IEEE 29148 / Karl Wiegers**  
> **Trabalho de Conclusão de Capacitação (TCC) — PNAAT 2026**  
> **Turma A – Tarde | Juazeiro do Norte – CE**  
> **Equipe Vinagrete:** Elilúcio Teixeira · Icaro Cavalcante · Gabriel Souza · Samuel Jackson  

---

## 1. Introdução e Escopo do Documento

Este documento consolida a especificação formal de engenharia de requisitos do **Sistema de Inspeção Visual de Cartas TCG por Edge AI e IoT**. 

O documento segue as diretrizes da norma internacional **IEEE 29148 (Requirements Engineering)** e as práticas de **Karl Wiegers**, articulando:
1. **Requisitos Funcionais (RF):** O que o sistema deve executar de forma observável e mensurável;
2. **Requisitos Não-Funcionais (RNF):** Propriedades de qualidade, desempenho, determinismo e segurança da solução;
3. **Regras de Negócio (RN):** Políticas operacionais, critérios de conformidade e restrições industriais do processo;
4. **Matrizes de Rastreabilidade Bidirecional:** O mapeamento que garante que cada requisito esteja associado a seus arquivos de código, regras de negócio e procedimentos de validação e aceite.

---

## 2. Requisitos Funcionais (RF)

| ID | Nome do Requisito | Descrição Detalhada | Critério de Aceite |
| :---: | :--- | :--- | :--- |
| **RF-01** | **Detecção de Presença por Visão** | O sistema deve monitorar continuamente a Região de Interesse (ROI) da esteira via algoritmo de Subtração de Fundo (*Background Subtraction* MOG2 na Raspberry Pi 5), identificar quando uma carta atinge a posição central e comandar a parada imediata da esteira (`STOP\n`). | Identificar a carta centralizada na ROI com tolerância vertical de $\pm 35\text{ px}$ e enviar `STOP\n` para frenagem em menos de $15\text{ ms}$. |
| **RF-02** | **Captura em Memória RAM (DMA)** | A câmera digital deve capturar o frame estático com a esteira imobilizada diretamente do buffer DMA em RAM, utilizando driver de vídeo contínuo (`Picamera2`/V4L2) para eliminar borrões de movimento (*motion blur*). | Latência de leitura do frame em regime permanente menor que $25\text{ ms}$ e ausência de arrasto visual na imagem. |
| **RF-03** | **Inferência de IA (YOLOv8-cls)** | O pipeline de visão deve executar modelo de rede neural convolucional leve (YOLOv8n-cls) sobre a imagem capturada, classificando a carta nas categorias mutuamente exclusivas: **`GOOD`** (Conforme) ou **`MISCUT`** (Defeituosa). | Classificação executada localmente (na borda) retornando classe predita e grau de confiança estatística com limiar $\ge 50\%$. |
| **RF-04** | **Controle Físico da Esteira** | O microcontrolador ESP32-S3 deve comutar o motor DC da esteira via transistor Darlington TIP122, respondendo tanto ao pressionamento manual da botoeira quanto a ordens seriais da Raspberry Pi (`STOP\n` e `START\n`). | Partida e frenagem do motor respondendo em tempo real, mantendo velocidade estável sob carga nominal. |
| **RF-05** | **Comunicação Serial Cabeada** | A troca de dados e telemetria entre o ESP32-S3 e a Raspberry Pi 5 deve ocorrer via enlace serial UART ponto a ponto a $115.200\text{ bps}$ em nível lógico $3.3\text{V TTL}$, utilizando protocolo baseado em strings ASCII terminadas em `\n`. | Transmissão e recepção sem corrupção de caracteres em regime contínuo, com buffer de recepção dedicado no FreeRTOS. |
| **RF-06** | **Sinalização de Defeito Pontual** | Ao detectar uma carta com defeito (`MISCUT`), a Raspberry Pi deve enviar o sinal `DEFECT\n`, fazendo o ESP32-S3 acionar o LED Vermelho e o Buzzer por um pulso contínuo de $1000\text{ ms}$. | Emissão de 1 pulso audiovisual de $1000\text{ ms}$ para cada refugo isolado, sem paralisar a esteira permanentemente. |
| **RF-07** | **Sinalização de Estado do Sistema** | O microcontrolador deve emitir feedback sonoro e luminoso de estado: **1 pulso curto ($500\text{ ms}$)** ao ligar o sistema (`SYS_ON`) e **2 pulsos curtos ($500\text{ ms}$ ON / $500\text{ ms}$ OFF)** ao desligar (`SYS_OFF`). | Diferenciação acústica clara e imediata a cada transição de estado da máquina. |
| **RF-08** | **Controle de Danos e Modo ALERTA** | O sistema deve monitorar a ocorrência de defeitos consecutivos. Caso sejam detectados $X$ `MISCUT`s consecutivos (onde $X$ é configurável, padrão $= 3$), o sistema deve entrar em **ALERTA**, desligar o motor e acionar sinalização oscilante contínua ($500\text{ ms}$ ON / $500\text{ ms}$ OFF) até intervenção do operador. | A esteira permanece parada proativamente, impedindo a continuidade de cortes defeituosos por desgaste da guilhotina. |
| **RF-09** | **Persistência Relacional e Auditoria** | Cada inspeção realizada deve ser registrada transacionalmente no banco SQLite. Para cartas aprovadas (`GOOD`), incrementam-se apenas os contadores; para cartas com defeito (`MISCUT`), gravam-se: `cartas_totais`, `carta_defeituosas`, `incio_leitrua`, `fim_leitura` e `status` UTC e o arquivo JPEG anotado em `/uploads`. | Persistência íntegra de metadados e persistência de imagem anotada em disco permitindo auditoria visual remota. |
| **RF-10** | **Ciclo de Vida Automático de Lotes** | O início de um novo lote de produção com identificador incremental no SQLite deve ocorrer de forma automatizada ao ligar a esteira (`SYS_ON`), e o encerramento com gravação de data/hora final deve ocorrer ao desligar a esteira (`SYS_OFF`). | Todas as cartas inspecionadas entre a partida e a parada ficam atreladas ao mesmo `id_lote` no banco de dados. |
| **RF-11** | **API REST para Supervisão** | O backend deve disponibilizar endpoints REST documentados (Swagger/OpenAPI) em FastAPI para registro de dados, encerramento de lotes e consulta agregada de métricas operacionais. | Endpoints respondem com código HTTP 200 e payload JSON estruturado conforme schemas Pydantic v2. |
| **RF-12** | **Dashboard Web do Operador** | A aplicação deve fornecer uma interface gráfica web responsiva servida via Nginx (porta 80), atualizada via polling assíncrono, exibindo: status da máquina, total de cartas, taxa percentual de refugo, gráfico por horário e galeria de fotos dos defeitos. | Atualização em tempo real (intervalo de $2\text{ s}$) sem interferir ou degradar o loop de inspeção da câmera na esteira. |

---

## 3. Requisitos Não-Funcionais (RNF)

| ID | Categoria | Descrição Detalhada | Métrica / Critério de Aceite |
| :---: | :--- | :--- | :--- |
| **RNF-01** | **Desempenho e Latência** | O ciclo completo de inspeção de cada carta (parada mecânica + captura de frame + inferência YOLO + decisão) não deve exceder $500\text{ ms}$. A captura isolada do frame em memória não deve ultrapassar $25\text{ ms}$. | Mediana de latência de captura $< 25\text{ ms}$ validada pelo script `benchmark_camera.py`. Ciclo total $< 500\text{ ms}$. |
| **RNF-02** | **Determinismo do Firmware** | As tarefas do microcontrolador ESP32-S3 devem ser executadas sob o FreeRTOS com prioridades preemptivas isoladas, garantindo que o filtro de *debounce* de $50\text{ ms}$ da botoeira não sofra preempção por I/O serial. | Ausência de chamadas bloqueantes no loop principal; tempo de resposta da botoeira $< 60\text{ ms}$. |
| **RNF-03** | **Confiabilidade da Persistência** | O banco de dados SQLite deve operar com modo de registro antecipado (*Write-Ahead Logging* — WAL) habilitado, prevenindo travamentos ou corrupção de dados em acessos concorrentes simultâneos (escrita do pipeline e leitura da API REST). | `PRAGMA journal_mode=WAL;` e `busy_timeout=5000` ativos na inicialização do SQLAlchemy. |
| **RNF-04** | **Reprodutibilidade do Ambiente** | O sistema completo (firmware, backend e visão) deve ser totalmente configurável a partir de variáveis centrais de ambiente (`config.py`), permitindo implantação em ambiente limpo sem dependências manuais não documentadas. | Execução reprodutível via `docker-compose.yml` e scripts Python documentados no `README.md`. |
| **RNF-05** | **Modularidade e Isolamento** | A camada de supervisão (Backend FastAPI e Frontend Web Nginx) deve ser empacotada em contêineres Docker independentes e desacoplados, isolando a interface administrativa das tarefas críticas de borda. | Falha ou reinicialização do dashboard web não interrompe o funcionamento físico da esteira ou da inspeção. |
| **RNF-06** | **Portabilidade do Firmware** | O firmware de controle do motor deve ser compilável através do framework nativo Espressif ESP-IDF v5.1+, sem dependências de bibliotecas de terceiros ou frameworks proprietários fora do padrão C/POSIX. | Build limpo via `idf.py build` para alvo `esp32s3`. |
| **RNF-07** | **Imunidade Eletromagnética e Segurança** | O circuito físico deve incorporar desacoplamento de terra comum e proteção contra sobretensão indutiva através de diodo de retorno (*flyback*) no motor, além de resistor limitador na base do transistor e no LED. | Ausência de ruídos ou reinicializações expontâneas (*brownouts*) no ESP32 durante a comutação de carga indutiva do motor DC. |

---

## 4. Regras de Negócio (RN)

As regras de negócio definem a lógica operacional inviolável do sistema produtivo:

```
                  DIAGRAMA DE TRANSIÇÃO DE ESTADOS DO SISTEMA

              ┌──────────────────────────────────────────────┐
              │                                              │
              ▼                                              │
      [ ESTADO INATIVO ] ──(Clique Botoeira / SYS_ON)───────►│
      (Motor desligado)                                      │
              ▲                                              ▼
              │                                     [ ESTADO ATIVO ]
              │                                     (Lote incremental aberto)
              │                                     (Esteira em movimento)
              │                                              │
     (Clique Botoeira /                                      ▼
         SYS_OFF)                                  [ CARTA DETECTADA ]
              │                                     (Comando STOP enviado)
              │                                     (YOLOv8 classifica)
              │                                              │
              │                       ┌──────────────────────┴──────────────────────┐
              │                       ▼                                             ▼
              │                  [ CARTA GOOD ]                               [ CARTA MISCUT ]
              │                  (Contador seq = 0)                           (Contador seq += 1)
              │                  (Esteira retoma / START)                     (Emite 1s bip / DEFECT)
              │                       │                                       (Persiste no SQLite)
              │                       │                                             │
              │                       │                         ┌───────────────────┴───────────────────┐
              │                       │                         ▼                                       ▼
              │                       │                (seq < Threshold)                       (seq >= Threshold)
              │                       │                (Esteira retoma / START)                         │
              │                       │                         │                                       ▼
              │                       │                         │                              [ MODO DE ALERTA ]
              │                       │                         │                              (Esteira travada)
              │                       │                         │                              (Sirene oscilante)
              │                       ▼                         ▼                                       │
              │                 [ AGUARDA SAÍDA DA CARTA / COOLDOWN ]                                   │
              │                                 │                                                       │
              └─────────────────────────────────┴───────────────────────────────────────────────────────┘
```

### RN-01: Ciclo de Vida Único de Lote de Produção
* O sistema opera estritamente com **um único lote ativo no estado `"EM_ANDAMENTO"`** por vez.
* No instante em que o operador pressiona a botoeira para ligar o sistema (`SYS_ON`), o backend encerra qualquer lote pendente anterior e cria um novo registro na tabela `lotes` com ID autoincremental (`id = last_id + 1`), `cartas_totais = 0`, `cartas_defeituosas = 0` e `inicio_leitura = now(UTC)`.
* Quando o sistema é desligado (`SYS_OFF`), o lote corrente é atualizado para `status = "CONCLUIDO"` (ou `"ENCERRADO"`) com o preenchimento de `fim_leitura`.
* Todas as cartas inspecionadas durante o período de funcionamento são vinculadas obrigatoriamente à chave estrangeira `id_lote` do lote ativo.

### RN-02: Política de Decisão e Descarte de Dados para Peças Conformes (`GOOD`)
* Uma carta é classificada como **`GOOD`** se a rede neural predisser a classe correspondente com índice de confiança estatística superior ao limiar configurado (`CONF_THRESHOLD >= 0.50`).
* Para itens conformes, o sistema **não grava a imagem em disco nem cria linha na tabela `defeitos`** (política de preservação de I/O em cartões microSD na borda). Apenas o contador global `cartas_totais` do lote e do `sistema_estado` é incrementado.
* A detecção de uma carta conforme zera imediatamente o contador de falhas consecutivas (`sequencia_atual = 0`).
* A esteira recebe o comando `START\n` e é reativada de imediato para prosseguir a produção.

### RN-03: Política de Registro e Sinalização para Peças Defeituosas (`MISCUT`)
* Uma carta é considerada com **`MISCUT`** quando o modelo indicar corte assimétrico fora dos limites ou se a probabilidade da classe `miscut` for preponderante.
* A cada refugo confirmado:
  1. Incrementam-se os contadores `cartas_defeituosas` (do lote e global) e incrementa-se `sequencia_atual += 1`;
  2. A imagem anotada gerada pelo YOLO é codificada em JPEG e gravada na pasta física de `/uploads`;
  3. Insere-se transacionalmente um registro na tabela `defeitos` com timestamp UTC, lote de origem, grau de confiança e caminho da imagem;
  4. Despacha-se o sinal serial `DEFECT\n` para o ESP32-S3 emitir exatamente **1 pulso audiovisual de $1000\text{ ms}$**.

### RN-04: Lógica Preventiva de Controle de Danos (Modo ALERTA)
* A produção contínua de defeitos consecutivos em uma linha de corte indica desgaste severo da lâmina ou descalibração mecânica da guilhotina.
* Se a variável `sequencia_atual` atingir ou superar o limiar programável `CONSECUTIVE_DEFECTS_ALERT` (padrão $= 3$):
  1. O serviço de inferência despacha imediatamente a instrução `ALERTA\n` via UART;
  2. O motor da esteira é **permanentemente desligado** (`motor_set(false)`);
  3. O ESP32-S3 entra no estado `em_alerta = true`, acionando a tarefa `alerta_task` que comuta LED e Buzzer em padrão oscilante intermitente ($500\text{ ms}$ ON / $500\text{ ms}$ OFF tipo "UIU-UIU-UIU");
  4. O pipeline de visão **congela novas inspeções** e ignora a esteira até que o operador humano intervenha.

### RN-05: Prioridade Absoluta de Intervenção do Operador na Botoeira
* A botoeira física do operador no GPIO 6 tem precedência absoluta sobre todos os comandos de software.
* Se a botoeira for pressionada enquanto o sistema estiver no modo **ALERTA**, a ação é interpretada estritamente como ordem de **DESLIGAMENTO E MANUTENÇÃO**:
  * O alarme contínuo é cancelado imediatamente (`em_alerta = false`);
  * O sistema é forçado para o estado inativo (`sys_on = false`);
  * O motor é desenergizado;
  * São emitidos os 2 bips de encerramento do sistema;
  * É despachada a instrução `SYS_OFF\n` via UART para a Raspberry Pi fechar o lote de produção no banco de dados.

### RN-06: Cooldown Mecânico e Eliminação de Falsos Re-Disparos
* Após inspecionar uma carta e emitir a instrução `START\n` para o motor da esteira:
  1. O detector de movimento entra compulsoriamente no estado transitório `ItemState.EXITING`;
  2. Impõe-se uma trava temporal mínima de $1.5\text{ s}$ (`min_exit_time_sec`), durante a qual **nenhum novo gatilho de parada pode ser gerado sob nenhuma hipótese**;
  3. A transição de volta para o estado `SEARCHING` (pronto para o próximo item) exige que o contorno da carta atual ultrapasse o terço inferior de saída da ROI (`cy > roi_center_y + 60`) OU que a ROI permaneça sem qualquer contorno por pelo menos 5 frames consecutivos (`empty_frames_count >= 5`);
  4. Antes de liberar o próximo ciclo, o pipeline descarta ativamente 8 frames do buffer da câmera para limpar resíduos ópticos.

---

## 5. Matrizes de Rastreabilidade Bidirecional

### 5.1. Matriz de Rastreabilidade: Requisitos Funcionais $\longleftrightarrow$ Componentes de Software/Hardware

| ID Requisito | Camada do Sistema | Arquivo(s) de Código de Implementação | Função / Símbolo Principal |
| :--- | :--- | :--- | :--- |
| **RF-01** | Visão / Borda | `inference/motion_detector.py`<br>`inference/serial_handler.py` | `MotionDetector.detect_motion_centered()`<br>`communicator.send_command("STOP\n")` |
| **RF-02** | Visão / Câmera | `inference/camera.py` | `CameraController.capture_frame()` (Picamera2 / GStreamer DMA) |
| **RF-03** | Inteligência Artificial | `inference/detector.py` | `YOLOInference.predict()` (`weights/best.pt`) |
| **RF-04** | Automação Física | `motor/main/main.c` | `motor_set()`, `botoeira_task()`, `uart_rx_task()` (TIP122 no GPIO 7) |
| **RF-05** | Comunicação Serial | `motor/main/main.c`<br>`inference/serial_handler.py` | `uart_init()`, `uart_rx_task()` (GPIO 17/18)<br>`SerialCommunicator` (pyserial 115200) |
| **RF-06** | Sinalização de Falha | `motor/main/main.c` | `sinalizar_pulso_ms(1000)` disparado pelo comando `DEFECT` |
| **RF-07** | Sinalização de Status | `motor/main/main.c` | `sinalizar(1)` no `SYS_ON`, `sinalizar(2)` no `SYS_OFF` |
| **RF-08** | Controle de Danos | `inference/serial_handler.py`<br>`motor/main/main.c` | Contador `consecutive_defects` $\ge$ `CONSECUTIVE_DEFECTS_ALERT`<br>`alerta_task()` acionada por `ALERTA` |
| **RF-09** | Persistência Relacional | `backend/models.py`<br>`backend/crud.py`<br>`inference/pipeline.py` | Modelos `Defeito`, `Lote`, `SistemaEstado`<br>`registrar_inspecao_com_dados()`<br>`salvar_imagem_base64()` |
| **RF-10** | Ciclo de Lotes | `inference/serial_handler.py`<br>`backend/crud.py` | Chamadas `iniciar_lote(db)` e `encerrar_lote(db)` no tráfego serial |
| **RF-11** | Backend & API REST | `backend/main.py`<br>`backend/schemas.py` | Endpoints `/api/inspecao/registrar`, `/api/lote/*`, `/api/dashboard-summary` |
| **RF-12** | Interface do Operador | `frontend/index.html`<br>`frontend/script.js`<br>`frontend/nginx.conf` | Polling `fetchDashboardData()`, renderização Chart.js e galeria |

---

### 5.2. Matriz de Rastreabilidade: Requisitos Funcionais $\longleftrightarrow$ Regras de Negócio

| ID Requisito | Regra(s) de Negócio Associada(s) | Descrição do Vínculo Operacional |
| :---: | :---: | :--- |
| **RF-01** | RN-06 | O gatilho de presença só pode ocorrer quando respeitado o cooldown e o descarte temporal mecânico da saída do item anterior. |
| **RF-03** | RN-02, RN-03 | A classe de saída da IA determina o disparo da rota de aprovação (RN-02) ou da rota de refugo com contagem para alarme (RN-03). |
| **RF-04** | RN-04, RN-05 | A comutação de motor respeita a prioridade de desligamento da botoeira (RN-04) e as pausas de frenagem do ciclo de corte (RN-05). |
| **RF-06** | RN-03 | O pulso longo de $1000\text{ ms}$ é reservado exclusivamente para defeitos pontuais, antes de atingir o threshold de alarme. |
| **RF-07** | RN-01, RN-05 | Os pulsos de estado confirmam fisicamente a abertura (1 bip) e o fechamento (2 bips) de um lote industrial. |
| **RF-08** | RN-03, RN-04 | O modo de alarme contínuo é governado pelo threshold da RN-03 e desarmado exclusivamente pela intervenção humana da RN-04. |
| **RF-09** | RN-01, RN-02, RN-03 | A política de persistência grava imagens apenas para refugo (RN-02/RN-03) e associa toda medição ao lote corrente (RN-01). |
| **RF-10** | RN-01 | Abertura e fechamento de lotes ocorrem de forma 100% acoplada à máquina de estados física de partida e parada. |

---

### 5.3. Matriz de Métodos de Verificação e Critérios de Aceite (IEEE 29148)

| ID Requisito | Método de Verificação | Procedimento de Teste | Critério de Sucesso |
| :---: | :---: | :--- | :--- |
| **RF-01** | Demonstração / Teste | Passar carta na esteira durante execução do pipeline de visão. | A esteira desacelera e para exatamente no centro vertical da ROI sem re-disparos. |
| **RF-02** | Teste Automatizado | Execução de `pytest tests/test_camera.py` e `scripts/benchmark_camera.py`. | Latência de captura $\le 25\text{ ms}$ em 30 iterações consecutivas. |
| **RF-03** | Análise / Teste | Execução de `pytest tests/test_inference.py` com amostras de referência. | Retorno de objeto `DetectionResult` contendo classe e confiança válida. |
| **RF-04** | Inspeção Física | Medição de nível no pino GPIO 7 com multímetro/osciloscópio e comutação do motor. | Tensão de base do TIP122 vai a ~3.3V com motor ligado e 0V com motor desligado. |
| **RF-05** | Demonstração | Monitoramento de log serial via `idf.py monitor` em paralelo ao terminal Python. | Troca bidirecional de mensagens ASCII sem perda de pacotes ou caracteres nulos. |
| **RF-06** | Teste Funcional | Inserção deliberada de carta com miscut visível na esteira. | Emissão de exatamente 1 pulso de $1000\text{ ms}$ no LED/Buzzer e retomada da esteira. |
| **RF-07** | Teste Funcional | Pressionamento da botoeira para ligar e desligar. | Emissão de 1 bip de $500\text{ ms}$ ao ligar e 2 bips de $500\text{ ms}$ ao desligar. |
| **RF-08** | Teste Funcional | Inserção consecutiva de 3 cartas defeituosas. | Esteira é paralisada e o alarme oscilante ("UIU-UIU") permanece tocando indefinidamente. |
| **RF-09** | Análise de Dados | Consulta SQL direta ao banco: `SELECT * FROM defeitos ORDER BY id DESC LIMIT 5;` | Registros gravados com timestamp válido, lote preenchido e imagem acessível via URL. |
| **RF-10** | Demonstração | Ligar e desligar esteira duas vezes e consultar tabela `lotes`. | IDs de lote sequenciais gerados com início e fim corretos. |
| **RF-11** | Teste Automatizado | Consulta via cURL ou Swagger UI em `http://localhost:8000/docs`. | Resposta HTTP 200 com payload JSON válido em todos os endpoints principais. |
| **RF-12** | Inspeção Visual | Acesso ao painel web no navegador em `http://localhost:80`. | Dashboard exibe contadores em tempo real, gráfico Chart.js e fotos na galeria. |
| **RNF-01** | Teste de Desempenho | Medição com `time.perf_counter()` entre detecção e envio de resposta serial. | Tempo total do ciclo de inspeção $< 500\text{ ms}$ por cartão. |
| **RNF-02** | Teste de Carga | Pressionamento rápido repetitivo da botoeira física. | O firmware filtra ruídos via debounce e executa comutação limpa sem travar o ESP32. |
| **RNF-03** | Teste de Concorrência | Escrita intensiva de inspeções enquanto o dashboard web executa polling a cada 2s. | Ausência de erros `database is locked` e integridade das consultas com WAL. |
