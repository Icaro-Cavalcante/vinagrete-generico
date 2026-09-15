# Módulo IoT & Automação Física (ESP32-S3 / FreeRTOS)

> **Documentação de Engenharia de Hardware e Firmware**  
> **Trabalho de Conclusão de Capacitação (TCC) — PNAAT 2026**  
> **Turma A – Tarde | Juazeiro do Norte – CE**  
> **Equipe Vinagrete:** Elilúcio Teixeira · Icaro Cavalcante · Gabriel Souza · Samuel Jackson  

---

## 1. Visão Geral do Módulo

O **Módulo IoT & Automação Física** é a camada determinística de tempo real do projeto, responsável pelo controle eletromecânico da esteira transportadora, pela interface direta com o operador humano (botoeira industrial), pela emissão de alarmes audiovisuais (LED e Buzzer) e pela ponte de comunicação serial cabeada (UART) com a camada cognitiva de visão computacional (Raspberry Pi 5).

Implementado sobre o microcontrolador **ESP32-S3** utilizando o framework oficial **ESP-IDF v5.5** e o sistema operacional de tempo real **FreeRTOS**, o módulo opera sob arquitetura preemptiva com tarefas desacopladas, garantindo que rotinas com restrições rígidas de tempo (como *debounce* de botoeira, comutação de motor e acionamento de alertas) não sofram travamentos ou atrasos por processamento externo.

```
                  ARQUITETURA DA CAMADA DE AUTOMAÇÃO FÍSICA

       ┌─────────────────────────────────────────────────────────────┐
       │                   ESP32-S3 (FreeRTOS)                       │
       │                                                             │
       │  [botoeira_task]     [uart_rx_task]       [alerta_task]     │
       │  Debounce 50 ms      Escuta UART 115200   Sinalizador PWM/  │
       │  Toggle / Shutdown   Comandos STOP/START  Oscilante 500 ms  │
       └──────┬──────────────────────┬──────────────────────┬────────┘
              │                      │                      │
       GPIO 6 │               GPIO 17/18             GPIO 1 │ GPIO 2
       (Input Pull-up)        (UART1 TX/RX)                 │
              │                      │               ┌──────┴──────┐
              ▼                      ▼               ▼             ▼
          BOTOEIRA            RASPBERRY PI 5      BUZZER          LED
          (Start/Stop)        (Edge AI / Visão)   (Alarme)     (Status)
                                     │
       GPIO 7 (Saída Digital)        │
              │                      │
              ▼                      │
       [ Transistor TIP122 ] ────────┘
              │
              ▼
       [ MOTOR DA ESTEIRA ] (DC 5V-12V)
```

---

## 2. Lista de Componentes Utilizados

A tabela abaixo relaciona todos os itens de hardware utilizados na montagem da célula de automação na bancada experimental:

| Item | Componente | Qtd. | Especificação / Modelo | Função no Sistema |
| :---: | :--- | :---: | :--- | :--- |
| **1** | Microcontrolador | 1 | **ESP32-S3** | Núcleo de processamento determinístico em FreeRTOS. |
| **2** | Protoboard | 2 | Em cada board: 300 pontos (30 linhas com 5 pontos em cada uma das duas colunas) + 25 pontos - e 25 pontos + em cada lateral | Plataforma física de prototipagem dos circuitos periféricos. |
| **3** | Atuador Mecânico | 1 | Kit Esteira Transportadora Em Acrílico 35cm | Tracionamento da esteira transportadora de cartas. |
| **4** | Transistor de Potência | 1 | **TIP122 (Darlington NPN, TO-220)** | Chaveamento eletrônico de corrente do motor DC via sinal digital. |
| **5** | Resistor de Proteção Base | 1 | **2,2 kΩ** | Limitação de corrente da saída do GPIO 7 para a base do TIP122. |
| **6** | Diodo de Retorno (Flyback) | 1 | **1N4007** (1A / 1000V) | Proteção contra picos de força contraeletromotriz gerados pelo motor. |
| **7** | Sinalizador Visual | 1 | **LED Difuso Vermelho 5 mm** | Feedback visual de estado ligado, desligado e alerta de defeito. |
| **8** | Resistor do LED | 1 | **330 Ω (1/4 W, 5%)** | Limitação de corrente para proteger o LED no GPIO 2 (3.3V). |
| **9** | Sinalizador Acústico | 1 | **Buzzer Contínuo** | Sinalização sonora pulsada (feedback) e oscilante (alarme). |
| **10** | Entrada do Operador | 1 | **Push-button / Botoeira Tátil** (4 pinos) | Chave manual para ligar, desligar e desativar alarmes do sistema. |
| **11** | Cabos de Conexão | 12 | Jumpers Macho-Macho | Interconexão elétrica entre ESP32 e protoboards. |
| **12** | Alimentação Externa | 1 | Fonte DC 5V/12V (2A) | Alimentação dedicada para o motor da esteira (GND comum com ESP). |

---

## 3. Mapeamento Completo de Pinos (Pinout)

Todos os pinos foram definidos de forma a evitar colisões com pinos de strapping do ESP32-S3 e manter compatibilidade com as rotinas do ESP-IDF:

### 3.1. Pinout do ESP32-S3
| Pino ESP32-S3 | Modo I/O | Periférico Conectado | Nível Lógico / Polaridade | Descrição Funcional |
| :--- | :---: | :--- | :---: | :--- |
| **GPIO 1** | Saída Digital | Buzzer Piezoelétrico | HIGH (1) = Som ativo | Sinal sonoro de feedback e sirene oscilante de alarme. |
| **GPIO 2** | Saída Digital | LED Vermelho (via 330 Ω) | HIGH (1) = Aceso | Sinalização luminosa sincronizada com o buzzer. |
| **GPIO 6** | Entrada Digital | Botoeira do Operador | LOW (0) = Pressionado | Entrada com pull-up interno ativo. Clique comanda toggle do sistema. |
| **GPIO 7** | Saída Digital | Base do TIP122 (via 1 kΩ) | HIGH (1) = Motor LIGADO | Comuta o transistor Darlington para alimentar o motor da esteira. |
| **GPIO 17** | Saída Serial | UART1 TX $\rightarrow$ RX da Pi | 3.3V TTL (115200 bps) | Linha de transmissão serial de eventos (`SYS_ON`, `SYS_OFF`). |
| **GPIO 18** | Entrada Serial | UART1 RX $\leftarrow$ TX da Pi | 3.3V TTL (115200 bps) | Linha de recepção serial de ordens (`STOP`, `START`, `DEFECT`, `ALERTA`). |
| **GND** | Referência (0V) | Malha de Terra Comum | 0V | Conexão de referência obrigatória entre ESP32, fonte do motor e Pi 5. |

### Interconexão com a Raspberry Pi 5
Conexão via cabo serial USB/UART, **/dev/ttyUSB0**.

---

## 4. Esquema Elétrico e Montagem na Protoboard Passo a Passo

```
                               ESQUEMA DE MONTAGEM NA PROTOBOARD

               +5V (Fonte Externa do Motor)
                    │
                    ├───[ + Motor DC ]
                    │         │
                    │      [Motor] ────┐
                    │         │        │
                    │   ┌─────┴────┐   │
                    └───┤ 1N4007   ├───┤ (Diodo Flyback Catodo no + / Anodo no -)
                        │ (Diodo)  │   │
                        └──────────┘   │
                                       │
                                    Coletor (C)
                                   ┌─────────┐
    GPIO 7 (ESP32) ───[ 1 kΩ ]────┤ TIP122  │ (Darlington NPN)
                                   │ Base (B)│
                                   └────┬────┘
                                     Emissor (E)
                                        │
                                        ▼
                                    GND Comum (ESP32 + Fonte Externa)
    ──────────────────────────────────────────────────────────────────────────
    GPIO 2 (ESP32) ───[ 330 Ω ]───[ Anodo (+) LED (-) Catodo ]───► GND
    
    GPIO 1 (ESP32) ───────────────[ (+) Buzzer (-) ]────────────► GND
    
    GPIO 6 (ESP32) ───────────────[ Terminal 1 ] Push-Button
                                  [ Terminal 2 ]────────────────► GND (Pull-up interno)
```

### 4.1. Circuito 1: Acionamento do Motor  da Esteira (Chaveamento TIP122)
O pino de saída do ESP32 opera em 3.3V com corrente máxima de ~20–40 mA, o que é insuficiente para acionar diretamente um motor elétrico (que exige de 200 mA a 1.5 A). Utiliza-se um transistor Darlington NPN TIP122 como chave saturada:
1. **Base (Pino 1 do TIP122):** Conectada ao **GPIO 7** do ESP32 através de um resistor em série de **1 kΩ**. Esse resistor limita a corrente de base a cerca de $I_B \approx \frac{3.3V - 1.4V}{1000\Omega} \approx 1.9\text{ mA}$, suficiente para saturar completamente o par Darlington.
2. **Coletor (Pino 2 do TIP122):** Conectado ao polo **negativo (-)** do Motor DC.
3. **Emissor (Pino 3 do TIP122):** Conectado diretamente à trilha de **GND Comum**.
4. **Polo Positivo (+) do Motor DC:** Conectado à linha de **+5V ou +12V da fonte externa**.
5. **Diodo de Roda-Livre (1N4007):** Instalado em antiparalelo direto nos terminais do motor (Catodo com listra branca no polo positivo `+`, Anodo no polo negativo `-`). 
   > *Atenção Crítica:* A ausência do diodo causará queima instantânea do transistor e travamentos no ESP32 devido a pulsos indutivos de alta tensão gerados no momento em que a esteira é desligada.

### 4.2. Circuito 2: Sinalizador Visual (LED Vermelho)
1. Conecte o terminal longo do LED (Anodo, `+`) a uma das pernas do resistor de **330 Ω**.
2. Conecte a outra perna do resistor de 330 Ω ao **GPIO 2** do ESP32-S3.
3. Conecte o terminal chanfrado/curto do LED (Catodo, `-`) ao barramento de **GND**.

### 4.3. Circuito 3: Sinalizador Acústico (Buzzer Piezoelétrico)
1. Conecte o pino positivo do buzzer (`+`, identificado na carcaça plástica) ao **GPIO 1** do ESP32-S3.
2. Conecte o pino negativo do buzzer (`-`) ao barramento de **GND**.

### 4.4. Circuito 4: Botoeira Industrial do Operador (Interface de Controle)
1. Conecte um dos terminais do push-button ao **GPIO 6** do ESP32-S3.
2. Conecte o terminal diagonalmente oposto ao barramento de **GND**.
3. *Dispensa resistor externo:* O firmware habilita o resistor de *pull-up* interno no chip (`pull_up_en = GPIO_PULLUP_ENABLE`). Quando a chave está aberta, o pino lê `1` (HIGH); quando pressionada, o pino é aterrado e lê `0` (LOW).

### 4.5. Circuito 5: Enlace Serial Cabeado UART (ESP32 $\longleftrightarrow$ Raspberry Pi 5)
1. Conecte o **GPIO 17 (TX)** do ESP32-S3 ao pino **GPIO 15 (RX / Pino 10)** da Raspberry Pi 5.
2. Conecte o **GPIO 18 (RX)** do ESP32-S3 ao pino **GPIO 14 (TX / Pino 8)** da Raspberry Pi 5.
3. **Malha de Terra (Obrigatória):** Conecte um jumper entre um pino **GND** do ESP32 e o **GND (Pino 6)** da Raspberry Pi. Sem essa linha comum, os sinais TTL flutuam e geram corrupção severa de caracteres na UART.

---

## 5. Lógica de Firmware e Temporização (FreeRTOS)

O código C implementado em `motor/main/main.c` é dividido em três tarefas assíncronas do FreeRTOS:

### 5.1. Tabela de Tarefas e Prioridades do FreeRTOS
| Nome da Task | Prioridade | Stack Size | Período de Execução | Responsabilidade |
| :--- | :---: | :---: | :---: | :--- |
| **`botoeira_task`** | 10 (Alta) | 4096 bytes | Loop contínuo a cada 10 ms | Lê o GPIO 6, aplica filtro de debounce (50 ms), detecta clique e comuta estado. |
| **`uart_rx_task`** | 8 (Média) | 4096 bytes | Bloqueante com timeout de 100 ms | Escuta comandos vindos da Raspberry Pi (`STOP`, `START`, `DEFECT`, `ALERTA`). |
| **`alerta_task`** | 5 (Baixa) | 2048 bytes | 500 ms ON / 500 ms OFF | Quando `em_alerta == true`, gera o padrão acústico contínuo ("UIU UIU"). |

### 5.2. Padrões de Sinalização e Feedback Acústico/Visual
| Evento Operacional | Comando / Gatilho | Padrão no LED e Buzzer | Duração / Comportamento |
| :--- | :--- | :--- | :--- |
| **Sistema Ligado** | Clique na Botoeira (`sys_on = true`) | **1 pulso curto** | 500 ms ligado $\rightarrow$ Desliga. |
| **Sistema Desligado** | Clique na Botoeira (`sys_on = false`) | **2 pulsos curtos** | 500 ms ON / 500 ms OFF / 500 ms ON $\rightarrow$ Desliga. |
| **Parada de Inspeção** | UART: `"STOP\n"` | **Silencioso** | Motor desliga sem emitir beeps (não atrasa o ciclo). |
| **Retomada de Esteira** | UART: `"START\n"` | **Silencioso** | Motor liga sem emitir beeps. |
| **Defeito Isolado (MISCUT)** | UART: `"DEFECT\n"` | **1 pulso longo** | 1000 ms contínuo no LED e Buzzer (sinaliza refugo). |
| **Modo ALERTA (Controle de Danos)** | UART: `"ALERTA\n"` | **Sequência oscilante** | Pulsos de 500 ms ON / 500 ms OFF repetidos indefinidamente até que o operador pressione a botoeira. |

---

## 6. Vocabulário do Protocolo UART (115200 bps, 8N1)

A tabela a seguir padroniza todas as mensagens ASCII terminadas em newline (`\n`) trocadas no barramento serial:

```
          FLUXO DE COMUNICAÇÃO SERIAL (ESP32 <──> RASPBERRY PI 5)

     [ ESP32-S3 ]                                      [ Raspberry Pi 5 ]
          │                                                    │
          │─────── "SYS_ON\n" (Operador ligou) ───────────────>│ Inicia Lote no BD
          │                                                    │
          │<────── "STOP\n" (Carta detectada na ROI) ──────────│ Para a esteira
          │                                                    │ Executa YOLOv8
          │<────── "DEFECT\n" (Carta reprovada) ───────────────│ Aciona 1s de beep
          │                                                    │
          │<────── "START\n" (Inspeção concluída) ─────────────│ Religa esteira
          │                                                    │
          │<────── "ALERTA\n" (3 falhas consecutivas) ─────────│ Trava esteira e
          │                                                    │ ativa sirene oscilante
          │                                                    │
          │─────── "SYS_OFF\n" (Operador interveio no botão) ──>│ Encerra Lote no BD
```

| Mensagem | Direção | Ação Disparada no Destinatário |
| :--- | :---: | :--- |
| **`SYS_ON\n`** | ESP32 $\rightarrow$ Pi | A Pi ativa a captura contínua e invoca `iniciar_lote(db)` no SQLite (novo ID). |
| **`SYS_OFF\n`** | ESP32 $\rightarrow$ Pi | A Pi pausa a captura e invoca `encerrar_lote(db)` no SQLite (grava timestamp final). |
| **`STOP\n`** | Pi $\rightarrow$ ESP32 | O ESP32 coloca o GPIO 7 em LOW, paralisando a esteira para captura estável sem borrão. |
| **`START\n`** | Pi $\rightarrow$ ESP32 | O ESP32 recoloca o GPIO 7 em HIGH, retomando a esteira (se não estiver em alerta). |
| **`DEFECT\n`** | Pi $\rightarrow$ ESP32 | O ESP32 aciona o LED e o Buzzer por 1000 ms para acusar a peça não conforme. |
| **`ALERTA\n`** | Pi $\rightarrow$ ESP32 | O ESP32 desliga o motor e ativa a `alerta_task` contínua oscilante. |

---

## 7. Guia de Compilação e Gravação do Firmware

### 7.1. Pré-requisitos
* **ESP-IDF v5.5** configurado nas variáveis de ambiente do sistema;
* Cabo USB conectado à porta de programação/UART do ESP32-S3.

### 7.2. Passo a Passo no Terminal
```bash
# 1. Navegar até o diretório do firmware
cd motor

# 2. Configurar o chip-alvo (apenas na primeira compilação)
idf.py set-target esp32s3

# 3. Compilar o projeto
idf.py build

# 4. Gravar o binário na placa e abrir o monitor serial
# No Linux: /dev/ttyUSB0 ou /dev/ttyACM0
# No Windows: COM3, COM4, etc.
idf.py -p /dev/ttyUSB0 flash monitor
```

*Para sair do monitor serial do ESP-IDF, pressione `Ctrl + ]`.*

---

## 8. Boas Práticas, Cuidados e Diagnóstico de Falhas (Troubleshooting)

1. **Alimentação Separada:** **Nunca alimente o motor C diretamente pelos pinos de 3.3V ou 5V do ESP32**. O consumo de corrente e os picos de partida causam queda de tensão (*brownout reset*) no microcontrolador. Use uma fonte externa dedicada e ligue todos os terras (GND) juntos.
2. **Debounce do Botão:** O firmware implementa um debounce digital por software de 50 ms (`DEBOUNCE_MS`). Caso utilize uma chave mecânica com muito desgaste de contato (*contact bounce*), o valor pode ser ajustado para até 80 ms em `main.c`.
3. **Verificação da Tensão dos Níveis Lógicos:** O ESP32-S3 e a Raspberry Pi 5 trabalham nativamente com níveis lógicos **3.3V TTL**. Portanto, a ligação serial direta entre GPIO 17/18 e GPIO 14/15 é 100% segura e não necessita de divisor de tensão resistivo ou conversor de nível lógico bidirecional.
