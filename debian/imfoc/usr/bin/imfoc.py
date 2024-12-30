import sys
import os
from PIL import Image
import numpy as np
import cv2
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, 
    QFileDialog, QLabel, QComboBox, QMessageBox, QCheckBox, QProgressBar, QHBoxLayout, QSpinBox, QGroupBox
)
from PyQt5.QtGui import QIcon, QPixmap, QFont
from PyQt5.QtCore import Qt, QEvent, QSettings
import io


def get_logo_path():
    """Logo dosyasının yolunu döndürür."""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "imfoclo.png")
    elif os.path.exists("/usr/share/icons/hicolor/48x48/apps/imfoclo.png"):
        return "/usr/share/icons/hicolor/48x48/apps/imfoclo.png"
    elif os.path.exists("imfoclo.png"):
        return "imfoclo.png"
    return None


def get_icon_path():
    """Simge dosyasının yolunu döndürür."""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "imfoclo.png")
    elif os.path.exists("/usr/share/icons/hicolor/48x48/apps/imfoclo.png"):
        return "/usr/share/icons/hicolor/48x48/apps/imfoclo.png"
    return None


LOGO_PATH = get_logo_path()
ICON_PATH = get_icon_path()


def install_rembg():
    """rembg kütüphanesini yükler"""
    try:
        import rembg
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "rembg"])


def remove_background(image):
    """OpenCV ile görüntünün arka planını kaldırır."""
    try:
        # PIL Image'i numpy dizisine dönüştür
        img_array = np.array(image)
        
        # BGR'ye dönüştür
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        # Görüntüyü işle
        mask = np.zeros(img_bgr.shape[:2], np.uint8)
        bgdModel = np.zeros((1,65), np.float64)
        fgdModel = np.zeros((1,65), np.float64)
        
        # Otomatik dikdörtgen
        rect = (10, 10, img_bgr.shape[1]-20, img_bgr.shape[0]-20)
        
        # GrabCut uygula
        cv2.grabCut(img_bgr, mask, rect, bgdModel, fgdModel, 5, cv2.GC_INIT_WITH_RECT)
        
        # Maskeyi oluştur
        mask2 = np.where((mask==2)|(mask==0), 0, 1).astype('uint8')
        
        # Maskeyi iyileştir
        kernel = np.ones((3,3), np.uint8)
        mask2 = cv2.morphologyEx(mask2, cv2.MORPH_OPEN, kernel, iterations=2)
        mask2 = cv2.morphologyEx(mask2, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask2 = cv2.GaussianBlur(mask2, (5,5), 0)
        
        # Alfa kanalı oluştur
        alpha = mask2 * 255
        
        # RGBA görüntüsü oluştur
        b, g, r = cv2.split(img_bgr)
        rgba = cv2.merge([r, g, b, alpha])
        
        # PIL Image'e dönüştür
        return Image.fromarray(rgba)
        
    except Exception as e:
        print(f"Arka plan kaldırma hatası: {e}")
        return image


class ImageConverter(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("ALGSoftware", "IMFOC")
        self.current_language = self.settings.value("language", "tr")
        self.initUI()

    def initUI(self):
        self.setWindowTitle('IMFOC')
        self.setWindowIcon(QIcon(ICON_PATH if ICON_PATH else 'imfoclo.png'))
        self.setStyleSheet("background-color: #2E2E2E; color: white;")
        self.setFixedSize(450, 650)

        layout = QVBoxLayout()

        # Dil seçici
        self.language_selector = QComboBox(self)
        self.language_selector.addItems(["Türkçe", "English"])
        self.language_selector.setCurrentText("Türkçe" if self.current_language == "tr" else "English")
        self.language_selector.currentTextChanged.connect(self.change_language)
        layout.addWidget(self.language_selector)

        if LOGO_PATH:
            self.logo_label = QLabel(self)
            pixmap = QPixmap(LOGO_PATH)
            scaled_pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(scaled_pixmap)
            self.logo_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.logo_label)

        self.info_label_format = QLabel(self)
        layout.addWidget(self.info_label_format)

        self.format_selector = QComboBox(self)
        self.format_selector.addItems(["PNG", "JPEG", "GIF", "BMP", "TIFF", "WEBP"])
        self.format_selector.setCurrentText("BMP")
        self.format_selector.currentTextChanged.connect(self.toggle_format_options)
        layout.addWidget(self.format_selector)

        self.info_label_quality = QLabel(self)
        layout.addWidget(self.info_label_quality)
        self.info_label_quality.setVisible(False)

        self.quality_selector = QComboBox(self)
        self.quality_selector.addItems([str(i) for i in range(10, 101, 10)])
        self.quality_selector.setVisible(False)
        layout.addWidget(self.quality_selector)

        self.remove_bg_checkbox = QCheckBox(self)
        self.remove_bg_checkbox.setStyleSheet("QCheckBox { color: white; }")
        self.remove_bg_checkbox.setEnabled(True)
        self.remove_bg_checkbox.setVisible(False)
        layout.addWidget(self.remove_bg_checkbox)

        # Boyutlandırma checkbox'ı
        self.resize_checkbox = QCheckBox(self)
        self.resize_checkbox.setStyleSheet("QCheckBox { color: white; }")
        self.resize_checkbox.stateChanged.connect(self.toggle_resize_options)
        layout.addWidget(self.resize_checkbox)

        # Boyutlandırma Grubu
        self.resize_group = QGroupBox(self)
        self.resize_group.setStyleSheet("""
            QGroupBox {
                color: white;
                border: 1px solid gray;
                border-radius: 5px;
                margin-top: 0.5em;
                padding: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
        """)
        resize_layout = QVBoxLayout()

        # Boyutlandırma tipi seçimi
        size_type_layout = QHBoxLayout()
        
        self.size_type_group = QComboBox(self)
        self.size_type_group.addItems(["Piksel", "Yüzde"])
        self.size_type_group.currentTextChanged.connect(self.change_size_type)
        size_type_layout.addWidget(self.size_type_group)
        
        resize_layout.addLayout(size_type_layout)

        # Hazır boyutlar combobox'ı
        self.preset_size_label = QLabel(self)
        resize_layout.addWidget(self.preset_size_label)
        
        self.preset_size_combo = QComboBox(self)
        self.preset_size_combo.addItems([
            "Özel",
            "1920x1080 (Full HD)",
            "1280x720 (HD)",
            "800x600",
            "640x480"
        ])
        self.preset_size_combo.currentTextChanged.connect(self.update_size_inputs)
        resize_layout.addWidget(self.preset_size_combo)

        # Genişlik ve yükseklik girişleri
        size_inputs_layout = QHBoxLayout()
        
        self.width_label = QLabel(self)
        size_inputs_layout.addWidget(self.width_label)
        
        self.width_input = QSpinBox(self)
        self.width_input.setRange(1, 10000)
        self.width_input.setValue(800)
        self.width_input.setStyleSheet("QSpinBox { color: black; }")
        size_inputs_layout.addWidget(self.width_input)
        
        self.height_label = QLabel(self)
        size_inputs_layout.addWidget(self.height_label)
        
        self.height_input = QSpinBox(self)
        self.height_input.setRange(1, 10000)
        self.height_input.setValue(600)
        self.height_input.setStyleSheet("QSpinBox { color: black; }")
        size_inputs_layout.addWidget(self.height_input)
        
        resize_layout.addLayout(size_inputs_layout)

        # En boy oranını koru checkbox'ı
        self.keep_aspect_ratio = QCheckBox(self)
        self.keep_aspect_ratio.setStyleSheet("QCheckBox { color: white; }")
        self.keep_aspect_ratio.setChecked(True)
        resize_layout.addWidget(self.keep_aspect_ratio)

        self.resize_group.setLayout(resize_layout)
        layout.addWidget(self.resize_group)
        self.resize_group.hide()  # Başlangıçta gizli

        self.status_label = QLabel('', self)
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 10px;
            }
        """)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        self.drag_label = QLabel(self)
        self.drag_label.setAlignment(Qt.AlignCenter)
        self.drag_label.setStyleSheet("background-color: #444; padding: 50px; border: 2px dashed #888; border-radius: 10px;")
        self.drag_label.setAcceptDrops(True)
        self.drag_label.setWordWrap(True)
        self.drag_label.installEventFilter(self)
        layout.addWidget(self.drag_label)

        self.button_about = QPushButton(self)
        self.button_about.setFont(QFont("Arial", 10))
        self.button_about.clicked.connect(self.show_about)
        self.button_about.setStyleSheet("""
            QPushButton {
                background-color: #353535;
                color: white;
                border: 1px solid gray;
                padding: 5px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #454545;
            }
        """)
        layout.addWidget(self.button_about)

        # Başlangıçta boyutlandırma seçeneklerini devre dışı bırak
        self.toggle_resize_options(False)

        self.setLayout(layout)
        self.update_language()

    def eventFilter(self, source, event):
        if event.type() == QEvent.MouseButtonPress:
            self.show_file_dialog()
        elif event.type() == QEvent.Drop:
            self.handle_drop_event(event)
        elif event.type() == QEvent.DragEnter:
            self.handle_drag_enter_event(event)
        return super().eventFilter(source, event)

    def show_file_dialog(self):
        input_file, _ = QFileDialog.getOpenFileName(self, self.tr("Görüntü Seç"), os.getenv('HOME'), self.tr("Görüntü Dosyaları (*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.webp *.svg *.heif *.psd *.pdf *.xps)"))

        if input_file:
            self.status_label.setText(self.tr('Dönüştürülüyor...'))
            self.convert_images(input_file)
            self.status_label.setText(self.tr('Dönüştürme tamamlandı!'))

    def handle_drag_enter_event(self, event):
        event.acceptProposedAction()

    def handle_drop_event(self, event):
        event.acceptProposedAction()
        urls = event.mimeData().urls()
        if urls:
            file_path = str(urls[0].toLocalFile())
            if self.is_supported_image(file_path):
                self.status_label.setText(self.tr('Dönüştürülüyor...'))
                self.convert_images(file_path)
                self.status_label.setText(self.tr('Dönüştürme tamamlandı!'))
            else:
                self.status_label.setText(self.tr('Desteklenmeyen dosya formatı.'))

    def convert_images(self, input_file):
        output_format = self.format_selector.currentText()
        quality = int(self.quality_selector.currentText()) if output_format == "JPEG" else 100
        image_name, image_ext = os.path.splitext(os.path.basename(input_file))
        output_dir = os.path.dirname(input_file)
        
        suffix = "_nobg" if self.remove_bg_checkbox.isChecked() else ""
        output_image_path = os.path.join(output_dir, f"{image_name}{suffix}.{output_format.lower()}")

        if self.is_supported_image(input_file):
            self.convert_image_format(input_file, output_image_path, output_format, quality)
        else:
            self.status_label.setText(self.tr('Desteklenmeyen dosya formatı.'))

    def convert_image_format(self, input_image, output_image, format, quality):
        try:
            image = Image.open(input_image)
            
            if self.remove_bg_checkbox.isChecked():
                try:
                    self.progress_bar.setValue(0)
                    self.progress_bar.show()
                    self.status_label.setText(self.status_messages['removing_bg'])
                    QApplication.processEvents()
                    
                    # Görüntüyü RGBA moduna dönüştür
                    if image.mode != 'RGBA':
                        image = image.convert('RGBA')
                    
                    # OpenCV ile arka planı kaldır
                    image = remove_background(image)
                    
                    self.progress_bar.setValue(70)
                    QApplication.processEvents()
                    
                except Exception as e:
                    self.status_label.setText(self.status_messages['bg_failed'])
                    print(f"Arka plan kaldırma hatası: {e}")
                    self.progress_bar.hide()
                    return
            
            # JPEG için RGB'ye dönüştür
            if format == 'JPEG':
                image = image.convert('RGB')
            
            # Boyutlandırma işlemi
            if self.resize_checkbox.isChecked():
                original_width, original_height = image.size
                
                if self.size_type_group.currentText() == "Yüzde":
                    # Yüzde olarak boyutlandırma
                    width_percent = self.width_input.value() / 100
                    height_percent = self.height_input.value() / 100
                    new_width = int(original_width * width_percent)
                    new_height = int(original_height * height_percent)
                else:
                    # Piksel olarak boyutlandırma
                    new_width = self.width_input.value()
                    new_height = self.height_input.value()

                if self.keep_aspect_ratio.isChecked():
                    # En boy oranını koru
                    ratio = min(new_width/original_width, new_height/original_height)
                    new_width = int(original_width * ratio)
                    new_height = int(original_height * ratio)

                # Image.Resampling.LANCZOS yerine Image.ANTIALIAS kullanılacak
                try:
                    # Yeni sürümlerde Resampling.LANCZOS kullanımını dene
                    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                except AttributeError:
                    # Eski sürümlerde ANTIALIAS kullanımına geri dön
                    image = image.resize((new_width, new_height), Image.ANTIALIAS)

            image.save(output_image, format=format, quality=quality)
            self.progress_bar.setValue(100)
            QApplication.processEvents()
            self.status_label.setText(self.status_messages['completed'])
            
            self.progress_bar.hide()
            
        except Exception as e:
            self.status_label.setText(self.status_messages['error'])
            print(self.tr(f"Hata oluştu: {e}"))
            self.progress_bar.hide()

    def toggle_format_options(self, format):
        """Format seçimine göre kalite ve arka plan kaldırma seçeneklerini göster/gizle."""
        # JPEG için kalite seçeneği
        if format == "JPEG":
            self.quality_selector.setVisible(True)
            self.info_label_quality.setVisible(True)
        else:
            self.quality_selector.setVisible(False)
            self.info_label_quality.setVisible(False)
        
        # PNG ve WebP için arka plan kaldırma seçeneği
        if format in ["PNG", "WEBP"]:
            self.remove_bg_checkbox.setVisible(True)
        else:
            self.remove_bg_checkbox.setVisible(False)
            self.remove_bg_checkbox.setChecked(False)  # Diğer formatlarda seçimi kaldır

    def is_supported_image(self, file_path):
        try:
            image = Image.open(file_path)
            image.verify()
            return True
        except (IOError, SyntaxError):
            return False

    def show_about(self):
        """Hakkında penceresini gösterir."""
        if self.current_language == "tr":
            about_text = (
                "IMFOC | IMage FOrmat Converter \n\n"
                "Bu uygulama, görüntü dosyalarını farklı formatlara dönüştürmenizi sağlayan açık kaynaklı bir araçtır.\n\n"
                "Özellikler:\n"
                "• Desteklenen formatlar: PNG, JPEG, GIF, BMP, TIFF, WEBP\n"
                "• Sürükle-bırak desteği\n"
                "• PNG ve WebP formatları için arka plan kaldırma (BETA)\n"
                "• JPEG formatı için kalite ayarı\n"
                "• Görüntü boyutlandırma (piksel veya yüzde)\n"
                "• Hazır boyut şablonları\n"
                "• En-boy oranı koruma\n"
                "• Türkçe ve İngilizce dil desteği\n\n"
                "Geliştirici: ALG Yazılım Inc.©\n"
                "www.algyazilim.com | info@algyazilim.com\n\n"
                "Fatih ÖNDER (CekToR) | fatih@algyazilim.com\n"
                "GitHub: https://github.com/cektor\n\n"
                "ALG Yazılım Pardus'a Göç'ü Destekler.\n\n"
                "Sürüm: 1.0.2"
            )
            title = "IMFOC Hakkında"
        else:
            about_text = (
                "IMFOC | IMage FOrmat Converter \n\n"
                "This is an open-source tool that allows you to convert image files to different formats.\n\n"
                "Features:\n"
                "• Supported formats: PNG, JPEG, GIF, BMP, TIFF, WEBP\n"
                "• Drag and drop support\n"
                "• Background removal for PNG and WebP formats (BETA)\n"
                "• Quality adjustment for JPEG format\n"
                "• Image resizing (pixels or percentage)\n"
                "• Preset size templates\n"
                "• Keep aspect ratio\n"
                "• Turkish and English language support\n\n"
                "Developer: ALG Software Inc.©\n"
                "www.algyazilim.com | info@algyazilim.com\n\n"
                "Fatih ÖNDER (CekToR) | fatih@algyazilim.com\n"
                "GitHub: https://github.com/cektor\n\n"
                "ALG Software Supports Migration to Pardus.\n\n"
                "Version: 1.0.2"
            )
            title = "About IMFOC"
        QMessageBox.information(self, title, about_text, QMessageBox.Ok)

    def change_language(self, language):
        self.current_language = "tr" if language == "Türkçe" else "en"
        self.settings.setValue("language", self.current_language)
        self.update_language()

    def update_language(self):
        if self.current_language == "tr":
            # Türkçe metinler
            self.setWindowTitle('IMFOC')
            self.info_label_format.setText("Hedef Format")
            self.info_label_quality.setText("JPEG Kalitesi")
            self.drag_label.setText("Görüntü dosyasını buraya sürükleyin veya tıklayın.")
            self.button_about.setText("Hakkında")
            self.remove_bg_checkbox.setText("Arka Planı Kaldır (BETA)")
            self.resize_group.setTitle("Boyutlandırma")
            self.resize_checkbox.setText("Boyutlandır")
            self.preset_size_label.setText("Hazır Boyutlar:")
            self.width_label.setText("Genişlik:")
            self.height_label.setText("Yükseklik:")
            self.keep_aspect_ratio.setText("En Boy Oranını Koru")
            self.size_type_group.clear()
            self.size_type_group.addItems(["Piksel", "Yüzde"])
            self.preset_size_combo.clear()
            self.preset_size_combo.addItems([
                "Özel",
                "1920x1080 (Full HD)",
                "1280x720 (HD)",
                "800x600",
                "640x480"
            ])
            # Durum mesajları
            self.status_messages = {
                'converting': 'Dönüştürülüyor...',
                'completed': 'Dönüştürme tamamlandı!',
                'error': 'Hata oluştu!',
                'unsupported': 'Desteklenmeyen dosya formatı.',
                'removing_bg': 'Arka plan kaldırılıyor...',
                'bg_failed': 'Arka plan kaldırma işlemi başarısız oldu.'
            }
        else:
            # İngilizce metinler
            self.setWindowTitle('IMFOC')
            self.info_label_format.setText("Target Format")
            self.info_label_quality.setText("JPEG Quality")
            self.drag_label.setText("Drag and drop an image file here or click to select.")
            self.button_about.setText("About")
            self.remove_bg_checkbox.setText("Remove Background (BETA)")
            self.resize_group.setTitle("Resize")
            self.resize_checkbox.setText("Resize Image")
            self.preset_size_label.setText("Preset Sizes:")
            self.width_label.setText("Width:")
            self.height_label.setText("Height:")
            self.keep_aspect_ratio.setText("Keep Aspect Ratio")
            self.size_type_group.clear()
            self.size_type_group.addItems(["Pixels", "Percent"])
            self.preset_size_combo.clear()
            self.preset_size_combo.addItems([
                "Custom",
                "1920x1080 (Full HD)",
                "1280x720 (HD)",
                "800x600",
                "640x480"
            ])
            # Status messages
            self.status_messages = {
                'converting': 'Converting...',
                'completed': 'Conversion completed!',
                'error': 'An error occurred!',
                'unsupported': 'Unsupported file format.',
                'removing_bg': 'Removing background...',
                'bg_failed': 'Background removal failed.'
            }

    def toggle_resize_options(self, enabled):
        """Boyutlandırma seçeneklerini etkinleştirir/devre dışı bırakır."""
        self.resize_group.setVisible(enabled)
        if enabled:
            self.preset_size_combo.setEnabled(True)
            self.width_input.setEnabled(True)
            self.height_input.setEnabled(True)
            self.keep_aspect_ratio.setEnabled(True)
            self.preset_size_label.setEnabled(True)

    def update_size_inputs(self, preset):
        """Hazır boyut seçildiğinde boyut girişlerini günceller."""
        if preset == "1920x1080 (Full HD)":
            self.width_input.setValue(1920)
            self.height_input.setValue(1080)
        elif preset == "1280x720 (HD)":
            self.width_input.setValue(1280)
            self.height_input.setValue(720)
        elif preset == "800x600":
            self.width_input.setValue(800)
            self.height_input.setValue(600)
        elif preset == "640x480":
            self.width_input.setValue(640)
            self.height_input.setValue(480)

    def change_size_type(self, size_type):
        """Boyutlandırma tipini değiştirir (Piksel/Yüzde)."""
        if size_type == "Piksel":
            self.width_input.setRange(1, 10000)
            self.height_input.setRange(1, 10000)
            self.width_input.setValue(800)
            self.height_input.setValue(600)
            self.preset_size_combo.setEnabled(True)
        else:  # Yüzde
            self.width_input.setRange(1, 1000)
            self.height_input.setRange(1, 1000)
            self.width_input.setValue(100)
            self.height_input.setValue(100)
            self.preset_size_combo.setEnabled(False)  # Yüzde modunda hazır boyutları devre dışı bırak

    def remove_bg_clicked(self):
        try:
            input_path = self.input_path_edit.text()
            if not input_path:
                self.show_error(self.tr("Please select an input file."))
                return
            
            output_path = self.output_path_edit.text()
            if not output_path:
                self.show_error(self.tr("Please select an output path."))
                return
            
            # Arkaplan kaldırma işlemini gerçekleştir
            remove_background(input_path, output_path)
            
            self.show_info(self.tr("Background removal completed successfully!"))
            
        except Exception as e:
            self.show_error(str(e))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    if ICON_PATH:
        app.setWindowIcon(QIcon(ICON_PATH))
    ex = ImageConverter()
    ex.show()
    sys.exit(app.exec_())
