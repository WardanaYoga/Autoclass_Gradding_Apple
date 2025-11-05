import RPi.GPIO as io
from hx711 import HX711
import cv2
import time
import os

# --- PENGATURAN ---
# !!! PASTIKAN NILAI INI DIDAPAT DARI SKRIP KALIBRASI !!!
referensi_unit = 432.123  # GANTI DENGAN NILAI KALIBRASI ANDA
pin_dt = 6
pin_sck = 5
kamera_port = 0
berat_minim_apel = 30  # gram

# --- INISIALISASI ---
print("Inisialisasi sistem...")

# Tambahkan setmode untuk kejelasan
io.setmode(io.BCM) 

hx = HX711(dout=pin_dt, pd_sck=pin_sck)
hx.set_reference_unit(referensi_unit)
hx.tare()  # Gunakan tare() untuk men-nol-kan di awal
print("Timbangan siap!")

cap = cv2.VideoCapture(kamera_port)
if not cap.isOpened():
    print(f"Error kamera di port {kamera_port}")
    io.cleanup()
    exit()
print("Kamera siap!")

# Definisikan semua path di awal
base_folder = "/home/aldiananta/proyekPerancangan/data"
hasil_folder = os.path.join(base_folder, "hasil_grading")

# Buat kedua folder jika belum ada (dipindahkan ke sini)
if not os.path.exists(base_folder):
    os.makedirs(base_folder)
    print(f"Folder '{base_folder}' berhasil dibuat!")

if not os.path.exists(hasil_folder):
    os.makedirs(hasil_folder)
    print(f"Folder '{hasil_folder}' berhasil dibuat!")
else:
    print(f"Folder '{hasil_folder}' sudah ada...")

# --- LOOP UTAMA ---
try:
    while True:
        # Ambil rata-rata 5 bacaan
        berat = hx.get_weight(5)
        
        # Gunakan end='\r' agar status tetap di satu baris
        print(f"Status: menunggu... Berat terdeteksi: {berat:.2f} g", end='\r')

        if berat > berat_minim_apel:
            # Hapus baris status sebelumnya dengan \n
            print(f"\nObjek terdeteksi! Berat: {berat:.2f} g")
            time.sleep(1) # Tunggu stabil

            ret, frame = cap.read()
            if ret:
                # Ganti %y menjadi %Y (4 digit tahun)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                
                nama_file = f"apel_{timestamp}_{int(berat)}g.jpg"
                save_path = os.path.join(hasil_folder, nama_file)

                cv2.imwrite(save_path, frame)
                # Beri nama file lengkap agar jelas
                print(f"Gambar disimpan sebagai: {save_path}")

                print("Menunggu objek diambil...")

                # Tunggu sampai objek diangkat
                while hx.get_weight(5) > berat_minim_apel:
                    time.sleep(0.5)

                print("Objek telah diambil. Sistem siap kembali.")
                hx.tare() # Nol-kan lagi timbangan, ini sudah benar!
            else:
                print("Error: gagal mengambil gambar")

        time.sleep(0.1) # Jeda agar CPU tidak 100%

except (KeyboardInterrupt, SystemExit):
    print("\nMematikan sistem...")

finally:
    cap.release()
    io.cleanup()
    print("Sistem mati.")
    print("KIW")
