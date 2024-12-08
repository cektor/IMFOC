from setuptools import setup

setup(
    name="imfoc",
    version="1.0",
    description="IMFOC - Image Format Converter",
    author="Fatih Önder",
    author_email="fatih@algyazilim.com",
    url="https://github.com/cektor/imfoc",
    packages=['imfoc'],  # Eğer bir modül dizinindeyse değiştirin, yoksa bu alanı kaldırabilirsiniz.
    install_requires=[
        'pyqt5',  # PyQt5 bağımlılığı
        'pillow',  # Pillow bağımlılığı
    ],
    package_data={
        '': ['*.png', '*.desktop'],  # Paket içindeki tüm .png ve .desktop dosyalarını ekler
    },
    data_files=[
        ('share/applications', ['imfoc.desktop']),  # Uygulama menüsüne .desktop dosyasını ekler
        ('share/icons/hicolor/48x48/apps', ['imfoclo.png']),  # Simgeyi uygun yere ekler
    ],
    entry_points={
        'gui_scripts': [
            'imfoc=imfoc:main',  # Uygulamanın giriş noktası (main fonksiyonunun adı imfoc.py'de tanımlı olmalıdır)
        ]
    },
)

