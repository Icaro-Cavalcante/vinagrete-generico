#include <stdio.h>
#include <stdbool.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "driver/uart.h"
#include "esp_log.h"

static const char *TAG = "ESTEIRA";

/* ---------- Definições de pinos (conforme pinout da placa) ---------- */
#define GPIO_MOTOR      GPIO_NUM_7   // Saída para base do TIP122 (via resistor 1k)
#define GPIO_BOTOEIRA   GPIO_NUM_6   // Entrada da botoeira (pull-up interno, ativo em LOW)
#define GPIO_LED        GPIO_NUM_2   // LED vermelho de sinalização
#define GPIO_BUZZER     GPIO_NUM_1   // Buzzer de sinalização

/* ---------- Parâmetros de debounce ---------- */
#define DEBOUNCE_MS     50           // Tempo mínimo de estabilidade do sinal
#define POLL_DELAY_MS   10           // Intervalo de leitura do pino

/* ---------- Parâmetros de sinalização (LED + Buzzer) ---------- */
#define PULSO_MS        500          // Duração de cada pulso de LED/buzzer (500 ms)
#define PAUSA_MS        500          // Pausa entre pulsos (500 ms)

/* ---------- Configurações UART ---------- */
#define UART_PORT       UART_NUM_0
#define UART_TX_PIN     GPIO_NUM_17  // Conectar ao RX da Raspberry Pi 5
#define UART_RX_PIN     GPIO_NUM_18  // Conectar ao TX da Raspberry Pi 5
#define UART_BAUD_RATE  115200
#define BUF_SIZE        1024

/* Estado global do sistema, motor e alerta */
static bool sys_on = false;
static bool motor_ligado = false;
static volatile bool em_alerta = false; // Indica se o alerta contínuo está ativo

/*
 * Emite N pulsos simultâneos de LED + buzzer, com pausa entre eles.
 * 1 pulso  -> Esteira ligada (500 ms ON)
 * 2 pulsos -> Esteira desligada (500 ms ON / 500 ms OFF / 500 ms ON)
 */
static void sinalizar(int num_pulsos)
{
    for (int i = 0; i < num_pulsos; i++) {
        gpio_set_level(GPIO_LED, 1);
        gpio_set_level(GPIO_BUZZER, 1);
        vTaskDelay(pdMS_TO_TICKS(PULSO_MS));

        gpio_set_level(GPIO_LED, 0);
        gpio_set_level(GPIO_BUZZER, 0);

        if (i < num_pulsos - 1) {
            vTaskDelay(pdMS_TO_TICKS(PAUSA_MS));
        }
    }
}

/*
 * Emite 1 pulso com duração configurável em ms (usado no DEFECT: 1000 ms)
 */
static void sinalizar_pulso_ms(int duracao_ms)
{
    gpio_set_level(GPIO_LED, 1);
    gpio_set_level(GPIO_BUZZER, 1);
    vTaskDelay(pdMS_TO_TICKS(duracao_ms));
    gpio_set_level(GPIO_LED, 0);
    gpio_set_level(GPIO_BUZZER, 0);
}

/*
 * Task de sinalização contínua de alerta.
 * Mantém a sequência oscilante (500 ms ON / 500 ms OFF) até intervenção do operador.
 */
static void alerta_task(void *arg)
{
    while (1) {
        if (em_alerta) {
            gpio_set_level(GPIO_LED, 1);
            gpio_set_level(GPIO_BUZZER, 1);
            vTaskDelay(pdMS_TO_TICKS(PULSO_MS));

            gpio_set_level(GPIO_LED, 0);
            gpio_set_level(GPIO_BUZZER, 0);
            vTaskDelay(pdMS_TO_TICKS(PAUSA_MS));
        } else {
            vTaskDelay(pdMS_TO_TICKS(100));
        }
    }
}

static void motor_set(bool ligar)
{
    motor_ligado = ligar;
    gpio_set_level(GPIO_MOTOR, motor_ligado ? 1 : 0);
    ESP_LOGI(TAG, "Motor %s", motor_ligado ? "LIGADO" : "DESLIGADO");
}

static void system_shutdown(void)
{
    em_alerta = false;
    sys_on = false;
    motor_set(false);
    ESP_LOGI(TAG, "Sistema DESLIGADO (SYS_OFF)");
    const char *msg = "SYS_OFF\n";
    uart_write_bytes(UART_PORT, msg, strlen(msg));
    sinalizar(2); // 2 pulsos de 500 ms
}

static void system_toggle(void)
{
    // Se estiver em alerta, o botão força o desligamento completo imediato
    if (em_alerta) {
        system_shutdown();
        return;
    }

    sys_on = !sys_on;
    if (sys_on) {
        ESP_LOGI(TAG, "Sistema LIGADO (SYS_ON)");
        const char *msg = "SYS_ON\n";
        uart_write_bytes(UART_PORT, msg, strlen(msg));
        motor_set(true);
        sinalizar(1); // 1 pulso de 500 ms
    } else {
        system_shutdown();
    }
}

static void uart_init(void)
{
    uart_config_t uart_config = {
        .baud_rate  = UART_BAUD_RATE,
        .data_bits  = UART_DATA_8_BITS,
        .parity     = UART_PARITY_DISABLE,
        .stop_bits  = UART_STOP_BITS_1,
        .flow_ctrl  = UART_HW_FLOWCTRL_DISABLE,
        .source_clk = UART_SCLK_DEFAULT,
    };
    uart_driver_install(UART_PORT, BUF_SIZE * 2, 0, 0, NULL, 0);
    uart_param_config(UART_PORT, &uart_config);
    uart_set_pin(UART_PORT, UART_TX_PIN, UART_RX_PIN, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE);
}

static void gpio_config_init(void)
{
    // Configura pinos de saída: motor, LED e buzzer
    // Configura pinos de saída: motor, LED e buzzer
    gpio_config_t saida_cfg = {
        .pin_bit_mask = (1ULL << GPIO_MOTOR) | (1ULL << GPIO_LED) | (1ULL << GPIO_BUZZER),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    gpio_config(&saida_cfg);

    // Configura pino da botoeira como entrada com pull-up interno (ativo em LOW)
    // Configura pino da botoeira como entrada com pull-up interno (ativo em LOW)
    gpio_config_t entrada_cfg = {
        .pin_bit_mask = (1ULL << GPIO_BOTOEIRA),
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_ENABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    gpio_config(&entrada_cfg);

    // Garante tudo desligado na inicialização
    // Garante tudo desligado na inicialização
    gpio_set_level(GPIO_LED, 0);
    gpio_set_level(GPIO_BUZZER, 0);
    motor_set(false);
}

/*
 * Task responsável por ler a botoeira com debounce e alternar (toggle)
 * o estado do motor a cada aperto válido, disparando a sinalização
 * de LED + buzzer correspondente.
 */
static void botoeira_task(void *arg)
{
    int nivel_estavel = 1;      // 1 = solto (pull-up), 0 = pressionado
    int nivel_anterior = 1;
    uint32_t contador_estavel_ms = 0;
    bool aguardando_liberar = false; // evita repetir o toggle enquanto o botão segue pressionado

    while (1) {
        int nivel_atual = gpio_get_level(GPIO_BOTOEIRA);

        if (nivel_atual == nivel_anterior) {
            contador_estavel_ms += POLL_DELAY_MS;
        } else {
            contador_estavel_ms = 0;
            nivel_anterior = nivel_atual;
        }

        // Sinal estável por tempo suficiente -> atualiza estado "debounced"
        if (contador_estavel_ms >= DEBOUNCE_MS && nivel_atual != nivel_estavel) {
            nivel_estavel = nivel_atual;

            if (nivel_estavel == 0 && !aguardando_liberar) {
                system_toggle();
                aguardando_liberar = true;
            } else if (nivel_estavel == 1) {
                // Botão solto: libera para o próximo aperto
                aguardando_liberar = false;
            }
        }

        vTaskDelay(pdMS_TO_TICKS(POLL_DELAY_MS));
    }
}

/* Escuta comandos vindos da Raspberry Pi 5 */
static void uart_rx_task(void *arg)
{
    static uint8_t data[BUF_SIZE];
    while (1) {
        int len = uart_read_bytes(UART_PORT, data, BUF_SIZE - 1, pdMS_TO_TICKS(100));
        if (len > 0) {
            data[len] = '\0';
            ESP_LOGI(TAG, "UART Recebido: %s", (char*)data);
            
            if (strstr((char*)data, "STOP") != NULL) {
                ESP_LOGI(TAG, "Comando STOP recebido");
                motor_set(false);
            }
            if (strstr((char*)data, "START") != NULL) {
                ESP_LOGI(TAG, "Comando START recebido");
                if (!em_alerta) {
                    motor_set(true);
                }
            }
            if (strstr((char*)data, "DEFECT") != NULL) {
                ESP_LOGI(TAG, "Comando DEFECT recebido");
                // Sinaliza defeito isolado: 1 pulso de 1000 ms sem travar a esteira em alerta contínuo
                sinalizar_pulso_ms(1000);
            }
            if (strstr((char*)data, "ALERTA") != NULL) {
                ESP_LOGI(TAG, "Comando ALERTA recebido (Controle de Danos)");
                motor_set(false);
                em_alerta = true; // Ativa o modo de alerta contínuo oscilante
            }
        }
    }
}

void app_main(void)
{
    ESP_LOGI(TAG, "Iniciando controle da esteira...");


    gpio_config_init();
    uart_init();

    xTaskCreate(botoeira_task, "botoeira_task", 4096, NULL, 10, NULL);
    xTaskCreate(uart_rx_task,  "uart_rx_task",  4096, NULL, 8,  NULL);
    xTaskCreate(alerta_task,   "alerta_task",   2048, NULL, 5,  NULL);
}