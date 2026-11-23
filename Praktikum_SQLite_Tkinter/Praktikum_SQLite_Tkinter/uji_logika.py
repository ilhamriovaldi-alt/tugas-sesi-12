"""Uji logika aplikasi tanpa GUI: tkinter diganti objek tiruan, database SQLite asli."""
import sys, types, sqlite3, os, itertools

# ---------- tkinter tiruan ----------
class Widget:
    def __init__(self, *a, **k): self.text = ""; self.kw = k
    def grid(self, **k): pass
    def pack(self, **k): pass
    def bind(self, *a): pass
    def focus_set(self): pass
    def geometry(self, *a): pass
    def title(self, *a): pass
    def mainloop(self): pass
    def get(self): return self.text
    def set(self, v): self.text = v
    def insert(self, i, v): self.text = self.text[:i] + str(v) + self.text[i:]
    def delete(self, a, b=None): self.text = ""
    def heading(self, *a, **k): pass
    def column(self, *a, **k): pass

class Tree(Widget):
    def __init__(self, *a, **k):
        super().__init__(); self.items = {}; self.sel = (); self.n = itertools.count(1)
    def get_children(self): return tuple(self.items)
    def delete(self, i): self.items.pop(i, None)
    def insert(self, p, pos, values): i = f"I{next(self.n)}"; self.items[i] = tuple(str(v) for v in values); return i
    def selection(self): return self.sel
    def item(self, i, opt): return self.items[i]

tk = types.ModuleType("tkinter"); ttk = types.ModuleType("tkinter.ttk"); mb = types.ModuleType("tkinter.messagebox")
tk.Tk = Widget; tk.END = 10**6
for n in ["Entry","Label","LabelFrame","Frame","Button","Combobox"]: setattr(ttk, n, Widget)
ttk.Treeview = Tree
log = []; jawab_ya = [True]
mb.showinfo = lambda t, m: log.append(("info", t)); mb.showwarning = lambda t, m: log.append(("warn", t))
mb.showerror = lambda t, m: log.append(("error", t)); mb.askyesno = lambda t, m: jawab_ya[0]
tk.ttk = ttk; tk.messagebox = mb
sys.modules.update({"tkinter": tk, "tkinter.ttk": ttk, "tkinter.messagebox": mb})

src = open(sys.argv[1], encoding="utf-8").read()
ns = {"__name__": "app"}
exec(compile(src, "aplikasi_mahasiswa.py", "exec"), ns)

def isi(nama, nim, prodi, alamat="", angk=""):
    ns["bersihkan_form"]()
    ns["entry_nama"].text, ns["entry_nim"].text, ns["combo_prodi"].text = nama, nim, prodi
    ns["entry_alamat"].text, ns["entry_angkatan"].text = alamat, angk
def rows(): return list(ns["tabel"].items.values())
def db(q, p=()):
    c = sqlite3.connect("mahasiswa.db"); r = c.execute(q, p).fetchall(); c.close(); return r
hasil = []
def cek(nama, kondisi): hasil.append((nama, bool(kondisi))); print(("LULUS " if kondisi else "GAGAL ") + nama)

# 1 data valid
log.clear(); isi("Andi", "00123", "Informatika", "Jombang", "2023"); ns["simpan_data"]()
cek("1 Data valid: tampil di tabel + info Berhasil", len(rows())==1 and ("info","Berhasil") in log)
cek("1b NIM berawalan nol tetap '00123' di database", db("select nim from mahasiswa")[0][0]=="00123")
# 2 kosong
for nama, nim, prodi in [("", "1", "Informatika"), ("B", "", "Informatika"), ("B", "1", "")]:
    log.clear(); isi(nama, nim, prodi); ns["simpan_data"]()
    cek(f"2 Masukan kosong ({nama!r},{nim!r},{prodi!r}) ditolak", ("warn","Validasi") in log and db("select count(*) from mahasiswa")[0][0]==1)
# angkatan tidak valid
log.clear(); isi("C", "9", "Akuntansi", "", "23"); ns["simpan_data"]()
cek("2b Angkatan tidak 4 digit ditolak", ("warn","Validasi") in log and db("select count(*) from mahasiswa")[0][0]==1)
# 3 duplikat
log.clear(); isi("Dobel", "00123", "Manajemen"); ns["simpan_data"]()
cek("3 NIM duplikat ditolak (NIM Duplikat)", ("error","NIM Duplikat") in log and db("select count(*) from mahasiswa")[0][0]==1)
# tambah data lain untuk uji
isi("Budi Santoso", "23002", "Sistem Informasi", "Surabaya", "2022"); ns["simpan_data"]()
isi("Citra", "23003", "Akuntansi", "", ""); ns["simpan_data"]()
cek("1c Alamat/angkatan kosong tersimpan sebagai kosong", db("select alamat, angkatan from mahasiswa where nim='23003'")[0]==("", None))
# 4 refresh
ns["tabel"].items.clear(); ns["refresh_data"]()
cek("4 Refresh memuat ulang 3 baris dari database", len(rows())==3)
# pencarian
ns["entry_cari"].text="budi"; ns["cari_data"](); cek("P1 Cari nama 'budi' -> 1 hasil", len(rows())==1)
ns["entry_cari"].text="0012"; ns["cari_data"](); cek("P2 Cari NIM '0012' -> 1 hasil", len(rows())==1 and rows()[0][2]=="00123")
ns["entry_cari"].text="zzz"; ns["cari_data"](); cek("P3 Cari tidak ada -> 0 hasil", len(rows())==0)
ns["entry_cari"].text="' OR 1=1 --"; ns["cari_data"](); cek("P4 Input injeksi diperlakukan sebagai teks -> 0 hasil", len(rows())==0)
ns["reset_pencarian"](); cek("P5 Reset menampilkan semua (3)", len(rows())==3)
# 6 ubah
t = ns["tabel"]; item = [i for i,v in t.items.items() if v[2]=="23002"][0]; t.sel=(item,)
ns["isi_form_dari_tabel"](); cek("6a Form terisi dari record terpilih", ns["entry_nama"].get()=="Budi Santoso" and ns["entry_angkatan"].get()=="2022")
ns["entry_nama"].text="Budi Hartono"; log.clear(); ns["ubah_data"]()
cek("6 Ubah: nama baru tampil di tabel & database", db("select nama from mahasiswa where nim='23002'")[0][0]=="Budi Hartono" and any(v[1]=="Budi Hartono" for v in rows()))
# ubah ke NIM milik data lain
item = [i for i,v in t.items.items() if v[2]=="23002"][0]; t.sel=(item,); ns["isi_form_dari_tabel"](); ns["entry_nim"].text="00123"; log.clear(); ns["ubah_data"]()
cek("6b Ubah NIM jadi NIM data lain ditolak", ("error","NIM Duplikat") in log)
# ubah tanpa pilih
t.sel=(); log.clear(); ns["ubah_data"](); cek("6c Ubah tanpa memilih baris -> peringatan", ("warn","Pilih Data") in log)
# 5 hapus
item = [i for i,v in t.items.items() if v[2]=="23003"][0]; t.sel=(item,)
jawab_ya[0]=False; ns["hapus_data"](); cek("5a Hapus dibatalkan -> data tetap", db("select count(*) from mahasiswa")[0][0]==3)
jawab_ya[0]=True; t.sel=(item,); ns["hapus_data"]()
cek("5 Hapus: hilang dari tabel dan database", len(rows())==2 and db("select count(*) from mahasiswa where nim='23003'")[0][0]==0)
t.sel=(); log.clear(); ns["hapus_data"](); cek("5b Hapus tanpa memilih -> peringatan", ("warn","Pilih Data") in log)
# 7 persistensi: jalankan ulang aplikasi pada file db yang sama
ns2 = {"__name__": "app"}; exec(compile(src, "aplikasi_mahasiswa.py", "exec"), ns2)
cek("7 Persistensi: aplikasi dijalankan ulang, 2 data lama tetap ada", len(ns2["tabel"].items)==2)

# migrasi database lama tanpa kolom angkatan
os.remove("mahasiswa.db")
c = sqlite3.connect("mahasiswa.db")
c.execute("CREATE TABLE mahasiswa (id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT NOT NULL, nim TEXT NOT NULL UNIQUE, prodi TEXT NOT NULL, alamat TEXT)")
c.execute("INSERT INTO mahasiswa (nama,nim,prodi,alamat) VALUES ('Lama','00999','Informatika','Jombang')"); c.commit(); c.close()
ns3 = {"__name__": "app"}; exec(compile(src, "aplikasi_mahasiswa.py", "exec"), ns3)
cols = [r[1] for r in db("pragma table_info(mahasiswa)")]
cek("M Migrasi: DB lama mendapat kolom angkatan, data lama utuh", "angkatan" in cols and db("select nama,nim,angkatan from mahasiswa")[0]==("Lama","00999",None) and len(ns3["tabel"].items)==1)

print(f"\nTOTAL: {sum(1 for _,k in hasil if k)}/{len(hasil)} lulus")
