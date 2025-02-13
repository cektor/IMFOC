#!/bin/bash

# Kaynak dosya adı
EXTENSION_FILE="imfoc-nemo.py"

# Hedef dizin
TARGET_DIR="$HOME/.local/share/nemo-python/extensions"

# Hedef dizini oluştur (varsa hata vermez)
mkdir -p "$TARGET_DIR"

# Dosyayı hedef dizine kopyala
if cp "$EXTENSION_FILE" "$TARGET_DIR/"; then
    echo "✅ Eklenti başarıyla kopyalandı: $TARGET_DIR/$EXTENSION_FILE"
    echo "✅ Nemoyu Açın MenuBardan Düzenleye Tıklayın. Eklentilere Tıklayın (Alt+P). IMFOC+NemoPython Adlı Eklenti Aktif değilse Aktif Edin "
else
    echo "❌ Kopyalama sırasında hata oluştu!"
    exit 1
fi

# Nemo'yu yeniden başlat
echo "🔄 Nemo yeniden başlatılıyor..."
nemo --quit
nohup nemo >/dev/null 2>&1 &

echo "✅ Kurulum tamamlandı! Nemo'yu açıp eklentiyi test edebilirsiniz."

