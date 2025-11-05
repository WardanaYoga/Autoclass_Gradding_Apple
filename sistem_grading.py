import RPi.GPIO as io
from hx711 import HX711
import cv2
import time
import os

# --- PENGATURAN ---

#MASUKAN NILAI KALIBRASI DISINI
referensi_unit = 10 # dapat diganti dengan nilai baru
pin_dt = 6
pin_sck = 5
kamera_port = 0
berat_minim_apel = 30 # asumsi

# INISIALISASI KOMPONEN
print("Inisialisasi sistem")

# INISIALISASI HX711
hx = HX711(dout = pin_dt, pd_sck = pin_sck)
hx.set_reference_unit(referensi_unit)
hx.tare()
print("timbangan telah siap")

# INISIALISASI KAMERA
cap = cv2.VideoCapture(kamera_port)
if not cap.isOpened():
	print("error kamera di port {kamera_port}")
	io.cleanup()
	exit()
print("kamera siap!!!")

# MEMBUAT FOLDER UNTUK MENYIMPAN GAMBAR
folder_name = "/home/aldiananta/proyekPerancangan/data"
if not os.path.exists (folder_name):
	os.makedirs(folder_name)
	print(f"Folder '{folder_name}' berhasil dibuat!")
else:
	print(f"Folder '{folder_name}' sudah ada...")
	
# --- LOOP UTAMA ---
try : 
	while True:
		# Memabaca berat mengambil rata rata 5 bacaan agar lebih stabil
		berat = hx.get_weight(5)
		
		# Menampilkan status
		print(f"status: menunggu... Berat terdeteksi: {berat:.2f} g")
		
		# Cek apakah terdapat apel
		if berat > berat_minim_apel:
			print(f"\nObjek terdeteksi! berat: {berat: .2f} g")
			time.sleep(1)
			
		# Ambil gambar
		ret, frame = cap.read()
		if ret:
			# membuat nama file berdasarkan waktu
			timestamp = time.strftime("%y%m%d_%H%M%S")
			nama_file = f"hasil_grading/apel_{timestamp}__{berat: .0f}g.jpg"
			save_path = os.path.join(folder_name,nama_file)
			
			cv2.imwrite(save_path, frame)
			print(f"gambar disimpan sebagai: {nama_file}")
			
			# logika grading
			
			print("menunggu objek diambil...")
			
			# tunggu sampai beratnya kembali ke nol
			while hx.get_weight(5) > berat_minim_apel:
				time.sleep(0.5)
			print("objek telah diambil. sistem siap kembali")
			hx.tare() # nol kan lagi agar timbangan akurat
			
		else:
			print("error : gagal mengambil gambar")
	time.sleep(0.1)
	
except (KeyboardInterrupt, SystemExit):
	print("\nMematikan sistem...")
finally:
	cap.release()
	io.cleanup()
	print("sistem mati")

