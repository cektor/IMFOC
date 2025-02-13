#!/usr/bin/env python3
# Nemo Image Format Converter Plugin (IMFOC - NEMO Ext)
# Converts images to PNG, JPG, GIF, BMP, TIFF, WEBP without quality loss
# https://github.com/cektor   | Fatih ÖNDER (CekToR)
# https://algyazilim.com
# https://fatihonder.org.tr

import os
import gi
import urllib.parse
from PIL import Image

gi.require_version('Nemo', '3.0')
from gi.repository import GObject, Nemo, Gtk

class IMFOC(GObject.GObject, Nemo.MenuProvider):
    def __init__(self):
        """Eklenti başlatıldığında çalıştırılacak kodlar."""
        super().__init__()
    
    def convert_image(self, menu, files, format):
        """Seçilen resmi belirlenen formata dönüştürür."""
        for file in files:
            file_path = urllib.parse.unquote(file.get_uri())  # URL kodlamasını kaldır
            if file_path.startswith("file://"):
                file_path = file_path[7:]  # "file://" ön ekini kaldır
            
            try:
                img = Image.open(file_path)
                save_path = os.path.splitext(file_path)[0] + f'.{format.lower()}'
                img.save(save_path, format=format.upper())
            except Exception as e:
                print(f"Hata: {e}")

    def open_about_page(self, menu, item):
        """Hakkında tıklandığında web sayfasını açar."""
        Gtk.show_uri(None, "https://github.com/cektor/IMFOC", Gtk.get_current_event_time())

    def get_file_items(self, window, files):
        """Sadece resim dosyaları için sağ tık menüsüne format dönüştürme seçenekleri ekler."""
        image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"}
        
        for file in files:
            if not any(file.get_name().lower().endswith(ext) for ext in image_extensions):
                return []  # Resim dosyası değilse seçenek ekleme

        submenu = Nemo.Menu()
        formats = ["PNG", "JPG", "GIF", "BMP", "TIFF", "WEBP"]
        
        for fmt in formats:
            item = Nemo.MenuItem(name=f'ConvertTo{fmt}',
                                 label=f'{fmt} olarak dönüştür',
                                 tip=f'Seçili resmi {fmt} formatına çevir',
                                 icon='image-x-generic')
            item.connect('activate', self.convert_image, files, fmt)
            submenu.append_item(item)
        
        main_item = Nemo.MenuItem(name='ConvertImage',
                                  label='IMFOC ile Dönüştür',
                                  tip='Seçili resmi farklı formata çevir',
                                  icon='image-x-generic')
        main_item.set_submenu(submenu)
        
        about_item = Nemo.MenuItem(name='AboutIMFOC',
                                   label='IMFOC Nemo Eklentisi\nFatih ÖNDER (CekToR)',
                                   tip='IMFOC hakkında bilgi',
                                   icon='dialog-information')
        about_item.connect('activate', self.open_about_page, None)  # 'None' parametre olarak geçirildi
        submenu.append_item(about_item)
        
        return [main_item]

