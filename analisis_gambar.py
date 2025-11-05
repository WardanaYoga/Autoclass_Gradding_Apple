import cv2
import numpy as np
import os

def analisis_apel(path_gambar):
    """
    Menganalisis satu gambar apel untuk ekstraksi fitur.
    Mengembalikan dictionary berisi data fitur.
    """
    
    # --- 1. Muat Gambar ---
    img = cv2.imread(path_gambar)
    if img is None:
        print(f"Error: Tidak bisa membaca gambar dari {path_gambar}")
        return None
    
    # Ubah ukuran agar pemrosesan lebih cepat (opsional)
    # img = cv2.resize(img, (400, 400))
    
    # --- 2. Isolasi Apel (Masking Hijau) ---
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # !!! INI HARUS DI-TUNING !!!
    # Rentang warna Hijau untuk Apel Manalagi
    # Format: (HUE, SATURATION, VALUE)
    lower_green = np.array([30, 40, 40])  # Coba nilai ini dulu
    upper_green = np.array([90, 255, 255]) # Coba nilai ini dulu
    
    mask = cv2.inRange(hsv, lower_green, upper_green)
    
    # Bersihkan mask dari noise
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)
    
    # --- 3. Ekstraksi Ukuran (Kontur) ---
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    data_fitur = {
        "diameter_px": 0,
        "luas_px": 0,
        "avg_color_hsv": (0,0,0),
        "defect_percent": 0
    }

    if len(contours) > 0:
        # Asumsi kontur terbesar adalah apel
        c = max(contours, key=cv2.contourArea)
        
        # Dapatkan luas
        data_fitur["luas_px"] = cv2.contourArea(c)
        
        # Dapatkan diameter (dalam piksel)
        ((x, y), radius) = cv2.minEnclosingCircle(c)
        data_fitur["diameter_px"] = radius * 2
        
        # --- 4. Ekstraksi Warna & Cacat ---
        
        # Warna rata-rata (hanya di area apel)
        mean_hsv = cv2.mean(hsv, mask=mask)
        data_fitur["avg_color_hsv"] = (mean_hsv[0], mean_hsv[1], mean_hsv[2])

        # Deteksi Cacat (bintik coklat/hitam)
        # !!! INI JUGA HARUS DI-TUNING !!!
        lower_defect = np.array([0, 0, 0])
        upper_defect = np.array([180, 255, 80]) # Cari yg gelap (Value rendah)
        
        mask_cacat_global = cv2.inRange(hsv, lower_defect, upper_defect)
        
        # Hanya ambil cacat yang ada DI DALAM apel
        mask_cacat_pada_apel = cv2.bitwise_and(mask_cacat_global, mask, mask=None)
        
        # Hitung persentase cacat
        luas_cacat = cv2.countNonZero(mask_cacat_pada_apel)
        if data_fitur["luas_px"] > 0:
            data_fitur["defect_percent"] = (luas_cacat / data_fitur["luas_px"]) * 100
        
        
        # --- Visualisasi (Untuk Debugging) ---
        # Gambar lingkaran dan kontur di gambar asli
        cv2.drawContours(img, [c], -1, (0, 255, 0), 2) # Kontur apel (Hijau)
        cv2.circle(img, (int(x), int(y)), int(radius), (0, 255, 255), 2) # Lingkaran (Kuning)
        
        # Tampilkan gambar hasil analisis
        cv2.imshow("Hasil Analisis", img)
        cv2.imshow("Mask Apel", mask)
        cv2.imshow("Mask Cacat", mask_cacat_pada_apel)
        
        # Simpan hasil untuk dicek
        # cv2.imwrite("hasil_analisis.jpg", img)
        # cv2.imwrite("hasil_mask.jpg", mask)
        
    return data_fitur
    
# --- BAGIAN UTAMA UNTUK TES ---
if __name__ == "__main__":
    
    # !!! GANTI INI dengan path gambar apel Anda !!!
    NAMA_FILE_TES = "/home/aldiananta/proyekPerancangan/data/hasil_grading/apel_20251105_165749_308g.jpg" 
    
    if not os.path.exists(NAMA_FILE_TES):
        print(f"Error: File tes '{NAMA_FILE_TES}' tidak ditemukan.")
        print("Salin satu gambar apel dari folder 'hasil_grading' ke folder ini.")
    else:
        print(f"Menganalisis {NAMA_FILE_TES}...")
        
        fitur = analisis_apel(NAMA_FILE_TES)
        
        if fitur:
            print("\n--- Hasil Ekstraksi Fitur ---")
            print(f"Diameter (piksel): {fitur['diameter_px']:.2f} px")
            print(f"Luas (piksel): {fitur['luas_px']:.2f} px")
            print(f"Warna Rata-rata (HSV): H={fitur['avg_color_hsv'][0]:.1f}, S={fitur['avg_color_hsv'][1]:.1f}, V={fitur['avg_color_hsv'][2]:.1f}")
            print(f"Persentase Cacat: {fitur['defect_percent']:.2f} %")
            
            print("\nMenampilkan gambar hasil. Tekan 'q' untuk keluar.")
            
            # Tahan jendela gambar agar tidak langsung tertutup
            while True:
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            cv2.destroyAllWindows()
