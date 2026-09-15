import cv2
import os
import sys

# Ensure we can import from config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import ROI_DIMENSIONS

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    image_path = os.path.join(base_dir, "images", "img.jpeg")
    output_path = os.path.join(base_dir, "images", "roi_preview.jpg")

    if not os.path.exists(image_path):
        print(f"Erro: Imagem não encontrada em {image_path}")
        return

    # Lê a imagem
    img = cv2.imread(image_path)
    if img is None:
        print(f"Erro ao ler a imagem {image_path}")
        return

    h, w = img.shape[:2]
    print(f"Dimensões da imagem original: {w}x{h}")

    # Pega os limites (garantindo que não passem do tamanho da imagem)
    roi_w, roi_h = ROI_DIMENSIONS
    roi_w = min(roi_w, w)
    roi_h = min(roi_h, h)
    
    x_center, y_center = w // 2, h // 2
    x_start = x_center - roi_w // 2
    x_end = x_start + roi_w
    y_start = y_center - roi_h // 2
    y_end = y_start + roi_h

    print(f"ROI X: {x_start} até {x_end}")
    print(f"ROI Y: {y_start} até {y_end}")

    # Desenha um retângulo vermelho (BGR)
    cv2.rectangle(img, (x_start, y_start), (x_end, y_end), (0, 0, 255), 3)

    # Adiciona um texto indicando a ROI
    cv2.putText(img, "ROI - Area de Inspecao", (x_start, max(20, y_start - 10)), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    # Desenha a linha central (gatilho de parada)
    roi_center_y = y_start + (y_end - y_start) // 2
    cv2.line(img, (x_start, roi_center_y), (x_end, roi_center_y), (0, 255, 0), 2)
    cv2.putText(img, "Centro (Gatilho)", (x_start, roi_center_y - 10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    # Desenha a faixa central do gatilho (+- 35 pixels)
    cv2.line(img, (x_start, roi_center_y - 35), (x_end, roi_center_y - 35), (255, 255, 0), 1, lineType=cv2.LINE_AA)
    cv2.line(img, (x_start, roi_center_y + 35), (x_end, roi_center_y + 35), (255, 255, 0), 1, lineType=cv2.LINE_AA)

    # Salva a imagem
    cv2.imwrite(output_path, img)
    print(f"Imagem com ROI salva com sucesso em: {output_path}")

if __name__ == "__main__":
    main()
