import sys
import os
from PIL import Image
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QComboBox, QMessageBox
from PyQt5.QtGui import QIcon, QPixmap, QFont
from PyQt5.QtCore import Qt, QEvent, QSettings


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
        self.setFixedSize(300, 500)

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
        self.format_selector.currentTextChanged.connect(self.toggle_quality_selector)
        layout.addWidget(self.format_selector)

        self.info_label_quality = QLabel(self)
        layout.addWidget(self.info_label_quality)
        self.info_label_quality.setVisible(False)

        self.quality_selector = QComboBox(self)
        self.quality_selector.addItems([str(i) for i in range(10, 101, 10)])
        self.quality_selector.setVisible(False)
        layout.addWidget(self.quality_selector)

        self.status_label = QLabel('', self)
        layout.addWidget(self.status_label)



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
        output_image_path = os.path.join(output_dir, f"{image_name}.{output_format.lower()}")

        if self.is_supported_image(input_file):
            self.convert_image_format(input_file, output_image_path, output_format, quality)
        else:
            self.status_label.setText(self.tr('Desteklenmeyen dosya formatı.'))

    def convert_image_format(self, input_image, output_image, format, quality):
        try:
            image = Image.open(input_image)
            if image.mode == 'RGBA' and format == 'JPEG':
                image = image.convert('RGB')
            image.save(output_image, format=format, quality=quality)
        except Exception as e:
            print(self.tr(f"Hata oluştu: {e}"))

    def toggle_quality_selector(self, format):
        if format == "JPEG":
            self.quality_selector.setVisible(True)
            self.info_label_quality.setVisible(True)
        else:
            self.quality_selector.setVisible(False)
            self.info_label_quality.setVisible(False)

    def is_supported_image(self, file_path):
        try:
            image = Image.open(file_path)
            image.verify()
            return True
        except (IOError, SyntaxError):
            return False

    def show_about(self):
        """Hakkında penceresini gösterir."""
        about_text = (
        "IMFOC | IMage FOrmat Converter \n\n"
        "Bu uygulama, kullanıcıların görüntü dosyalarını kolayca farklı formatlara dönüştürmesine olanak tanır. Sürükle-bırak özelliğiyle kullanıcı dostu bir deneyim sunar; bir görüntü dosyasını uygulamaya sürükleyerek veya etiket alanına tıklayarak dosya seçebilirsiniz.\n\n"
        "Geliştirici: ALG Yazılım Inc.©\n"
        "www.algyazilim.com | info@algyazilim.com\n\n"
        "Fatih ÖNDER (CekToR) | fatih@algyazilim.com\n"
        "GitHub: https://github.com/cektor\n\n"
        "ALG Yazılım Pardus'a Göç'ü Destekler.\n\n"
        "Sürüm: 1.0"
        )
        # Hakkında penceresini doğru şekilde göster
        QMessageBox.information(self, "IMFOC Hakkında", about_text, QMessageBox.Ok)

    def change_language(self, language):
        self.current_language = "tr" if language == "Türkçe" else "en"
        self.settings.setValue("language", self.current_language)
        self.update_language()

    def update_language(self):
        if self.current_language == "tr":
            self.info_label_format.setText("Hedef Formatı")
            self.info_label_quality.setText("JPEG Kalitesi")
            self.drag_label.setText("Görüntü dosyasını buraya sürükleyin veya tıklayın.")
            self.button_about.setText("Hakkında")
        else:
            self.info_label_format.setText("Target Format")
            self.info_label_quality.setText("JPEG Quality")
            self.drag_label.setText("Drag and drop an image file here or click to select.")
            self.button_about.setText("About")


def main():
    # Ana uygulama kodunuz buraya gelecek
    app = QApplication(sys.argv)
    window = ImageConverter()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
