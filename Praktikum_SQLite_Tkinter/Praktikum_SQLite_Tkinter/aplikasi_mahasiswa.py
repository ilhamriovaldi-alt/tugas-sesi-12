"""
Aplikasi Penyimpanan Data Mahasiswa (Tkinter + SQLite)
Praktikum Dasar SQLite dan Integrasi dengan Tkinter

Fitur:
- Simpan (INSERT), tampil (SELECT), ubah (UPDATE), hapus (DELETE)
- Validasi masukan dan penanganan galat (NIM unik)
- Pencarian berdasarkan nama atau NIM (tugas pengembangan 1)
- Kolom angkatan + migrasi database lama (tugas pengembangan 2)
"""
import sqlite3
import tkinter as tk
from contextlib import contextmanager
from tkinter import ttk, messagebox

DB_NAME = "mahasiswa.db"
DAFTAR_PRODI = ["Informatika", "Sistem Informasi", "Manajemen", "Akuntansi"]


# ---------------------------------------------------------------- DATABASE
@contextmanager
def koneksi():
    """Membuka koneksi, menyimpan perubahan, lalu selalu menutupnya."""
    conn = sqlite3.connect(DB_NAME)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def buat_tabel():
    with koneksi() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mahasiswa (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                nama     TEXT NOT NULL,
                nim      TEXT NOT NULL UNIQUE,
                prodi    TEXT NOT NULL,
                alamat   TEXT,
                angkatan INTEGER
            )
        """)
        # Migrasi: database lama (tanpa kolom angkatan) diperbarui, datanya tetap aman.
        kolom_ada = [r[1] for r in conn.execute("PRAGMA table_info(mahasiswa)")]
        if "angkatan" not in kolom_ada:
            conn.execute("ALTER TABLE mahasiswa ADD COLUMN angkatan INTEGER")


def angkatan_valid(teks):
    """Angkatan boleh kosong; jika diisi harus 4 digit angka (mis. 2023)."""
    return teks == "" or (teks.isdigit() and len(teks) == 4)


buat_tabel()

# ----------------------------------------------------------------- ANTARMUKA
root = tk.Tk()
root.title("Aplikasi Data Mahasiswa")
root.geometry("900x640")

form = ttk.LabelFrame(root, text="Formulir Mahasiswa", padding=12)
form.pack(fill="x", padx=15, pady=12)

ttk.Label(form, text="Nama").grid(row=0, column=0, padx=5, pady=5, sticky="w")
entry_nama = ttk.Entry(form, width=30)
entry_nama.grid(row=0, column=1, padx=5, pady=5)

ttk.Label(form, text="NIM").grid(row=0, column=2, padx=5, pady=5, sticky="w")
entry_nim = ttk.Entry(form, width=30)
entry_nim.grid(row=0, column=3, padx=5, pady=5)

ttk.Label(form, text="Program Studi").grid(row=1, column=0, padx=5, pady=5, sticky="w")
combo_prodi = ttk.Combobox(form, values=DAFTAR_PRODI, state="readonly", width=27)
combo_prodi.grid(row=1, column=1, padx=5, pady=5)

ttk.Label(form, text="Alamat").grid(row=1, column=2, padx=5, pady=5, sticky="w")
entry_alamat = ttk.Entry(form, width=30)
entry_alamat.grid(row=1, column=3, padx=5, pady=5)

ttk.Label(form, text="Angkatan").grid(row=2, column=0, padx=5, pady=5, sticky="w")
entry_angkatan = ttk.Entry(form, width=30)
entry_angkatan.grid(row=2, column=1, padx=5, pady=5)

# Baris pencarian
frame_cari = ttk.Frame(root)
frame_cari.pack(fill="x", padx=15, pady=(0, 5))
ttk.Label(frame_cari, text="Cari (nama / NIM)").pack(side="left", padx=5)
entry_cari = ttk.Entry(frame_cari, width=30)
entry_cari.pack(side="left", padx=5)

# Treeview
kolom = ("id", "nama", "nim", "prodi", "angkatan", "alamat")
tabel = ttk.Treeview(root, columns=kolom, show="headings")

for key, judul in [("id", "ID"), ("nama", "Nama"), ("nim", "NIM"),
                   ("prodi", "Program Studi"), ("angkatan", "Angkatan"),
                   ("alamat", "Alamat")]:
    tabel.heading(key, text=judul)

tabel.column("id", width=50, anchor="center")
tabel.column("nama", width=170)
tabel.column("nim", width=110)
tabel.column("prodi", width=150)
tabel.column("angkatan", width=80, anchor="center")
tabel.column("alamat", width=240)
tabel.pack(fill="both", expand=True, padx=15, pady=8)


# -------------------------------------------------------------------- LOGIKA
def tampilkan_data(kata_kunci=""):
    """SELECT semua data, atau yang cocok dengan kata kunci nama/NIM."""
    for item in tabel.get_children():
        tabel.delete(item)

    with koneksi() as conn:
        if kata_kunci:
            pola = f"%{kata_kunci}%"
            rows = conn.execute(
                """SELECT id, nama, nim, prodi, angkatan, alamat
                   FROM mahasiswa
                   WHERE nama LIKE ? OR nim LIKE ?
                   ORDER BY id DESC""",
                (pola, pola),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT id, nama, nim, prodi, angkatan, alamat
                   FROM mahasiswa ORDER BY id DESC"""
            ).fetchall()

    for row in rows:
        # None (kolom kosong) ditampilkan sebagai teks kosong
        tabel.insert("", tk.END, values=["" if v is None else v for v in row])


def bersihkan_form():
    entry_nama.delete(0, tk.END)
    entry_nim.delete(0, tk.END)
    combo_prodi.set("")
    entry_alamat.delete(0, tk.END)
    entry_angkatan.delete(0, tk.END)
    entry_nama.focus_set()


def baca_form():
    """Mengambil seluruh isi formulir (sudah di-strip)."""
    return (entry_nama.get().strip(), entry_nim.get().strip(),
            combo_prodi.get().strip(), entry_alamat.get().strip(),
            entry_angkatan.get().strip())


def validasi(nama, nim, prodi, angkatan):
    if not nama or not nim or not prodi:
        messagebox.showwarning("Validasi", "Nama, NIM, dan Program Studi wajib diisi.")
        return False
    if not angkatan_valid(angkatan):
        messagebox.showwarning("Validasi", "Angkatan harus berupa 4 digit angka, misalnya 2023.")
        return False
    return True


def simpan_data():
    nama, nim, prodi, alamat, angkatan = baca_form()
    if not validasi(nama, nim, prodi, angkatan):
        return

    try:
        with koneksi() as conn:
            conn.execute(
                """INSERT INTO mahasiswa (nama, nim, prodi, alamat, angkatan)
                   VALUES (?, ?, ?, ?, ?)""",
                (nama, nim, prodi, alamat, int(angkatan) if angkatan else None),
            )
        messagebox.showinfo("Berhasil", "Data berhasil disimpan.")
        tampilkan_data()
        bersihkan_form()
    except sqlite3.IntegrityError:
        messagebox.showerror("NIM Duplikat", "NIM sudah terdaftar.")
    except sqlite3.Error as error:
        messagebox.showerror("Kesalahan Database", str(error))


def hapus_data():
    pilihan = tabel.selection()
    if not pilihan:
        messagebox.showwarning("Pilih Data", "Pilih baris yang akan dihapus.")
        return

    data = tabel.item(pilihan[0], "values")
    record_id = int(data[0])
    if not messagebox.askyesno("Konfirmasi", f"Hapus data {data[1]}?"):
        return

    try:
        with koneksi() as conn:
            conn.execute("DELETE FROM mahasiswa WHERE id = ?", (record_id,))
    except sqlite3.Error as error:
        messagebox.showerror("Kesalahan Database", str(error))
        return

    tampilkan_data()
    bersihkan_form()


def isi_form_dari_tabel(event=None):
    """Memuat record terpilih ke form. Data dibaca ulang dari database
    agar NIM berawalan nol (misalnya 00123) tidak berubah."""
    pilihan = tabel.selection()
    if not pilihan:
        return
    record_id = int(tabel.item(pilihan[0], "values")[0])

    with koneksi() as conn:
        row = conn.execute(
            "SELECT nama, nim, prodi, alamat, angkatan FROM mahasiswa WHERE id = ?",
            (record_id,),
        ).fetchone()
    if row is None:
        return

    bersihkan_form()
    entry_nama.insert(0, row[0])
    entry_nim.insert(0, row[1])
    combo_prodi.set(row[2])
    entry_alamat.insert(0, row[3] or "")
    entry_angkatan.insert(0, "" if row[4] is None else str(row[4]))


def ubah_data():
    pilihan = tabel.selection()
    if not pilihan:
        messagebox.showwarning("Pilih Data", "Pilih data yang akan diubah.")
        return

    record_id = int(tabel.item(pilihan[0], "values")[0])
    nama, nim, prodi, alamat, angkatan = baca_form()
    if not validasi(nama, nim, prodi, angkatan):
        return

    try:
        with koneksi() as conn:
            conn.execute(
                """UPDATE mahasiswa
                   SET nama = ?, nim = ?, prodi = ?, alamat = ?, angkatan = ?
                   WHERE id = ?""",
                (nama, nim, prodi, alamat,
                 int(angkatan) if angkatan else None, record_id),
            )
        tampilkan_data()
        bersihkan_form()
        messagebox.showinfo("Berhasil", "Data berhasil diperbarui.")
    except sqlite3.IntegrityError:
        messagebox.showerror("NIM Duplikat", "NIM sudah digunakan data lain.")
    except sqlite3.Error as error:
        messagebox.showerror("Kesalahan Database", str(error))


def cari_data():
    tampilkan_data(entry_cari.get().strip())


def reset_pencarian():
    entry_cari.delete(0, tk.END)
    tampilkan_data()


def refresh_data():
    entry_cari.delete(0, tk.END)
    tampilkan_data()


tabel.bind("<<TreeviewSelect>>", isi_form_dari_tabel)
entry_cari.bind("<Return>", lambda event: cari_data())

# --------------------------------------------------------------------- TOMBOL
ttk.Button(frame_cari, text="Cari", command=cari_data).pack(side="left", padx=4)
ttk.Button(frame_cari, text="Reset", command=reset_pencarian).pack(side="left", padx=4)

baris_tombol = ttk.Frame(root)
baris_tombol.pack(fill="x", padx=15, pady=5)

ttk.Button(baris_tombol, text="Simpan Data",
           command=simpan_data).pack(side="left", padx=4)
ttk.Button(baris_tombol, text="Ubah Data",
           command=ubah_data).pack(side="left", padx=4)
ttk.Button(baris_tombol, text="Refresh",
           command=refresh_data).pack(side="left", padx=4)
ttk.Button(baris_tombol, text="Bersihkan Form",
           command=bersihkan_form).pack(side="left", padx=4)
ttk.Button(baris_tombol, text="Hapus Data Terpilih",
           command=hapus_data).pack(side="right", padx=4)

tampilkan_data()
root.mainloop()
