import time
from roboflow import Roboflow
from ultralytics import YOLO

if __name__ == "__main__":
    # === 1) Baixar dataset do Roboflow ===
    # 👇 COLOQUE SUA NOVA API KEY AQUI (a antiga "V4gOORWIzylNWCqiu1RA" pode ter expirado/rotacionado)
    rf = Roboflow(api_key="SUA_API_KEY_AQUIS")

    project = rf.workspace("samuel-jackson-mesquita-lima").project("vinagrete_pokemontcg_miscut")
    version = project.version(2)  # v4: novo treino sobre o mesmo dataset (mesmas imagens, versão reprocessada)
    dataset = version.download("folder")  # formato "folder" = estrutura de classificação (ImageFolder)

    # === 2) Treinamento (classificação: good vs miscut) ===
    # Usamos yolov8n-cls.pt (variante de CLASSIFICAÇÃO), não yolov8n.pt,
    # pois o defeito-alvo (corte errado) é uma propriedade geométrica da carta inteira,
    # não uma região localizada -> classificação, não detecção.
    model = YOLO("yolov8n-cls.pt")  # nano-cls: mesma justificativa da Aula 6 para edge (Raspberry Pi 5)

    start_time = time.time()
    results = model.train(
        data=dataset.location,   # caminho já vem pronto do download, sem precisar hardcodar
        epochs=200,
        imgsz=224,      # classificação não precisa de 640px; reduz MUITO o uso de VRAM
        batch=8,        # 16 estourou a VRAM de 6GB na validação do epoch 5; se ainda faltar memória, tente batch=4
        workers=4,      # menos threads de dataloader = menos memória pinned
        device=0,
        patience=100,
        project="runs",
        name="vinagrete-pokemontcg-miscut-classify",
    )
    total_time = time.time() - start_time
    print(f"Tempo total de treinamento: {total_time:.2f} segundos ({total_time / 60:.2f} minutos)")
    print("Pesos salvos em:", results.save_dir)