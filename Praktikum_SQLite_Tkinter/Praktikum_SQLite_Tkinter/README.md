# Praktikum SQLite dan Tkinter — Aplikasi Penyimpanan Data Mahasiswa

Aplikasi desktop berbasis **Python 3, Tkinter, dan SQLite (modul `sqlite3`)** untuk menyimpan, menampilkan, mengubah, mencari, dan menghapus data mahasiswa secara permanen dalam file `mahasiswa.db`.

## Fitur

| Fitur | Keterangan |
| --- | --- |
| Simpan (INSERT) | Menyimpan data baru memakai placeholder `?` (aman dari SQL injection) |
| Tampil (SELECT) | Data tampil pada `ttk.Treeview`, data terbaru di atas |
| Ubah (UPDATE) | Klik baris, data masuk ke formulir, ubah, lalu klik **Ubah Data** |
| Hapus (DELETE) | Menghapus baris terpilih dengan konfirmasi |
| Refresh / Bersihkan Form | Memuat ulang data dari database / mengosongkan formulir |
| Pencarian | Cari berdasarkan nama atau NIM (`LIKE ?`), tombol **Cari** / **Reset** / tekan Enter |
| Kolom Angkatan | Kolom `angkatan` (INTEGER, opsional, 4 digit) pada tabel, formulir, dan Treeview |
| Validasi | Nama, NIM, Program Studi wajib diisi; NIM unik; angkatan 4 digit bila diisi |
| Penanganan galat | `IntegrityError` (NIM ganda) dan `sqlite3.Error` ditangkap, tampil pesan yang jelas |

## Struktur Database

Database: `mahasiswa.db` — Tabel: `mahasiswa`

| Kolom | Tipe | Batasan |
| --- | --- | --- |
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| nama | TEXT | NOT NULL |
| nim | TEXT | NOT NULL UNIQUE (TEXT agar NIM berawalan nol tidak hilang) |
| prodi | TEXT | NOT NULL |
| alamat | TEXT | opsional |
| angkatan | INTEGER | opsional (tugas pengembangan) |

## Cara Menjalankan

```bash
python aplikasi_mahasiswa.py
```

File `mahasiswa.db` dan tabel `mahasiswa` dibuat otomatis jika belum ada. Koneksi dikelola oleh fungsi `koneksi()` (context manager) yang melakukan *commit*, *rollback*, dan `close()` secara tertib.

## Hasil Pengujian (Bagian 2.5)

| No. | Skenario | Langkah uji | Hasil yang diharapkan | Hasil |
| --- | --- | --- | --- | --- |
| 1 | Data valid | Isi kolom wajib, klik Simpan Data | Data muncul pada tabel | ✓ |
| 2 | Masukan kosong | Kosongkan salah satu kolom wajib | Peringatan muncul; data tidak disimpan | ✓ |
| 3 | NIM duplikat | Simpan dua data dengan NIM sama | Data kedua ditolak dengan pesan galat | ✓ |
| 4 | Refresh | Klik tombol Refresh | Daftar dimuat ulang dari database | ✓ |
| 5 | Hapus | Pilih satu baris, klik Hapus, konfirmasi | Baris hilang dari tabel dan database | ✓ |
| 6 | Ubah | Pilih satu baris, ubah nama, klik Ubah Data | Nama baru tampil pada tabel | ✓ |
| 7 | Persistensi | Tutup lalu buka kembali aplikasi | Data sebelumnya tetap tersedia | ✓ |
| 8 | Pemeriksaan DB | Buka file melalui DB Browser | Tabel dan record dapat diperiksa | ☐ *(isi setelah dibuka di DB Browser)* |

Pengujian tambahan (tugas pengembangan): pencarian nama/NIM, input berisi `' OR 1=1 --` diperlakukan sebagai teks biasa, angkatan non-4-digit ditolak, ubah NIM menjadi NIM milik data lain ditolak, dan migrasi database lama.

Skenario 1–7 dan pengujian tambahan diverifikasi dengan `uji_logika.py` (23 dari 23 pengujian lulus). Jalankan dengan `python uji_logika.py aplikasi_mahasiswa.py` di folder kosong (skrip membuat dan memakai `mahasiswa.db` di folder tempat dijalankan).

## Bukti Persistensi Data

1. Jalankan aplikasi, simpan 2–3 data, tutup aplikasi.
2. Jalankan lagi `python aplikasi_mahasiswa.py`: data tetap tampil karena dibaca dari `mahasiswa.db`.
3. Buka `mahasiswa.db` di DB Browser for SQLite (tab Browse Data) untuk melihat record yang sama.

Tangkapan layar: `screenshot/form_treeview.png`, `screenshot/db_browser.png`.

## Tugas Pengembangan

**1. Pencarian.** Fungsi `tampilkan_data(kata_kunci)` memakai `WHERE nama LIKE ? OR nim LIKE ?` dengan parameter `f"%{kata_kunci}%"`. Kata kunci dikirim sebagai parameter, bukan digabung ke string SQL.

**2. Kolom angkatan.** Kolom `angkatan INTEGER` ditambahkan pada `CREATE TABLE`, formulir, Treeview, INSERT, UPDATE, dan SELECT. Untuk **file database lama yang belum memiliki kolom tersebut**, `CREATE TABLE IF NOT EXISTS` tidak mengubah tabel yang sudah ada, sehingga kolom tidak akan muncul dan SELECT/INSERT baru akan gagal dengan `no such column`. Ada dua pilihan: (a) menghapus `mahasiswa.db` (data lama hilang), atau (b) menjalankan `ALTER TABLE mahasiswa ADD COLUMN angkatan INTEGER`. Aplikasi ini memakai pilihan (b) secara otomatis di `buat_tabel()`: ia memeriksa `PRAGMA table_info(mahasiswa)` dan menjalankan `ALTER TABLE` hanya jika kolom belum ada. Data lama tetap utuh, dan kolom angkatan-nya bernilai kosong (NULL).

**3. Persistensi.** Lihat bagian "Bukti Persistensi Data" di atas.

## Jawaban Pertanyaan Refleksi

**1. Peran `connect()`, `execute()`, dan `commit()`.**
`sqlite3.connect()` membuka file `mahasiswa.db` (dan membuatnya jika belum ada) sehingga aplikasi punya jalur ke database. `execute()` mengirim perintah SQL, misalnya INSERT, ke database melalui koneksi tersebut; nilai dari formulir dikirim sebagai parameter `?` supaya diperlakukan sebagai data. Selama belum di-*commit*, perubahan masih berupa transaksi sementara. `commit()` menyimpannya secara permanen ke file, sehingga data tetap ada setelah aplikasi ditutup. Pada aplikasi ini ketiganya dibungkus fungsi `koneksi()`, yang juga melakukan `rollback()` bila terjadi galat dan selalu `close()` di akhir.

**2. Bagian paling menantang dan cara mengatasinya.**
*(Ganti dengan pengalaman Anda sendiri. Contoh:)* Bagian yang paling menantang adalah memahami alur `koneksi()` dengan `@contextmanager` serta menjaga NIM berawalan nol (mis. `00123`) agar tidak berubah menjadi `123` ketika data dibawa dari Treeview ke formulir. Saya mengatasinya dengan membaca ulang data dari database berdasarkan `id` saat baris dipilih, bukan mengambil teks dari Treeview, dan dengan menyimpan NIM sebagai TEXT.

**3. Fitur atau perlindungan data untuk bagian administrasi program studi.**
Pertama, login dan pembagian hak akses agar tidak semua orang dapat mengubah atau menghapus data. Kedua, pencadangan (*backup*) otomatis file `mahasiswa.db` secara berkala karena seluruh data berada dalam satu file. Ketiga, pencatatan riwayat perubahan (*audit log*) untuk mengetahui siapa mengubah atau menghapus data. Keempat, validasi format NIM, ekspor data ke CSV/Excel, dan pertimbangan perlindungan data pribadi (misalnya alamat) sesuai kebijakan kampus. Bila pengguna sudah banyak dan bersamaan, sebaiknya beralih ke database server seperti MySQL atau PostgreSQL.

## Berkas

- `aplikasi_mahasiswa.py` — program utama
- `mahasiswa.db` — dibuat otomatis saat aplikasi dijalankan (sertakan versi yang berisi data uji Anda)
- `uji_logika.py` — skrip uji logika
- `screenshot/` — tangkapan layar formulir + Treeview dan DB Browser
