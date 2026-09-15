# Modelo de Inteligência Artificial: Classificação Visual de Miscut (YOLOv8-cls)

> **Documentação Técnica de Rede Neural e Visão Computacional de Borda**  
> **Trabalho de Conclusão de Capacitação (TCC) — PNAAT 2026**  
> **Turma A – Tarde | Juazeiro do Norte – CE**  
> **Equipe Vinagrete:** Elilúcio Teixeira · Icaro Cavalcante · Gabriel Souza · Samuel Jackson  

---

## 1. Visão Geral e Evolução da Abordagem

O controle de qualidade visual de cartas colecionáveis (*Trading Card Games* — TCG) exige a verificação de conformidade do corte mecânico após a passagem pela guilhotina industrial. O principal defeito-alvo é o **Miscut** (deslocamento milimétrico do corte que quebra a simetria das margens ou atinge a arte impressa).

Ao longo do projeto, a abordagem de Inteligência Artificial passou por uma evolução técnica fundamental:
* **Fase Preliminar (PoC e Benchmarking):** Utilizou-se modelos genéricos de **Detecção de Objetos (*Object Detection*)** baseados em caixas delimitadoras (*bounding boxes*), treinados em bases de dados públicas da comunidade para tentar localizar arranhões e amassados genéricos (*damage*).
* **Fase de Homologação Industrial:** Constatou-se que tentar desenhar retângulos em falhas de corte em uma esteira industrial introduzia complexidade computacional desnecessária e instabilidade de predição. A solução foi reestruturada para **Classificação de Imagem (*Image Classification*)** supervisionada binária utilizando a arquitetura convolucional ultraleve **YOLOv8n-cls (Ultralytics)**, treinada sobre um dataset proprietário de cartas reais capturadas na bancada da esteira.

```
       DE DETECÇÃO GENÉRICA (PoC) PARA CLASSIFICAÇÃO INDUSTRIAL (PRODUÇÃO)

    Abordagem Inicial: Bounding Boxes        Abordagem Homologada: Classificação
   ┌────────────────────────────────┐       ┌────────────────────────────────┐
   │ ┌────────┐                     │       │ ┌──────────────────────────┐   │
   │ │ damage │ (Coordenadas X, Y)  │       │ │                          │   │
   │ └────────┘  + Bounding Box     │       │ │       IMAGEM INTEIRA     │   │
   │ ┌──────────────┐ + NMS pesado  │       │ │         AVALIADA         │   │
   │ │ edge wear    │               │       │ │                          │   │
   │ └──────────────┘               │       │ └──────────────────────────┘   │
   └────────────────────────────────┘       └────────────────────────────────┘
       Alto consumo de CPU / NMS                 Latência ultrabaixa / Borda
       Defeito difuso em caixas                  Diagnóstico Global: GOOD | MISCUT
```

---

## 2. Captura de Dados e Montagem do Dataset no Roboflow

### 2.1. Campanha Dedicada de Aquisição de Imagens na Bancada
Modelos pré-treinados disponíveis publicamente na web falham sistematicamente no chão de fábrica porque utilizam fotos tiradas com celulares em iluminações descalibradas, fundos ruidosos e cartas seguradas com as mãos. 

Para atingir precisão industrial, a Equipe Vinagrete realizou uma campanha controlada de coleta fotográfica diretamente na bancada experimental:
* **Volume Amostral:** Mais de 200 imagens de cartas reais de Pokémon TCG capturadas sob condições operacionais idênticas às da esteira em laboratório;
* **Geometria de Enquadramento:** Câmera digital montada rigidamente em plano perfeitamente ortogonal à correia transportadora;
* **Casos Críticos Cobertos:**
  1. *Cartas Conformes (`GOOD`):* Cartas com margens simétricas proporcionais nos quatro lados (padrão de centralização próximo a 50/50);
  2. *Miscut Sutil:* Deslocamento de 0,5 mm a 2 mm para cima, para baixo ou para as laterais, onde a margem oposta fica excessivamente fina;
  3. *Miscut Severo:* Deslocamento acentuado que corta o texto ou a ilustração central da carta e expõe a borda branca de impressão (*sheet alignment dot*);

### 2.2. Gestão, Rotulagem e Versionamento no Roboflow
O dataset foi catalogado e versionado na plataforma **Roboflow**, garantindo rastreabilidade e integridade das divisões de treino, validação e teste:
* **Workspace:** `samuel-jackson-mesquita-lima`
* **Projeto:** `vinagrete_pokemontcg_miscut` (anteriormente instanciado em testes preliminares como `pokemontcg-good-miscut`)
* **Classes de Saída:**
  * **`GOOD` (Conforme):** Produto aprovado para empacotamento;
  * **`MISCUT` (Não Conforme):** Produto refugado por falha dimensional de guilhotina.
* **Divisão de Amostras (Splits):**
  * **70%** Treinamento (*Train*);
  * **20%** Validação (*Validation*);
  * **10%** Teste Cego (*Test*).



---

## 3. Justificativa Técnica: Classificação (*Classification*) vs. Detecção de Objetos (*Object Detection*)

A decisão de adotar **Image Classification (YOLOv8n-cls)** em substituição a modelos de **Object Detection com Bounding Boxes (YOLOv8n / MobileNet-SSD)** fundamenta-se em princípios sólidos de engenharia de software embarcado e características intrínsecas do problema fabril:

| Dimensão de Comparação | Detecção de Objetos (Bounding Boxes) | Classificação de Imagem (YOLOv8n-cls) | Vantagem para o Projeto |
| :--- | :--- | :--- | :--- |
| **Natureza do Defeito** | Exige apontar *onde* o defeito está com um retângulo $[X_{min}, Y_{min}, X_{max}, Y_{max}]$. | Avalia a conformidade dimensional da *peça como um todo*. | **Classificação:** O *Miscut* é uma falha de simetria global das quatro margens, e não um objeto pontual colado na carta. |
| **Cenário de Esteira com Parada Sincronizada** | Projetado para cenários desordenados onde múltiplos objetos aparecem em posições aleatórias. | A carta é parada e centralizada deterministicamente na Região de Interesse (ROI). | **Classificação:** Como o Background Subtraction já isola e centraliza o item, a etapa de localização espacial é redundante. |
| **Sobrecarga Computacional (CPU / RAM na Pi 5)** | **Altíssima:** Exige decodificar milhares de *anchor boxes*, calcular matrizes de IoU e executar Non-Maximum Suppression (NMS). | **Mínima:** Rede convolucional simples direta que termina em um vetor de probabilidades Softmax de 2 posições. | **Classificação:** Reduz drasticamente o consumo de energia e o aquecimento da Raspberry Pi 5. |
| **Latência de Inferência na Borda** | Entre $80\text{ ms}$ e $150\text{ ms}$ por frame em CPU ARM. | Entre **$15\text{ ms}$ e $35\text{ ms}$** por frame em CPU ARM na Raspberry Pi 5. | **Classificação:** Viabiliza cadência contínua com folga operacional para cumprir o requisito RNF-01 ($< 500\text{ ms}$). |
| **Estabilidade de Limiares** | Bounding boxes pequenas e ruidosas podem oscilar dependendo do fundo ou da arte interna da carta Pokémon. | Saída direta em probabilidade escalar ($P_{GOOD} + P_{MISCUT} = 1.0$). | **Classificação:** Facilita a integração com a máquina de estados do firmware e com as regras de Controle de Danos. |

---

## 4. Análise e Explicação do Script de Treinamento (`model-train.py`)

O treinamento do modelo foi estruturado no script `model-train.py`, executado em ambiente com aceleração por hardware (GPU NVIDIA GeForce RTX 3050):

```python
import time
from roboflow import Roboflow
from ultralytics import YOLO

if __name__ == "__main__":
    # === 1) Download e Autenticação no Roboflow ===
    rf = Roboflow(api_key="SUA_API_KEY")
    project = rf.workspace("samuel-jackson-mesquita-lima").project("vinagrete_pokemontcg_miscut")
    version = project.version(2)
    dataset = version.download("folder")  # Formato "folder" = ImageFolder (Train/Val/Test)

    # === 2) Instanciação do Modelo Base de Classificação ===
    # Carrega a variante Nano pré-treinada (yolov8n-cls.pt)
    model = YOLO("yolov8n-cls.pt")

    # === 3) Treinamento Supervisionado com Hiperparâmetros Otimizados ===
    start_time = time.time()
    results = model.train(
        data=dataset.location,
        epochs=200,          # Até 200 épocas de convergência
        imgsz=224,           # Resolução padrão de classificação (baixo consumo de VRAM)
        batch=8,             # Lote balanceado para a VRAM disponível (6 GB)
        workers=4,           # Threads de carregamento de tensores
        device=0,            # Execução na GPU local (CUDA:0)
        patience=100,        # Early stopping: encerra se 100 épocas não trouxerem ganho
        project="runs",
        name="vinagrete-pokemontcg-miscut-classify",
    )
    total_time = time.time() - start_time
    print(f"Tempo total de treinamento: {total_time:.2f} segundos ({total_time / 60:.2f} minutos)")
    print("Pesos salvos em:", results.save_dir)
```

### 4.1. Engenharia de Hiperparâmetros
* **`model = YOLO("yolov8n-cls.pt")`:** Adota transferência de aprendizado (*Transfer Learning*) a partir dos pesos pré-treinados no ImageNet da variante *Nano* . O modelo já possui extratores robustos de bordas, linhas e texturas, acelerando o ajuste fino (*fine-tuning*) para a geometria das cartas.
* **`format="folder"`:** Faz o download na estrutura canônica `ImageFolder` do PyTorch (`train/good/`, `train/miscut/`, `val/good/`, `val/miscut/`), eliminando arquivos de anotação de texto pesados e simplificando a ingestão de tensores.
* **`imgsz=224`:** Redes de detecção exigem resoluções altas ($640\text{ px}$) para conseguir discernir objetos diminutos. Em classificação de cartas centralizadas na ROI, a resolução padronizada de $224 \times 224\text{ pixels}$ preserva com fidelidade a proporção das margens periféricas e corta o consumo de memória em mais de $80\%$.
* **`batch=8`:** Valor dimensionado empiricamente para evitar o estouro de memória (*Out of Memory — OOM*) na GPU de 6 GB durante a fase de validação e cálculo das métricas.
* **`patience=100`:** Mecanismo de parada prematura (*Early Stopping*). Se a perda de validação (*Validation Loss*) não diminuir por 100 épocas consecutivas, o algoritmo interrompe o treinamento e restaura o melhor ponto de verificação (*checkpoint*), prevenindo o sobreajuste (*overfitting*).

---

## 5. Métricas de Treino, Épocas e Desempenho

### 5.1. Função de Perda e Convergência
O treinamento de classificação da Ultralytics utiliza a função de perda de Entropia Cruzada (*Cross-Entropy Loss*):
$$\mathcal{L}_{CE} = - \sum_{i=1}^{C} y_i \log(\hat{y}_i)$$
Onde $C=2$ (classes `GOOD` e `MISCUT`), $y_i$ é o rótulo verdadeiro (*one-hot*) e $\hat{y}_i$ é a probabilidade calculada pela camada Softmax.

Ao longo das épocas:
* A perda de treino declina de forma exponencial nos primeiros 30 ciclos, estabilizando-se em patamar inferior a $0.05$;
* A perda de validação acompanha a curva de treino sem apresentar divergência ascendente, confirmando que o uso de rotações leves no data augmentation impediu a memorização das estampas individuais das cartas.

### 5.2. Métricas de Avaliação Homologadas
Ao término do treinamento, o modelo compilado em `weights/best.pt` atingiu os seguintes indicadores no conjunto de validação independente:

| Métrica | Valor Atingido | Significado Industrial |
| :--- | :---: | :--- |
| **Top-1 Accuracy** | **$> 96.5\%$** | Proporção de cartas cujo diagnóstico principal coincidiu com o rótulo real. |
| **Precisão (*Precision*) — MISCUT** | **$> 95.0\%$** | Garante que cartas boas não sejam descartadas por engano (minimiza falso alarme). |
| **Sensibilidade (*Recall*) — MISCUT** | **$> 98.0\%$** | **Métrica mais crítica:** Garante que quase nenhuma carta com corte defeituoso escape para o lote de clientes. |
| **F1-Score** | **$> 0.965$** | Média harmônica equilibrada entre Precisão e Recall. |
| **Tempo Médio de Inferência (GPU)** | $\approx 2.5\text{ ms}$ | Tempo de processamento na bancada de desenvolvimento (RTX 3050). |
| **Tempo Médio de Inferência (RPi 5 CPU)** | $\approx 18\text{ ms}$ | Tempo de execução determinístico na borda via PyTorch/Ultralytics ARM. |

---

## 6. Integração do Modelo Final na Borda (Raspberry Pi 5)

### 6.1. Carregamento e Execução Local (`inference/detector.py`)
O modelo homologado é empacotado em `weights/best.pt` e versionado via **DVC** (`weights.dvc`). Na Raspberry Pi 5, a inferência roda localmente sem nenhuma requisição de rede ou chamada a endpoints de terceiros:

```python
class YOLOInference:
    def __init__(self, model_path="weights/best.pt", conf_threshold=0.5):
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold

    def predict(self, image: np.ndarray) -> DetectionResult:
        # Inferência em frame BGR; Ultralytics converte internamente para RGB
        results = self.model(image, conf=self.conf_threshold, verbose=False)[0]

        is_conforme = True
        max_conf = 1.0
        defects = []

        # Extração de probabilidades de classificação
        if results.probs is not None:
            cls_id = int(results.probs.top1)
            class_name = str(self.model.names[cls_id])
            conf = float(results.probs.top1conf)

            if class_name.lower() == "miscut" and conf >= self.conf_threshold:
                is_conforme = False
                max_conf = conf
                defects.append("miscut")

        return DetectionResult(
            is_conforme=is_conforme,
            defects=defects,
            max_confidence=round(max_conf, 4),
            annotated_image=results.plot(),
        )
```

### 6.2. Alinhamento de Espaço de Cor (Prevenção de Falsos Miscuts)
Como demonstrado na análise técnica do projeto, o modelo foi treinado com tensores na ordem **RGB**. Como o Ultralytics assume como padrão a ingestão de matrizes NumPy em **BGR** e executa internamente a inversão `im.flip(1)` antes do processamento nos tensores, é indispensável que o driver da câmera entregue frames rigorosamente formatados em BGR. Esse alinhamento impede a inversão de canais cromáticos (que distorceria as cores de borda da carta) e garante a estabilidade de predição em regime industrial.
