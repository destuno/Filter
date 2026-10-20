from PIL import Image, ImageDraw, ImageFont

def create_banner():
    # Устанавливаем точное разрешение 640x360
    size = (640, 360)
    image = Image.new("RGB", size, color=(15, 15, 25))
    draw = ImageDraw.Draw(image)
    
    # Центр холста для горизонтального формата
    cx, cy = 320, 150
    
    # Рисуем неоновые окружности под размер 640x360
    draw.ellipse([cx - 120, cy - 120, cx + 120, cy + 120], outline=(0, 255, 150), width=5)
    draw.ellipse([cx - 90, cy - 90, cx + 90, cy + 90], outline=(120, 80, 255), width=3)
    
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 55)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except IOError:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Текст FX в центре окружности
    text = "FX"
    bbox = draw.textbbox((0, 0), text, font=font_large)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = cx - text_width / 2
    y = cy - text_height / 2
    
    # Неоновая тень и основной текст
    draw.text((x + 2, y + 2), text, fill=(0, 150, 100), font=font_large)
    draw.text((x, y), text, fill=(255, 255, 255), font=font_large)
    
    # Подпись снизу
    subtext = "MEDIA FILTER"
    bbox_sub = draw.textbbox((0, 0), subtext, font=font_small)
    sub_width = bbox_sub[2] - bbox_sub[0]
    draw.text((cx - sub_width / 2, cy + 80), subtext, fill=(150, 150, 200), font=font_small)

    output_path = "bot_banner.png"
    image.save(output_path, quality=95)
    print(f"✅ Баннер 640x360 успешно создан: {output_path}")

if __name__ == "__main__":
    create_banner()