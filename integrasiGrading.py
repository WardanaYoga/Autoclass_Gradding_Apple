import RPi.GPIO as io
from hx711 import HX711
import cv2
import time
import os
import numpy as np

# --- PENGATURAN ---
# !!! PASTIKAN NILAI INI DIDAPAT DARI SKRIP KALIBRASI !!!
referensi_unit = 432.123  # GANTI DENGAN NILAI KALIBRASI TIMBANGAN ANDA
pin_dt = 6
pin_sck = 5
kamera_port = 0
berat_minim_apel = 30  # gram

# !!! MASUKKAN NILAI KALIBRASI PIKSEL ANDA DI SINI !!!
# (Didapat dari langkah 1 di atas)
PIKSEL_PER_CM = 50.0  # GANTI DENGAN NILAI ANDA (misal: 130px / 2.6cm = 50)

# --- FUNGSI ANALISIS GAMBAR (Kita copy-paste dari skrip sebelumnya) ---

def analisis_apel(path_gambar, piksel_per_cm):
    """
    Menganalisis satu gambar apel untuk ekstraksi fitur.
    Mengembalikan dictionary berisi data fitur.
    """
    img = cv2.imread(path_gambar)
    if img is None:
        return None
    
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Rentang warna Hijau (Gunakan nilai tuning Anda)
    lower_green = np.array([30, 40, 40])
    upper_green = np.array([90, 255, 255])
    mask = cv2.inRange(hsv, lower_green, upper_green)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    data_fitur = {
        "diameter_cm": 0,
        "defect_percent": 0
    }

    if len(contours) > 0:
        c = max(contours, key=cv2.contourArea)
        luas_apel_px = cv2.contourArea(c)
        
        # Hitung diameter
        ((x, y), radius_px) = cv2.minEnclosingCircle(c)
        diameter_px = radius_px * 2
        
        # --- Konversi Piksel ke CM ---
        data_fitur["diameter_cm"] = diameter_px / piksel_per_cm
        
        # Deteksi Cacat (Gunakan nilai tuning Anda)
        lower_defect = np.array([0, 0, 0])
        upper_defect = np.array([180, 255, 80]) # Cari yg gelap
        
        mask_cacat_global = cv2.inRange(hsv, lower_defect, upper_defect)
        mask_cacat_pada_apel = cv2.bitwise_and(mask_cacat_global, mask, mask=None)
        
        luas_cacat_px = cv2.countNonZero(mask_cacat_pada_apel)
        if luas_apel_px > 0:
            data_fitur["defect_percent"] = (luas_cacat_px / luas_apel_px) * 100
            
    return data_fitur

# --- FUNGSI LOGIKA GRADING ---

def tentukan_grade(berat, diameter, cacat):
    """
    Menentukan grade apel berdasarkan aturan.
    INI HANYA CONTOH! Ganti aturannya sesuai kebutuhan Anda.
    """
    print(f"--- Menganalisis Fitur ---")
    print(f"Berat: {berat:.1f} g")
    print(f"Diameter: {diameter:.2f} cm")
    print(f"Cacat: {cacat:.1f} %")
    
    # --- ATURAN GRADE (CONTOH) ---
    if berat > 150 and diameter > 7.0 and cacat < 5:
        return "GRADE A (Super)"
    
    elif (berat > 120 or diameter > 6.0) and cacat < 15:
        return "GRADE B (Baik)"
    
    else:
        return "GRADE C (Jus/Olahan)"

# --- INISIALISASI SISTEM (Sama seperti sebelumnya) ---
print("Inisialisasi sistem...")
io.setmode(io.BCM) 
hx = HX711(dout=pin_dt, pd_sck=pin_sck)
hx.set_reference_unit(referensi_unit)
hx.tare()
print("Timbangan siap!")
cap = cv2.VideoCapture(kamera_port)
if not cap.isOpened():
    print(f"Error kamera di port {kamera_port}")
    io.cleanup()
    exit()
print("Kamera siap!")
base_folder = "/home/aldiananta/proyekPerancangan/data"
hasil_folder = os.path.join(base_folder, "hasil_grading")
if not os.path.exists(hasil_folder):
    os.makedirs(hasil_folder)
print(f"Folder '{hasil_folder}' siap...")

# --- LOOP UTAMA (Dengan Penambahan Analisis) ---
try:
    while True:
        berat = hx.get_weight(5)
        print(f"Status: menunggu... Berat terdeteksi: {berat:.2f} g", end='\r')

        if berat > berat_minim_apel:
            print(f"\nObjek terdeteksi! Berat awal: {berat:.2f} g")
            time.sleep(1) # Tunggu stabil
            
            # Ambil berat akhir yang lebih stabil
            berat_final = hx.get_weight(5)
            
            ret, frame = cap.read()
            if ret:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                nama_file = f"apel_{timestamp}_{int(berat_final)}g.jpg"
                save_path = os.path.join(hasil_folder, nama_file)

                cv2.imwrite(save_path, frame)
                print(f"Gambar disimpan sebagai: {save_path}")

                # --- PROSES BARU DIMULAI DI SINI ---
                print("Memulai analisis gambar...")
                fitur = analisis_apel(save_path, PIKSEL_PER_CM)
                
                if fitur:
                    # Tentukan grade-nya
                    grade_apel = tentukan_grade(
                        berat_final, 
                        fitur["diameter_cm"], 
                        fitur["defect_percent"]
                    )
                    
                    print(f"\n>>> HASIL AKHIR: {grade_apel} <<<")
                    
                    # (Di sinilah Anda bisa menambahkan kode 
                    #  untuk menggerakkan servo/aktuator)
                    # if grade_apel == "GRADE A":
                    #    servo_A.gerak()
                    
                else:
                    print("Error: Gagal menganalisis gambar.")
                # --- PROSES BARU SELESAI ---

                print("\nMenunggu objek diambil...")
                while hx.get_weight(5) > berat_minim_apel:
                    time.sleep(0.5)

                print("Objek telah diambil. Sistem siap kembali.")
                hx.tare()
            else:
                print("Error: gagal mengambil gambar")

        time.sleep(0.1)

except (KeyboardInterrupt, SystemExit):
    print("\nMematikan sistem...")
finally:
    cap.release()
    io.cleanup()
    print("Sistem mati.")
