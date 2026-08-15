import streamlit as st
import sqlite3
import pandas as pd

# ==========================================
# 1. SETUP DATABASE & TABEL (SQLite)
# ==========================================
DB_NAME = "kokurikuler.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Tabel Modul
    c.execute('''
        CREATE TABLE IF NOT EXISTS modules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            target_class TEXT NOT NULL,
            integrated_subjects TEXT,
            target_characters TEXT,
            schedule_type TEXT,
            target_jp INTEGER DEFAULT 180,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Tabel Sesi
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_id INTEGER NOT NULL,
            session_title TEXT NOT NULL,
            allocated_jp INTEGER NOT NULL,
            facilitator_guide TEXT,
            student_activity TEXT,
            character_focus TEXT,
            character_indicators TEXT,
            FOREIGN KEY(module_id) REFERENCES modules(id) ON DELETE CASCADE
        )
    ''')
    # Tabel Observasi
    c.execute('''
        CREATE TABLE IF NOT EXISTS character_observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            group_or_student TEXT NOT NULL,
            score_level TEXT NOT NULL,
            notes TEXT,
            observed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Helper DB Functions
def run_query(query, params=()):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()

def fetch_data(query, params=()):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

# ==========================================
# 2. KONFIGURASI UI/UX STREAMLIT
# ==========================================
st.set_page_config(page_title="KokuFlow - Panduan Kokurikuler", layout="wide")

# CSS Injection untuk menyembunyikan elemen default Streamlit
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

st.title("🌱 KokuFlow: Generator & Observasi Kokurikuler")
st.markdown("Membantu Koordinator merancang aktivitas dan Fasilitator memandu serta menilai karakter siswa dengan mudah.")

# ==========================================
# 3. TABS NAVIGASI UTAMA
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs([
    "🎯 Mode Fasilitator (Kelas)", 
    "🛠️ Koordinator: Sesi & Aktivitas", 
    "📁 Kelola Modul Proyek", 
    "🖨️ Rekap Observasi & Cetak"
])

# ------------------------------------------
# TAB 3: KELOLA MODUL PROYEK (Create & View Modules)
# ------------------------------------------
with tab3:
    st.header("Kelola Modul Proyek Kokurikuler")
    
    with st.expander("➕ Tambah Modul Baru", expanded=True):
        with st.form("form_tambah_modul"):
            m_title = st.text_input("Judul / Tema Modul (Contoh: Gaya Hidup Berkelanjutan)")
            m_class = st.text_input("Kelas / Fase (Contoh: Kelas 7 / Fase D)")
            m_subjects = st.text_input("Mata Pelajaran Terintegrasi (Koma dipisah)")
            m_chars = st.text_input("Dimensi Karakter Fokus (Contoh: Gotong Royong, Kreatif)")
            m_schedule = st.selectbox("Sistem Alokasi Waktu", ["Blok (10 JP/Minggu)", "Cicil Harian (2 JP/Hari)"])
            m_jp = st.number_input("Target Total JP per Semester", min_value=10, value=180)
            
            submit_modul = st.form_submit_button("Simpan Modul")
            if submit_modul:
                if m_title:
                    run_query("INSERT INTO modules (title, target_class, integrated_subjects, target_characters, schedule_type, target_jp) VALUES (?, ?, ?, ?, ?, ?)", 
                              (m_title, m_class, m_subjects, m_chars, m_schedule, m_jp))
                    st.success("Modul berhasil ditambahkan!")
                    st.rerun()
                else:
                    st.error("Judul modul wajib diisi!")

    st.subheader("Daftar Modul Saat Ini")
    df_modules = fetch_data("SELECT * FROM modules")
    if not df_modules.empty:
        st.dataframe(df_modules, use_container_width=True)
    else:
        st.info("Belum ada modul yang dibuat.")

# ------------------------------------------
# TAB 2: KOORDINATOR - SUSUN SESI & AKTIVITAS
# ------------------------------------------
with tab2:
    st.header("Susun Alur Pertemuan & Aktivitas Siswa")
    
    if df_modules.empty:
        st.warning("Silakan buat modul di tab 'Kelola Modul Proyek' terlebih dahulu.")
    else:
        # Pilih Modul
        mod_options = dict(zip(df_modules['id'], df_modules['title'] + " (" + df_modules['target_class'] + ")"))
        selected_mod_id = st.selectbox("Pilih Modul Proyek:", options=list(mod_options.keys()), format_func=lambda x: mod_options[x], key="mod_sel_tab2")
        
        # Hitung JP terpakai
        df_ses_jp = fetch_data("SELECT SUM(allocated_jp) as total_jp FROM sessions WHERE module_id=?", (selected_mod_id,))
        total_jp_used = df_ses_jp['total_jp'].iloc[0] if pd.notnull(df_ses_jp['total_jp'].iloc[0]) else 0
        target_jp = int(df_modules[df_modules['id'] == selected_mod_id]['target_jp'].iloc[0])
        
        st.metric(label="Total JP Terpakai", value=f"{total_jp_used} / {target_jp} JP", delta=f"Sisa {target_jp - total_jp_used} JP")
        if total_jp_used >= target_jp:
            st.success("🎉 Alokasi JP sudah memenuhi target semester!")
        
        with st.expander("➕ Tambah Sesi Pertemuan Baru", expanded=False):
            with st.form("form_tambah_sesi"):
                s_title = st.text_input("Judul Pertemuan / Aktivitas (Contoh: Eksplorasi Masalah Sampah)")
                s_jp = st.number_input("Alokasi JP untuk Sesi Ini", min_value=1, max_value=20, value=2)
                s_guide = st.text_area("Panduan Fasilitator (Apa yang harus dilakukan guru di kelas?)", height=100)
                s_activity = st.text_area("Instruksi Lembar Tugas Siswa (Apa yang dikerjakan siswa?)", height=100)
                s_char_focus = st.text_input("Karakter yang Diobservasi (Contoh: Gotong Royong)")
                s_char_ind = st.text_area("Indikator Perilaku Karakter (Contoh: Aktif membagi tugas dalam kelompok)")
                
                submit_sesi = st.form_submit_button("Simpan Sesi")
                if submit_sesi:
                    if s_title:
                        run_query("INSERT INTO sessions (module_id, session_title, allocated_jp, facilitator_guide, student_activity, character_focus, character_indicators) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                  (selected_mod_id, s_title, s_jp, s_guide, s_activity, s_char_focus, s_char_ind))
                        st.success("Sesi berhasil ditambahkan!")
                        st.rerun()
                    else:
                        st.error("Judul sesi wajib diisi!")

        st.subheader("Daftar Sesi Pertemuan")
        df_sessions = fetch_data("SELECT id, session_title, allocated_jp, character_focus FROM sessions WHERE module_id=?", (selected_mod_id,))
        if not df_sessions.empty:
            st.table(df_sessions)
            
            # Form hapus sesi
            s_del_id = st.selectbox("Hapus Sesi (Pilih ID Sesi)", df_sessions['id'])
            if st.button("Hapus Sesi Terpilih", type="primary"):
                run_query("DELETE FROM sessions WHERE id=?", (s_del_id,))
                run_query("DELETE FROM character_observations WHERE session_id=?", (s_del_id,))
                st.success("Sesi dan data observasinya berhasil dihapus!")
                st.rerun()
        else:
            st.info("Belum ada sesi untuk modul ini.")

# ------------------------------------------
# TAB 1: MODE FASILITATOR (Buka Kelas & Nilai)
# ------------------------------------------
with tab1:
    st.header("Mode Fasilitator (Langsung Praktik)")
    
    if df_modules.empty:
        st.warning("Belum ada modul. Koordinator perlu membuatnya terlebih dahulu.")
    else:
        col1, col2 = st.columns([1, 1])
        with col1:
            f_mod_id = st.selectbox("Pilih Modul:", options=list(mod_options.keys()), format_func=lambda x: mod_options[x], key="mod_sel_tab1")
            
            df_ses_tab1 = fetch_data("SELECT * FROM sessions WHERE module_id=?", (f_mod_id,))
            if df_ses_tab1.empty:
                st.info("Belum ada sesi di modul ini.")
            else:
                ses_options = dict(zip(df_ses_tab1['id'], "Sesi " + df_ses_tab1['id'].astype(str) + " - " + df_ses_tab1['session_title'] + " (" + df_ses_tab1['allocated_jp'].astype(str) + " JP)"))
                f_ses_id = st.selectbox("Pilih Sesi Pertemuan:", options=list(ses_options.keys()), format_func=lambda x: ses_options[x])
                
                # Menampilkan Panduan & Tugas Siswa
                sesi_aktif = df_ses_tab1[df_ses_tab1['id'] == f_ses_id].iloc[0]
                
                st.markdown("---")
                st.subheader("📋 Panduan Fasilitator")
                st.info(sesi_aktif['facilitator_guide'] if sesi_aktif['facilitator_guide'] else "Tidak ada instruksi khusus.")
                
                st.subheader("🧑‍🎓 Instruksi Tugas Siswa")
                st.success(sesi_aktif['student_activity'] if sesi_aktif['student_activity'] else "Tidak ada tugas siswa.")

        with col2:
            if not df_ses_tab1.empty:
                st.subheader("📝 Input Observasi Karakter Cepat")
                st.markdown(f"**Fokus Karakter:** {sesi_aktif['character_focus']}")
                st.caption(f"*Indikator:* {sesi_aktif['character_indicators']}")
                
                with st.form("form_observasi"):
                    obs_name = st.text_input("Nama Siswa / Nama Kelompok")
                    obs_score = st.radio("Tingkat Pencapaian:", ["Mulai Berkembang", "Sedang Berkembang", "Sangat Berkembang"])
                    obs_notes = st.text_input("Catatan Perilaku Anekdot (Opsional)")
                    
                    submit_obs = st.form_submit_button("Simpan Catatan Observasi")
                    if submit_obs:
                        if obs_name:
                            run_query("INSERT INTO character_observations (session_id, group_or_student, score_level, notes) VALUES (?, ?, ?, ?)",
                                      (f_ses_id, obs_name, obs_score, obs_notes))
                            st.success("Observasi tersimpan!")
                        else:
                            st.error("Nama siswa/kelompok wajib diisi!")
                
                st.markdown("**Riwayat Observasi di Sesi Ini:**")
                df_obs = fetch_data("SELECT group_or_student, score_level, notes FROM character_observations WHERE session_id=? ORDER BY id DESC", (f_ses_id,))
                if not df_obs.empty:
                    st.dataframe(df_obs, use_container_width=True)
                else:
                    st.caption("Belum ada catatan observasi untuk sesi ini.")

# ------------------------------------------
# TAB 4: REKAP OBSERVASI & CETAK PANDUAN
# ------------------------------------------
with tab4:
    st.header("Rekap Data & Laporan")
    if df_modules.empty:
        st.info("Data belum tersedia.")
    else:
        r_mod_id = st.selectbox("Pilih Modul untuk Laporan:", options=list(mod_options.keys()), format_func=lambda x: mod_options[x], key="mod_sel_tab4")
        
        st.subheader("1. Ringkasan Modul & JP")
        mod_info = df_modules[df_modules['id'] == r_mod_id].iloc[0]
        st.write(f"**Tema:** {mod_info['title']} | **Kelas:** {mod_info['target_class']}")
        st.write(f"**Karakter Fokus Utama:** {mod_info['target_characters']}")
        
        st.subheader("2. Rekap Observasi Karakter Siswa/Kelompok")
        query_rekap = '''
            SELECT s.session_title, s.character_focus, o.group_or_student, o.score_level, o.notes
            FROM character_observations o
            JOIN sessions s ON o.session_id = s.id
            WHERE s.module_id = ?
        '''
        df_rekap = fetch_data(query_rekap, (r_mod_id,))
        if not df_rekap.empty:
            st.dataframe(df_rekap, use_container_width=True)
        else:
            st.warning("Belum ada data observasi pada modul ini.")
            
        st.caption("Gunakan CTRL+P (atau CMD+P) di browser Anda untuk mencetak halaman rekap ini.")
