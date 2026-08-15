#https://gemini.google.com/app/410e09031b398e4f

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# ==========================================
# 1. KONFIGURASI HALAMAN & CSS
# ==========================================
st.set_page_config(
    page_title="Kasir Toko Sederhana (Offline)",
    page_icon="🛒",
    layout="wide"
)

# Injeksi CSS Kustom (Sembunyikan watermark default Streamlit & perjelas visual)
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stMetric {
            background-color: #f8f9fa;
            border-left: 5px solid #28a745;
            padding: 12px;
            border-radius: 6px;
        }
        .kasbon-metric {
            background-color: #fff3cd;
            border-left: 5px solid #ffc107;
            padding: 12px;
            border-radius: 6px;
        }
        .footer-text {
            font-size: 13px;
            color: #555555;
            border-top: 1px solid #e0e0e0;
            padding-top: 12px;
            margin-top: 30px;
            text-align: center;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. INISIALISASI DATABASE SQLITE
# ==========================================
DB_NAME = "toko_offline.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Tabel Master Produk
    c.execute("""
        CREATE TABLE IF NOT EXISTS produk (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_produk TEXT NOT NULL,
            kategori TEXT DEFAULT 'Umum',
            harga_beli REAL NOT NULL,
            harga_jual REAL NOT NULL,
            stok INTEGER NOT NULL
        )
    """)
    
    # Tabel Pelanggan & Rekap Kasbon
    c.execute("""
        CREATE TABLE IF NOT EXISTS pelanggan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_pelanggan TEXT NOT NULL UNIQUE,
            kontak_blok TEXT,
            total_utang REAL DEFAULT 0.0
        )
    """)
    
    # Tabel Transaksi (Header)
    c.execute("""
        CREATE TABLE IF NOT EXISTS transaksi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kode_transaksi TEXT UNIQUE,
            tanggal_waktu TEXT,
            total_belanja REAL,
            status_bayar TEXT,
            id_pelanggan INTEGER,
            bayar REAL,
            kembalian REAL,
            FOREIGN KEY (id_pelanggan) REFERENCES pelanggan(id)
        )
    """)
    
    # Tabel Transaksi Detail (Item Penjualan)
    c.execute("""
        CREATE TABLE IF NOT EXISTS transaksi_detail (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_transaksi INTEGER,
            id_produk INTEGER,
            nama_produk TEXT,
            harga_beli REAL,
            harga_satuan REAL,
            qty INTEGER,
            subtotal REAL,
            FOREIGN KEY (id_transaksi) REFERENCES transaksi(id),
            FOREIGN KEY (id_produk) REFERENCES produk(id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Helper Query Database
def run_query(query, params=()):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def execute_query(query, params=()):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(query, params)
    last_id = c.lastrowid
    conn.commit()
    conn.close()
    return last_id

# ==========================================
# 3. STATE MANAJEMEN KERANJANG BELANJA
# ==========================================
if "keranjang" not in st.session_state:
    st.session_state.keranjang = []

def reset_keranjang():
    st.session_state.keranjang = []

# ==========================================
# 4. SIDEBAR NAVIGASI & FOOTER
# ==========================================
st.sidebar.title("🛒 Toko Sembako Offline")
menu = st.sidebar.radio(
    "PILIH MENU",
    ["🛒 Kasir Cepat", "📦 Kelola Produk & Stok", "📒 Buku Kasbon / Utang", "📊 Laporan & Riwayat", "❓ Bantuan (Help)"]
)

st.sidebar.markdown(
    '<div class="footer-text">Dibuat oleh pawandigital (Wa : 089696380422)</div>',
    unsafe_allow_html=True
)

# ==========================================
# 5. HALAMAN: KASIR CEPAT (FAST POS)
# ==========================================
if menu == "🛒 Kasir Cepat":
    st.subheader("⚡ Kasir Cepat (Transaksi Instan)")
    
    col_input, col_cart = st.columns([1.1, 1.4])
    
    df_produk = run_query("SELECT * FROM produk WHERE stok > 0 ORDER BY nama_produk ASC")
    
    with col_input:
        st.markdown("**1. Pilih Barang**")
        if df_produk.empty:
            st.warning("Stok barang kosong atau belum diinput. Masuk ke menu 'Kelola Produk' terlebih dahulu.")
        else:
            opsi_produk = {
                f"{row['nama_produk']} | Stok: {row['stok']} | Rp {row['harga_jual']:,.0f}": row['id']
                for _, row in df_produk.iterrows()
            }
            pilihan = st.selectbox("Cari Nama Barang:", list(opsi_produk.keys()))
            id_terpilih = opsi_produk[pilihan]
            detail_prod = df_produk[df_produk["id"] == id_terpilih].iloc[0]
            
            qty = st.number_input(
                "Jumlah (Qty):", 
                min_value=1, 
                max_value=int(detail_prod['stok']), 
                value=1, 
                step=1
            )
            
            if st.button("➕ Masukkan ke Keranjang", use_container_width=True):
                sudah_ada = False
                for item in st.session_state.keranjang:
                    if item["id_produk"] == id_terpilih:
                        if item["qty"] + qty <= detail_prod['stok']:
                            item["qty"] += qty
                            item["subtotal"] = item["qty"] * item["harga_jual"]
                            sudah_ada = True
                        else:
                            st.error(f"Kuantitas melebihi sisa stok ({detail_prod['stok']})!")
                            sudah_ada = True
                        break
                
                if not sudah_ada:
                    st.session_state.keranjang.append({
                        "id_produk": id_terpilih,
                        "nama_produk": detail_prod["nama_produk"],
                        "harga_beli": detail_prod["harga_beli"],
                        "harga_jual": detail_prod["harga_jual"],
                        "qty": qty,
                        "subtotal": qty * detail_prod["harga_jual"]
                    })
                st.rerun()

    with col_cart:
        st.markdown("**2. Daftar Keranjang Belanja**")
        if st.session_state.keranjang:
            df_cart = pd.DataFrame(st.session_state.keranjang)[["nama_produk", "harga_jual", "qty", "subtotal"]]
            df_cart.columns = ["Nama Barang", "Harga", "Qty", "Subtotal"]
            st.dataframe(df_cart, use_container_width=True)
            
            total_belanja = sum(item["subtotal"] for item in st.session_state.keranjang)
            st.markdown(f"### Total Belanja: **Rp {total_belanja:,.0f}**")
            
            st.markdown("---")
            metode = st.radio("Metode Pembayaran:", ["Tunai (Lunas)", "Kasbon / Utang"], horizontal=True)
            
            id_pelanggan = None
            bayar = 0.0
            kembalian = 0.0
            
            if metode == "Tunai (Lunas)":
                bayar = st.number_input("Nominal Uang Bayar (Rp):", min_value=0.0, value=float(total_belanja), step=1000.0)
                kembalian = bayar - total_belanja
                if kembalian >= 0:
                    st.success(f"Kembalian: **Rp {kembalian:,.0f}**")
                else:
                    st.error(f"Uang kurang: Rp {abs(kembalian):,.0f}")
            else:
                df_pelanggan = run_query("SELECT * FROM pelanggan ORDER BY nama_pelanggan ASC")
                if df_pelanggan.empty:
                    st.error("Belum ada data pelanggan di Buku Kasbon. Daftarkan nama pelanggan terlebih dahulu di menu 'Buku Kasbon / Utang'!")
                else:
                    opsi_pelanggan = {
                        f"{row['nama_pelanggan']} ({row['kontak_blok']})": row['id']
                        for _, row in df_pelanggan.iterrows()
                    }
                    pilih_pel = st.selectbox("Pilih Nama Pelanggan / Warga:", list(opsi_pelanggan.keys()))
                    id_pelanggan = opsi_pelanggan[pilih_pel]
                    st.info(f"Utang sebesar **Rp {total_belanja:,.0f}** akan dicatat ke buku kasbon.")
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("🗑️ Kosongkan Keranjang", use_container_width=True):
                    reset_keranjang()
                    st.rerun()
            
            with col_b2:
                if st.button("💾 SIMPAN TRANSAKSI", type="primary", use_container_width=True):
                    if metode == "Tunai (Lunas)" and bayar < total_belanja:
                        st.error("Nominal uang yang dibayar masih kurang!")
                    elif metode == "Kasbon / Utang" and id_pelanggan is None:
                        st.error("Pilih pelanggan untuk mencatat kasbon!")
                    else:
                        kode_trx = "TRX-" + datetime.now().strftime("%y%m%d%H%M%S")
                        tgl_waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        status = "LUNAS" if metode == "Tunai (Lunas)" else "KASBON"
                        
                        id_trx = execute_query("""
                            INSERT INTO transaksi (kode_transaksi, tanggal_waktu, total_belanja, status_bayar, id_pelanggan, bayar, kembalian)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (kode_trx, tgl_waktu, total_belanja, status, id_pelanggan, bayar, kembalian))
                        
                        for item in st.session_state.keranjang:
                            execute_query("""
                                INSERT INTO transaksi_detail (id_transaksi, id_produk, nama_produk, harga_beli, harga_satuan, qty, subtotal)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (id_trx, item["id_produk"], item["nama_produk"], item["harga_beli"], item["harga_jual"], item["qty"], item["subtotal"]))
                            
                            execute_query("""
                                UPDATE produk SET stok = stok - ? WHERE id = ?
                            """, (item["qty"], item["id_produk"]))
                        
                        if status == "KASBON":
                            execute_query("""
                                UPDATE pelanggan SET total_utang = total_utang + ? WHERE id = ?
                            """, (total_belanja, id_pelanggan))
                        
                        reset_keranjang()
                        st.success(f"Transaksi {kode_trx} Berhasil Disimpan!")
                        st.rerun()
        else:
            st.info("Keranjang belanja masih kosong. Pilih barang di sebelah kiri.")

# ==========================================
# 6. HALAMAN: KELOLA PRODUK & STOK (CRUD)
# ==========================================
elif menu == "📦 Kelola Produk & Stok":
    st.subheader("📦 Kelola Produk & Stok Barang")
    tab_read, tab_create, tab_update, tab_delete = st.tabs(["📋 Data Produk", "➕ Tambah Produk", "✏️ Edit Produk", "🗑️ Hapus Produk"])
    
    with tab_read:
        df_produk = run_query("SELECT id, nama_produk, kategori, harga_beli, harga_jual, stok FROM produk ORDER BY id DESC")
        st.markdown(f"**Total Produk Terdaftar: {len(df_produk)} item**")
        
        cari = st.text_input("🔍 Cari Barang Berdasarkan Nama:", "")
        if cari:
            df_view = df_produk[df_produk["nama_produk"].str.contains(cari, case=False)]
        else:
            df_view = df_produk
        
        st.dataframe(df_view, use_container_width=True)
    
    with tab_create:
        st.markdown("**Form Tambah Barang Baru**")
        with st.form("form_tambah_produk", clear_on_submit=True):
            nama_p = st.text_input("Nama Barang (Contoh: Beras Ramos 5kg / Minyak 1L):")
            kategori_p = st.text_input("Kategori / Jenis:", value="Sembako")
            c1, c2, c3 = st.columns(3)
            with c1:
                hb = st.number_input("Harga Modal/Beli (Rp):", min_value=0.0, step=500.0)
            with c2:
                hj = st.number_input("Harga Jual (Rp):", min_value=0.0, step=500.0)
            with c3:
                stk = st.number_input("Stok Awal:", min_value=0, step=1)
            
            submit_p = st.form_submit_button("Simpan Barang Baru")
            if submit_p:
                if not nama_p.strip():
                    st.error("Nama barang tidak boleh kosong!")
                else:
                    execute_query("""
                        INSERT INTO produk (nama_produk, kategori, harga_beli, harga_jual, stok)
                        VALUES (?, ?, ?, ?, ?)
                    """, (nama_p.strip(), kategori_p.strip(), hb, hj, stk))
                    st.success(f"Barang '{nama_p}' berhasil ditambahkan!")
                    st.rerun()

    with tab_update:
        st.markdown("**Form Edit Data / Koreksi Stok Barang**")
        df_p = run_query("SELECT * FROM produk ORDER BY nama_produk ASC")
        if df_p.empty:
            st.info("Belum ada data barang untuk diedit.")
        else:
            p_opsi = {f"{r['nama_produk']} (ID: {r['id']})": r['id'] for _, r in df_p.iterrows()}
            p_pilih = st.selectbox("Pilih Barang yang Mau Diedit:", list(p_opsi.keys()))
            id_edit = p_opsi[p_pilih]
            d_edit = df_p[df_p["id"] == id_edit].iloc[0]
            
            with st.form("form_edit_produk"):
                e_nama = st.text_input("Nama Barang:", value=d_edit["nama_produk"])
                e_kat = st.text_input("Kategori:", value=d_edit["kategori"])
                c1, c2, c3 = st.columns(3)
                with c1:
                    e_hb = st.number_input("Harga Beli (Rp):", min_value=0.0, value=float(d_edit["harga_beli"]), step=500.0)
                with c2:
                    e_hj = st.number_input("Harga Jual (Rp):", min_value=0.0, value=float(d_edit["harga_jual"]), step=500.0)
                with c3:
                    e_stk = st.number_input("Stok Saat Ini:", min_value=0, value=int(d_edit["stok"]), step=1)
                
                btn_update = st.form_submit_button("Update Data Barang")
                if btn_update:
                    execute_query("""
                        UPDATE produk SET nama_produk = ?, kategori = ?, harga_beli = ?, harga_jual = ?, stok = ?
                        WHERE id = ?
                    """, (e_nama.strip(), e_kat.strip(), e_hb, e_hj, e_stk, id_edit))
                    st.success(f"Data '{e_nama}' berhasil diperbarui!")
                    st.rerun()

    with tab_delete:
        st.markdown("**Hapus Data Barang**")
        df_p = run_query("SELECT * FROM produk ORDER BY nama_produk ASC")
        if df_p.empty:
            st.info("Tidak ada barang untuk dihapus.")
        else:
            p_opsi_del = {f"{r['nama_produk']} (ID: {r['id']})": r['id'] for _, r in df_p.iterrows()}
            p_pilih_del = st.selectbox("Pilih Barang yang Mau Dihapus:", list(p_opsi_del.keys()), key="del_prod_sel")
            id_del = p_opsi_del[p_pilih_del]
            
            st.warning("⚠️ Menghapus barang tidak akan menghapus riwayat transaksi lama yang sudah tersimpan.")
            if st.button("🗑️ Konfirmasi Hapus Barang", type="primary"):
                execute_query("DELETE FROM produk WHERE id = ?", (id_del,))
                st.success("Barang berhasil dihapus!")
                st.rerun()

# ==========================================
# 7. HALAMAN: BUKU KASBON / UTANG (CRUD)
# ==========================================
elif menu == "📒 Buku Kasbon / Utang":
    st.subheader("📒 Buku Kasbon & Utang Pelanggan")
    
    tab_rekap, tab_tambah_pel, tab_bayar_utang, tab_kelola_pel = st.tabs([
        "📋 Rekap Kasbon Warga", "➕ Daftar Warga Baru", "💰 Catat Pelunasan Utang", "⚙️ Kelola / Hapus Warga"
    ])
    
    with tab_rekap:
        df_pel = run_query("SELECT id, nama_pelanggan, kontak_blok, total_utang FROM pelanggan ORDER BY total_utang DESC")
        total_semua_kasbon = df_pel["total_utang"].sum() if not df_pel.empty else 0.0
        
        st.markdown(
            f'<div class="kasbon-metric"><h4>Total Keseluruhan Uang Toko yang Belum Lunas (Kasbon): <b>Rp {total_semua_kasbon:,.0f}</b></h4></div><br>', 
            unsafe_allow_html=True
        )
        
        st.dataframe(df_pel, use_container_width=True)
    
    with tab_tambah_pel:
        st.markdown("**Daftarkan Nama Pelanggan / Warga Baru**")
        with st.form("form_tambah_warga", clear_on_submit=True):
            nama_w = st.text_input("Nama Pelanggan (Contoh: Pak Budi / Bu Siti):")
            blok_w = st.text_input("Blok Rumah / No. HP (Contoh: Blok C2 / 08123456789):")
            utang_awal = st.number_input("Kasbon Awal jika ada (Rp):", min_value=0.0, value=0.0, step=1000.0)
            
            sub_w = st.form_submit_button("Simpan Pelanggan")
            if sub_w:
                if not nama_w.strip():
                    st.error("Nama pelanggan wajib diisi!")
                else:
                    try:
                        execute_query("""
                            INSERT INTO pelanggan (nama_pelanggan, kontak_blok, total_utang)
                            VALUES (?, ?, ?)
                        """, (nama_w.strip(), blok_w.strip(), utang_awal))
                        st.success(f"Pelanggan '{nama_w}' berhasil didaftarkan!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error(f"Nama pelanggan '{nama_w}' sudah terdaftar! Gunakan nama pembeda.")

    with tab_bayar_utang:
        st.markdown("**Form Pembayaran / Cicilan Kasbon**")
        df_berutang = run_query("SELECT * FROM pelanggan WHERE total_utang > 0 ORDER BY nama_pelanggan ASC")
        
        if df_berutang.empty:
            st.success("🎉 Tidak ada pelanggan yang memiliki tunggakan kasbon saat ini.")
        else:
            opsi_utang = {
                f"{r['nama_pelanggan']} ({r['kontak_blok']}) - Sisa Utang: Rp {r['total_utang']:,.0f}": r['id']
                for _, r in df_berutang.iterrows()
            }
            pilih_u = st.selectbox("Pilih Pelanggan yang Mau Bayar:", list(opsi_utang.keys()))
            id_pel_bayar = opsi_utang[pilih_u]
            data_u = df_berutang[df_berutang["id"] == id_pel_bayar].iloc[0]
            
            with st.form("form_cicil_utang"):
                st.write(f"Nama: **{data_u['nama_pelanggan']}** | Total Utang: **Rp {data_u['total_utang']:,.0f}**")
                bayar_kasbon = st.number_input("Nominal yang Dibayarkan (Rp):", min_value=1.0, max_value=float(data_u["total_utang"]), value=float(data_u["total_utang"]), step=1000.0)
                
                btn_bayar = st.form_submit_button("Catat Pelunasan")
                if btn_bayar:
                    sisa = data_u["total_utang"] - bayar_kasbon
                    execute_query("UPDATE pelanggan SET total_utang = ? WHERE id = ?", (sisa, id_pel_bayar))
                    
                    # Update status transaksi kasbon lama jika sudah lunas
                    if sisa == 0:
                        execute_query("UPDATE transaksi SET status_bayar = 'LUNAS' WHERE id_pelanggan = ? AND status_bayar = 'KASBON'", (id_pel_bayar,))
                    
                    st.success(f"Pembayaran Rp {bayar_kasbon:,.0f} berhasil dicatat! Sisa utang: Rp {sisa:,.0f}")
                    st.rerun()

    with tab_kelola_pel:
        st.markdown("**Edit atau Hapus Data Pelanggan**")
        df_p_all = run_query("SELECT * FROM pelanggan ORDER BY nama_pelanggan ASC")
        if df_p_all.empty:
            st.info("Belum ada data pelanggan.")
        else:
            opsi_p_all = {f"{r['nama_pelanggan']} (ID: {r['id']})": r['id'] for _, r in df_p_all.iterrows()}
            pilih_p_all = st.selectbox("Pilih Pelanggan:", list(opsi_p_all.keys()))
            id_p_target = opsi_p_all[pilih_p_all]
            d_p_target = df_p_all[df_p_all["id"] == id_p_target].iloc[0]
            
            c_ed, c_del = st.columns(2)
            with c_ed:
                with st.form("form_edit_nama_pel"):
                    e_n_pel = st.text_input("Nama:", value=d_p_target["nama_pelanggan"])
                    e_k_pel = st.text_input("Blok / Kontak:", value=d_p_target["kontak_blok"])
                    if st.form_submit_button("Update Info Pelanggan"):
                        execute_query("UPDATE pelanggan SET nama_pelanggan = ?, kontak_blok = ? WHERE id = ?", (e_n_pel.strip(), e_k_pel.strip(), id_p_target))
                        st.success("Info pelanggan berhasil diperbarui!")
                        st.rerun()
            
            with c_del:
                st.write(f"Hapus data **{d_p_target['nama_pelanggan']}**?")
                if d_p_target["total_utang"] > 0:
                    st.error("⚠️ Pelanggan masih punya tunggakan utang. Lunasi dahulu sebelum dihapus.")
                else:
                    if st.button("🗑️ Hapus Data Pelanggan", type="primary"):
                        execute_query("DELETE FROM pelanggan WHERE id = ?", (id_p_target,))
                        st.success("Data pelanggan berhasil dihapus!")
                        st.rerun()

# ==========================================
# 8. HALAMAN: LAPORAN & RIWAYAT (CRUD)
# ==========================================
elif menu == "📊 Laporan & Riwayat":
    st.subheader("📊 Laporan Penjualan & Riwayat Transaksi")
    
    # Ringkasan Metrik
    df_trx = run_query("SELECT * FROM transaksi ORDER BY id DESC")
    df_detail = run_query("SELECT * FROM transaksi_detail")
    
    total_omset = df_trx["total_belanja"].sum() if not df_trx.empty else 0.0
    total_tunai = df_trx[df_trx["status_bayar"] == "LUNAS"]["total_belanja"].sum() if not df_trx.empty else 0.0
    total_utang_trx = df_trx[df_trx["status_bayar"] == "KASBON"]["total_belanja"].sum() if not df_trx.empty else 0.0
    
    # Hitung estimasi laba kotor
    if not df_detail.empty:
        laba_kotor = sum((r["harga_satuan"] - r["harga_beli"]) * r["qty"] for _, r in df_detail.iterrows())
    else:
        laba_kotor = 0.0
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Omset Transaksi", f"Rp {total_omset:,.0f}")
    with c2:
        st.metric("Tunai Diterima (Lunas)", f"Rp {total_tunai:,.0f}")
    with c3:
        st.metric("Transaksi Kasbon", f"Rp {total_utang_trx:,.0f}")
    with c4:
        st.metric("Estimasi Laba Kotor", f"Rp {laba_kotor:,.0f}")
    
    st.markdown("---")
    
    tab_list_trx, tab_detail_view, tab_hapus_trx = st.tabs(["📜 Daftar Transaksi", "🔍 Detail Item Penjualan", "🗑️ Batalkan Transaksi"])
    
    with tab_list_trx:
        if df_trx.empty:
            st.info("Belum ada riwayat transaksi penjualan.")
        else:
            st.dataframe(df_trx[["id", "kode_transaksi", "tanggal_waktu", "total_belanja", "status_bayar", "bayar", "kembalian"]], use_container_width=True)
            
    with tab_detail_view:
        if df_detail.empty:
            st.info("Belum ada detail barang terjual.")
        else:
            st.dataframe(df_detail[["id_transaksi", "nama_produk", "harga_satuan", "qty", "subtotal"]], use_container_width=True)

    with tab_hapus_trx:
        st.markdown("**Batalkan / Hapus Transaksi (Rollback Stok Otomatis)**")
        if df_trx.empty:
            st.info("Tidak ada transaksi untuk dibatalkan.")
        else:
            opsi_t_del = {
                f"{r['kode_transaksi']} - {r['tanggal_waktu']} - Rp {r['total_belanja']:,.0f} ({r['status_bayar']})": r['id']
                for _, r in df_trx.iterrows()
            }
            pilih_t_del = st.selectbox("Pilih Transaksi yang Mau Dibatalkan/Dihapus:", list(opsi_t_del.keys()))
            id_t_del = opsi_t_del[pilih_t_del]
            trx_target = df_trx[df_trx["id"] == id_t_del].iloc[0]
            
            st.error("⚠️ Membatalkan transaksi akan mengembalikan stok barang ke inventori secara otomatis.")
            if st.button("🚨 Batalkan & Hapus Transaksi Ini", type="primary"):
                # Kembalikan stok
                items = run_query("SELECT id_produk, qty FROM transaksi_detail WHERE id_transaksi = ?", (id_t_del,))
                for _, row in items.iterrows():
                    execute_query("UPDATE produk SET stok = stok + ? WHERE id = ?", (row["qty"], row["id_produk"]))
                
                # Kurangi saldo kasbon jika transaksi tersebut kasbon
                if trx_target["status_bayar"] == "KASBON" and trx_target["id_pelanggan"]:
                    execute_query("UPDATE pelanggan SET total_utang = total_utang - ? WHERE id = ?", (trx_target["total_belanja"], trx_target["id_pelanggan"]))
                
                # Hapus detail dan header transaksi
                execute_query("DELETE FROM transaksi_detail WHERE id_transaksi = ?", (id_t_del,))
                execute_query("DELETE FROM transaksi WHERE id = ?", (id_t_del,))
                st.success("Transaksi berhasil dibatalkan dan stok telah dikembalikan ke toko!")
                st.rerun()

# ==========================================
# 9. HALAMAN: BANTUAN (HELP)
# ==========================================
elif menu == "❓ Bantuan (Help)":
    st.subheader("❓ Panduan Penggunaan Kasir Toko")
    
    with st.expander("1. Cara Melakukan Transaksi Kasir Cepat (Tunai)", expanded=True):
        st.markdown("""
        * Buka menu **🛒 Kasir Cepat**.
        * Pilih barang yang dibeli pada menu dropdown, tentukan kuantitas (Qty), lalu klik tombol **➕ Masukkan ke Keranjang**.
        * Masukkan semua barang yang dibeli pembeli ke keranjang.
        * Pilih metode **Tunai (Lunas)**, masukkan uang bayar dari pembeli.
        * Klik **💾 SIMPAN TRANSAKSI**. Stok barang akan langsung berkurang otomatis.
        """)
        
    with st.expander("2. Cara Mencatat Belanja Kasbon (Utang)", expanded=False):
        st.markdown("""
        * Pastikan nama pembeli/warga sudah terdaftar di menu **📒 Buku Kasbon / Utang**.
        * Pada menu Kasir Cepat, pilih opsi pembayaran **Kasbon / Utang**.
        * Pilih nama pelanggan/warga yang berutang, lalu klik **💾 SIMPAN TRANSAKSI**.
        * Saldo utang warga tersebut akan otomatis bertambah di buku kasbon toko.
        """)
        
    with st.expander("3. Cara Mencatat Pembayaran / Cicilan Utang Warga", expanded=False):
        st.markdown("""
        * Masuk ke menu **📒 Buku Kasbon / Utang** -> pilih tab **💰 Catat Pelunasan Utang**.
        * Pilih nama warga yang ingin melunasi/mencicil.
        * Masukkan jumlah uang yang disetorkan, lalu klik **Catat Pelunasan**.
        """)

    with st.expander("4. Cara Mengisi atau Mengubah Stok Barang Toko", expanded=False):
        st.markdown("""
        * Masuk ke menu **📦 Kelola Produk & Stok**.
        * Gunakan tab **➕ Tambah Produk** untuk mendaftarkan barang baru.
        * Gunakan tab **✏️ Edit Produk** untuk menambah jumlah stok masuk atau mengganti harga beli/jual barang.
        """)

    st.info("💡 **Aplikasi ini berjalan 100% Offline**. Database tersimpan aman di file lokal komputer toko (`toko_offline.db`).")
