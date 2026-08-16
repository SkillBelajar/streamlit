import streamlit as st
import sqlite3
import pandas as pd

# ==========================================
# 1. KONFIGURASI HALAMAN & CSS INJECT
# ==========================================
st.set_page_config(page_title="Koku-Master | App Kokurikuler Lintas Ilmu", page_icon="📚", layout="wide")

# Sembunyikan elemen bawaan Streamlit untuk tampilan lebih bersih
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .css-1rs6os {visibility: hidden;}
    .css-17ziqus {visibility: hidden;}
    .sidebar-footer {
        position: fixed;
        bottom: 20px;
        left: 20px;
        color: gray;
        font-size: 14px;
    }
    </style>
""", unsafe_allow_html=True)


# ==========================================
# 2. FUNGSI DATABASE (SQLite3)
# ==========================================
def get_connection():
    return sqlite3.connect("kokurikuler.db", check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Tabel 1: Master Tema
    c.execute('''CREATE TABLE IF NOT EXISTS themes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nama_tema TEXT, jenjang_kelas TEXT, mapel_terkait TEXT, benang_merah TEXT, fokus_karakter TEXT)''')
    # Tabel 2: Weekly Plans (10 JP)
    c.execute('''CREATE TABLE IF NOT EXISTS weekly_plans 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, theme_id INTEGER, minggu_ke INTEGER, alokasi_jp INTEGER DEFAULT 10, topik_mingguan TEXT, skenario_siswa TEXT, panduan_fasilitator TEXT)''')
    # Tabel 3: Kelas & Fasilitator
    c.execute('''CREATE TABLE IF NOT EXISTS facilitator_classes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, theme_id INTEGER, nama_kelas TEXT, nama_fasilitator TEXT, kontak TEXT)''')
    # Tabel 4: Rubrik Karakter
    c.execute('''CREATE TABLE IF NOT EXISTS character_rubrics 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, theme_id INTEGER, dimensi_karakter TEXT, indikator_perilaku TEXT, teknik_penilaian TEXT)''')
    conn.commit()
    conn.close()

# Inisialisasi Database
init_db()

def run_query(query, params=()):
    conn = get_connection()
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()

def get_data(query, params=()):
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

# Mengambil list tema untuk dropdown
def get_theme_dict():
    df = get_data("SELECT id, nama_tema FROM themes")
    return {row['nama_tema']: row['id'] for index, row in df.iterrows()} if not df.empty else {}


# ==========================================
# 3. SIDEBAR & MENU NAVIGASI
# ==========================================
st.sidebar.title("📚 Koku-Master")
st.sidebar.markdown("Manajemen Modul Kokurikuler")
menu = st.sidebar.radio("Navigasi Menu:", [
    "📌 Bantuan & Panduan", 
    "1️⃣ Master Tema Proyek", 
    "2️⃣ Roadmap Mingguan", 
    "3️⃣ Distribusi Kelas", 
    "4️⃣ Rubrik Penilaian", 
    "🖨️ Cetak Panduan"
])

st.sidebar.markdown('<div class="sidebar-footer"><b>Dibuat oleh pawandigital (Wa : 089696380422)</b></div>', unsafe_allow_html=True)


# ==========================================
# 4. HALAMAN KONTEN UTAMA
# ==========================================

# --- MENU: Bantuan & Panduan ---
if menu == "📌 Bantuan & Panduan":
    st.header("Selamat Datang di Aplikasi Koku-Master")
    st.markdown("""
    Aplikasi ini dirancang khusus untuk membantu Koordinator merancang kegiatan kokurikuler lintas disiplin ilmu.
    
    **Langkah-langkah Penggunaan:**
    1. **Master Tema Proyek:** Mulai dari sini. Buat tema utama, tentukan kelas, dan gabungkan mapel untuk menemukan benang merahnya.
    2. **Roadmap Mingguan:** Pecah tema tersebut ke dalam pertemuan per minggu (wajib 10 Jam Pelajaran per minggu). Tulis instruksi langkah-demi-langkah untuk siswa dan fasilitator.
    3. **Distribusi Kelas:** Petakan kelas mana saja yang menjalankan modul ini (misal: 9A, 9B) dan siapa guru fasilitatornya.
    4. **Rubrik Penilaian:** Buat lembar observasi karakter yang akan digunakan fasilitator untuk menilai siswa.
    5. **Cetak Panduan:** Lihat hasil rangkuman lengkap yang siap didistribusikan kepada guru fasilitator agar mereka tidak bingung lagi!
    """)


# --- MENU: Master Tema Proyek (CRUD) ---
elif menu == "1️⃣ Master Tema Proyek":
    st.header("Master Tema Integrasi Lintas Mapel")
    tab1, tab2, tab3 = st.tabs(["➕ Tambah Tema", "📋 Daftar Tema", "✏️ Edit / Hapus"])
    
    with tab1:
        with st.form("form_tambah_tema"):
            nama_tema = st.text_input("Nama Tema (Contoh: Pahlawan Kuliner Lokal)")
            jenjang_kelas = st.selectbox("Jenjang Kelas", ["Kelas 7", "Kelas 8", "Kelas 9", "Kelas 10", "Kelas 11", "Kelas 12"])
            mapel = st.text_area("Mata Pelajaran Terkait (Contoh: IPA, IPS, Bahasa Indonesia)")
            benang_merah = st.text_area("Benang Merah Integrasi (Konsep yang menyatukan mapel)")
            fokus_karakter = st.text_input("Fokus Dimensi Karakter (Contoh: Gotong Royong & Bernalar Kritis)")
            submit = st.form_submit_button("Simpan Tema")
            if submit and nama_tema:
                run_query("INSERT INTO themes (nama_tema, jenjang_kelas, mapel_terkait, benang_merah, fokus_karakter) VALUES (?,?,?,?,?)", 
                          (nama_tema, jenjang_kelas, mapel, benang_merah, fokus_karakter))
                st.success("Tema berhasil disimpan!")

    with tab2:
        df_themes = get_data("SELECT * FROM themes")
        if not df_themes.empty:
            st.dataframe(df_themes, use_container_width=True)
        else:
            st.info("Belum ada data.")

    with tab3:
        if not df_themes.empty:
            pilih_id = st.selectbox("Pilih ID Tema untuk diubah/hapus:", df_themes['id'].tolist())
            data_edit = df_themes[df_themes['id'] == pilih_id].iloc[0]
            
            with st.form("form_edit_tema"):
                e_nama = st.text_input("Nama Tema", data_edit['nama_tema'])
                e_kelas = st.text_input("Jenjang Kelas", data_edit['jenjang_kelas'])
                e_mapel = st.text_area("Mata Pelajaran Terkait", data_edit['mapel_terkait'])
                e_benang = st.text_area("Benang Merah Integrasi", data_edit['benang_merah'])
                e_fokus = st.text_input("Fokus Dimensi Karakter", data_edit['fokus_karakter'])
                
                col_e1, col_e2 = st.columns(2)
                update_btn = col_e1.form_submit_button("Update Data")
                delete_btn = col_e2.form_submit_button("Hapus Data", type="primary")
                
                if update_btn:
                    run_query("UPDATE themes SET nama_tema=?, jenjang_kelas=?, mapel_terkait=?, benang_merah=?, fokus_karakter=? WHERE id=?", 
                              (e_nama, e_kelas, e_mapel, e_benang, e_fokus, pilih_id))
                    st.success("Data berhasil diupdate! Silakan refresh halaman.")
                if delete_btn:
                    run_query("DELETE FROM themes WHERE id=?", (pilih_id,))
                    st.warning("Data berhasil dihapus! Silakan refresh halaman.")
        else:
            st.info("Belum ada data untuk diedit.")


# --- MENU: Roadmap Mingguan (CRUD) ---
elif menu == "2️⃣ Roadmap Mingguan":
    st.header("Perencanaan Skenario Mingguan (10 JP/Minggu)")
    themes_dict = get_theme_dict()
    
    if not themes_dict:
        st.warning("Silakan buat 'Master Tema Proyek' terlebih dahulu.")
    else:
        tab1, tab2, tab3 = st.tabs(["➕ Tambah Minggu", "📋 Daftar Roadmap", "✏️ Edit / Hapus"])
        
        with tab1:
            with st.form("form_mingguan"):
                pilih_tema = st.selectbox("Pilih Tema Terkait", list(themes_dict.keys()))
                minggu_ke = st.number_input("Minggu Ke-", min_value=1, step=1)
                alokasi_jp = st.number_input("Alokasi JP", value=10, disabled=True)
                topik = st.text_input("Topik/Sub-Tema Minggu Ini")
                skenario = st.text_area("Skenario Aktivitas Siswa (Berpusat pada siswa)")
                panduan_fasil = st.text_area("Panduan Langkah Fasilitator (Agar guru tidak bingung)")
                
                if st.form_submit_button("Simpan Roadmap"):
                    run_query("INSERT INTO weekly_plans (theme_id, minggu_ke, alokasi_jp, topik_mingguan, skenario_siswa, panduan_fasilitator) VALUES (?,?,?,?,?,?)", 
                              (themes_dict[pilih_tema], minggu_ke, alokasi_jp, topik, skenario, panduan_fasil))
                    st.success("Roadmap Mingguan berhasil disimpan!")

        with tab2:
            df_wp = get_data('''SELECT wp.id, t.nama_tema, wp.minggu_ke, wp.alokasi_jp, wp.topik_mingguan, wp.skenario_siswa, wp.panduan_fasilitator 
                                FROM weekly_plans wp JOIN themes t ON wp.theme_id = t.id''')
            # [PERBAIKAN BUG DISINI]
            if not df_wp.empty:
                st.dataframe(df_wp, use_container_width=True)
            else:
                st.info("Belum ada data.")

        with tab3:
            if not df_wp.empty:
                wp_id = st.selectbox("Pilih ID Roadmap untuk diubah/hapus:", df_wp['id'].tolist())
                wp_data = df_wp[df_wp['id'] == wp_id].iloc[0]
                with st.form("form_edit_wp"):
                    e_topik = st.text_input("Topik", wp_data['topik_mingguan'])
                    e_skenario = st.text_area("Skenario", wp_data['skenario_siswa'])
                    e_panduan = st.text_area("Panduan Fasilitator", wp_data['panduan_fasilitator'])
                    
                    c1, c2 = st.columns(2)
                    if c1.form_submit_button("Update Data"):
                        run_query("UPDATE weekly_plans SET topik_mingguan=?, skenario_siswa=?, panduan_fasilitator=? WHERE id=?", 
                                  (e_topik, e_skenario, e_panduan, wp_id))
                        st.success("Update sukses!")
                    if c2.form_submit_button("Hapus Data", type="primary"):
                        run_query("DELETE FROM weekly_plans WHERE id=?", (wp_id,))
                        st.warning("Hapus sukses!")


# --- MENU: Distribusi Kelas & Fasilitator (CRUD) ---
elif menu == "3️⃣ Distribusi Kelas":
    st.header("Pemetaan Kelas Paralel & Fasilitator")
    themes_dict = get_theme_dict()
    
    if not themes_dict:
        st.warning("Silakan buat 'Master Tema Proyek' terlebih dahulu.")
    else:
        tab1, tab2, tab3 = st.tabs(["➕ Tambah Kelas", "📋 Daftar Pemetaan", "✏️ Edit / Hapus"])
        
        with tab1:
            with st.form("form_kelas"):
                pilih_tema = st.selectbox("Tema Proyek", list(themes_dict.keys()))
                nama_kelas = st.text_input("Nama Kelas (Contoh: 9A)")
                nama_fasil = st.text_input("Nama Guru Fasilitator")
                kontak = st.text_input("Keterangan / Kontak")
                
                if st.form_submit_button("Simpan Data Kelas"):
                    run_query("INSERT INTO facilitator_classes (theme_id, nama_kelas, nama_fasilitator, kontak) VALUES (?,?,?,?)", 
                              (themes_dict[pilih_tema], nama_kelas, nama_fasil, kontak))
                    st.success("Data Kelas berhasil disimpan!")

        with tab2:
            df_fc = get_data('''SELECT fc.id, t.nama_tema, fc.nama_kelas, fc.nama_fasilitator, fc.kontak 
                                FROM facilitator_classes fc JOIN themes t ON fc.theme_id = t.id''')
            # [PERBAIKAN BUG DISINI]
            if not df_fc.empty:
                st.dataframe(df_fc, use_container_width=True)
            else:
                st.info("Belum ada data.")

        with tab3:
            if not df_fc.empty:
                fc_id = st.selectbox("Pilih ID Pemetaan:", df_fc['id'].tolist())
                fc_data = df_fc[df_fc['id'] == fc_id].iloc[0]
                with st.form("form_edit_fc"):
                    e_kelas = st.text_input("Kelas", fc_data['nama_kelas'])
                    e_fasil = st.text_input("Fasilitator", fc_data['nama_fasilitator'])
                    
                    c1, c2 = st.columns(2)
                    if c1.form_submit_button("Update"):
                        run_query("UPDATE facilitator_classes SET nama_kelas=?, nama_fasilitator=? WHERE id=?", (e_kelas, e_fasil, fc_id))
                        st.success("Update sukses!")
                    if c2.form_submit_button("Hapus", type="primary"):
                        run_query("DELETE FROM facilitator_classes WHERE id=?", (fc_id,))
                        st.warning("Hapus sukses!")


# --- MENU: Rubrik Penilaian Karakter (CRUD) ---
elif menu == "4️⃣ Rubrik Penilaian":
    st.header("Rubrik Observasi Fasilitator")
    themes_dict = get_theme_dict()
    
    if not themes_dict:
        st.warning("Silakan buat 'Master Tema Proyek' terlebih dahulu.")
    else:
        tab1, tab2, tab3 = st.tabs(["➕ Tambah Indikator", "📋 Daftar Rubrik", "✏️ Edit / Hapus"])
        
        with tab1:
            with st.form("form_rubrik"):
                pilih_tema = st.selectbox("Tema Proyek", list(themes_dict.keys()))
                dimensi = st.text_input("Dimensi Karakter (Contoh: Gotong Royong)")
                indikator = st.text_area("Indikator Perilaku yang Diamati")
                teknik = st.selectbox("Teknik Penilaian", ["Observasi", "Jurnal", "Penilaian Diri", "Penilaian Antar Teman"])
                
                if st.form_submit_button("Simpan Indikator"):
                    run_query("INSERT INTO character_rubrics (theme_id, dimensi_karakter, indikator_perilaku, teknik_penilaian) VALUES (?,?,?,?)", 
                              (themes_dict[pilih_tema], dimensi, indikator, teknik))
                    st.success("Indikator berhasil disimpan!")

        with tab2:
            df_cr = get_data('''SELECT cr.id, t.nama_tema, cr.dimensi_karakter, cr.indikator_perilaku, cr.teknik_penilaian 
                                FROM character_rubrics cr JOIN themes t ON cr.theme_id = t.id''')
            # [PERBAIKAN BUG DISINI]
            if not df_cr.empty:
                st.dataframe(df_cr, use_container_width=True)
            else:
                st.info("Belum ada data.")

        with tab3:
            if not df_cr.empty:
                cr_id = st.selectbox("Pilih ID Rubrik:", df_cr['id'].tolist())
                cr_data = df_cr[df_cr['id'] == cr_id].iloc[0]
                with st.form("form_edit_cr"):
                    e_dim = st.text_input("Dimensi", cr_data['dimensi_karakter'])
                    e_ind = st.text_area("Indikator", cr_data['indikator_perilaku'])
                    
                    c1, c2 = st.columns(2)
                    if c1.form_submit_button("Update"):
                        run_query("UPDATE character_rubrics SET dimensi_karakter=?, indikator_perilaku=? WHERE id=?", (e_dim, e_ind, cr_id))
                        st.success("Update sukses!")
                    if c2.form_submit_button("Hapus", type="primary"):
                        run_query("DELETE FROM character_rubrics WHERE id=?", (cr_id,))
                        st.warning("Hapus sukses!")


# --- MENU: Cetak Panduan ---
elif menu == "🖨️ Cetak Panduan":
    st.header("Hasil Akhir: Modul Panduan Fasilitator")
    themes_dict = get_theme_dict()
    
    if not themes_dict:
        st.warning("Data tema masih kosong.")
    else:
        pilih_tema = st.selectbox("Pilih Tema untuk Ditampilkan/Dicetak:", list(themes_dict.keys()))
        t_id = themes_dict[pilih_tema]
        
        st.markdown("---")
        # 1. Info Master
        df_t = get_data(f"SELECT * FROM themes WHERE id={t_id}").iloc[0]
        st.subheader(f"Tema: {df_t['nama_tema']}")
        st.write(f"**Kelas:** {df_t['jenjang_kelas']} | **Mapel Terintegrasi:** {df_t['mapel_terkait']}")
        st.write(f"**Benang Merah:** {df_t['benang_merah']}")
        st.write(f"**Fokus Karakter:** {df_t['fokus_karakter']}")
        
        # 2. Roadmap
        st.markdown("### 📅 Skenario Mingguan (Alokasi: 10 JP per Minggu)")
        df_wp = get_data(f"SELECT * FROM weekly_plans WHERE theme_id={t_id} ORDER BY minggu_ke ASC")
        if not df_wp.empty:
            for idx, row in df_wp.iterrows():
                with st.expander(f"Minggu Ke-{row['minggu_ke']}: {row['topik_mingguan']} (10 JP)"):
                    st.write("**Aktivitas Siswa:**")
                    st.write(row['skenario_siswa'])
                    st.write("**Panduan Fasilitator (Step-by-step):**")
                    st.info(row['panduan_fasilitator'])
        else:
            st.warning("Belum ada roadmap mingguan untuk tema ini.")
            
        # 3. Rubrik
        st.markdown("### 📊 Lembar Observasi Karakter")
        df_cr = get_data(f"SELECT * FROM character_rubrics WHERE theme_id={t_id}")
        if not df_cr.empty:
            st.table(df_cr[['dimensi_karakter', 'indikator_perilaku', 'teknik_penilaian']])
        else:
            st.warning("Belum ada rubrik karakter.")
            
        st.info("💡 Tekan CTRL+P (atau CMD+P di Mac) di browser Anda untuk menyimpan halaman ini sebagai PDF dan membagikannya ke fasilitator.")
