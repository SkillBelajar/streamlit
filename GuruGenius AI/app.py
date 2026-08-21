import streamlit as st
import sqlite3
import requests
import json
from datetime import datetime

# ==========================================
# KONFIGURASI & DATABASE SETUP
# ==========================================
st.set_page_config(page_title="GuruGenius AI", page_icon="📚", layout="wide")

# Sembunyikan elemen default Streamlit
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# Helper function untuk Database agar aman dari thread error
def get_db_connection():
    conn = sqlite3.connect('gurugenius.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Inisialisasi Tabel
def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    # Tabel Bank Soal
    c.execute('''
        CREATE TABLE IF NOT EXISTS bank_soal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mapel TEXT,
            kelas TEXT,
            topik TEXT,
            konten_soal TEXT,
            tanggal TIMESTAMP
        )
    ''')
    # Tabel Pengaturan (menyimpan API Key dan Model)
    c.execute('''
        CREATE TABLE IF NOT EXISTS pengaturan (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            api_key TEXT,
            model_name TEXT
        )
    ''')
    # Insert default settings jika kosong
    c.execute('INSERT OR IGNORE INTO pengaturan (id, api_key, model_name) VALUES (1, "", "")')
    conn.commit()
    conn.close()

init_db()

# ==========================================
# FUNGSI-FUNGSI CRUD & AI
# ==========================================
def get_settings():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT api_key, model_name FROM pengaturan WHERE id = 1')
    data = c.fetchone()
    conn.close()
    return data['api_key'], data['model_name']

def save_settings(api_key, model_name):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE pengaturan SET api_key = ?, model_name = ? WHERE id = 1', (api_key, model_name))
    conn.commit()
    conn.close()

def generate_soal_ai(mapel, kelas, topik, tipe_soal, api_key, model_name):
    prompt = f"Anda adalah asisten guru ahli. Buatkan soal latihan untuk mata pelajaran {mapel}, jenjang/kelas {kelas}, dengan topik '{topik}'. Tipe soal: {tipe_soal}. Berikan 3 tingkat kesulitan (Mudah, Sedang, Sulit) masing-masing 2 soal, lengkap dengan kunci jawaban dan pembahasan singkat. Format output harus terstruktur dan siap cetak."
    
    # Backend request ke penyedia AI
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Default model pencegahan jika kosong
    if not model_name:
        model_name = "mistralai/mistral-7b-instruct:free"
        
    data = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        return f"Terjadi kesalahan saat menghubungi server AI: {e}"

def simpan_soal(mapel, kelas, topik, konten_soal):
    conn = get_db_connection()
    c = conn.cursor()
    tanggal = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('INSERT INTO bank_soal (mapel, kelas, topik, konten_soal, tanggal) VALUES (?, ?, ?, ?, ?)',
              (mapel, kelas, topik, konten_soal, tanggal))
    conn.commit()
    conn.close()

def get_semua_soal():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM bank_soal ORDER BY id DESC')
    data = c.fetchall()
    conn.close()
    return data

def update_soal(id_soal, topik, konten_soal):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE bank_soal SET topik = ?, konten_soal = ? WHERE id = ?', (topik, konten_soal, id_soal))
    conn.commit()
    conn.close()

def hapus_soal(id_soal):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM bank_soal WHERE id = ?', (id_soal,))
    conn.commit()
    conn.close()


# ==========================================
# ANTARMUKA PENGGUNA (UI)
# ==========================================
st.sidebar.title("📚 GuruGenius")
menu = st.sidebar.radio("Navigasi", ["Generator Soal", "Bank Soal", "Pengaturan", "Bantuan"])

st.sidebar.markdown("---")
st.sidebar.markdown("**Dibuat oleh pawandigital (Wa : 089696380422)**")

api_key, model_name = get_settings()

if menu == "Generator Soal":
    st.header("⚡ Generator Soal Berjenjang")
    
    if not api_key:
        st.warning("API Key belum diatur. Silakan masuk ke menu 'Pengaturan' terlebih dahulu.")
    
    with st.form("form_generator"):
        col1, col2 = st.columns(2)
        with col1:
            mapel = st.text_input("Mata Pelajaran (Cth: Matematika, IPA)")
            kelas = st.text_input("Jenjang & Kelas (Cth: SD Kelas 5)")
        with col2:
            topik = st.text_input("Topik/Materi Spesifik (Cth: Pecahan)")
            tipe_soal = st.selectbox("Tipe Soal", ["Pilihan Ganda", "Uraian", "Campuran"])
            
        submit = st.form_submit_button("Mulai Generate Soal 🚀")
        
    if submit:
        if not api_key:
            st.error("Gagal! Masukkan API Key di menu pengaturan.")
        elif not mapel or not kelas or not topik:
            st.error("Harap isi mata pelajaran, kelas, dan topik materi.")
        else:
            with st.spinner("AI sedang merakit soal untuk Anda..."):
                hasil_ai = generate_soal_ai(mapel, kelas, topik, tipe_soal, api_key, model_name)
                st.session_state['hasil_sementara'] = hasil_ai
                st.session_state['data_sementara'] = {"mapel": mapel, "kelas": kelas, "topik": topik}
                
    if 'hasil_sementara' in st.session_state:
        st.subheader("Hasil Generate:")
        hasil_teks = st.text_area("Anda bisa mengedit hasil ini sebelum disimpan", st.session_state['hasil_sementara'], height=400)
        
        if st.button("💾 Simpan ke Bank Soal"):
            data_meta = st.session_state['data_sementara']
            simpan_soal(data_meta['mapel'], data_meta['kelas'], data_meta['topik'], hasil_teks)
            st.success("Soal berhasil disimpan ke Bank Soal!")
            del st.session_state['hasil_sementara']
            del st.session_state['data_sementara']

elif menu == "Bank Soal":
    st.header("🗂️ Bank Soal & Arsip")
    semua_soal = get_semua_soal()
    
    if not semua_soal:
        st.info("Belum ada soal yang tersimpan di Bank Soal.")
    else:
        # Menampilkan daftar soal
        for soal in semua_soal:
            with st.expander(f"{soal['mapel']} - {soal['kelas']} | Topik: {soal['topik']} ({soal['tanggal']})"):
                # Form Update
                with st.form(f"form_update_{soal['id']}"):
                    edit_topik = st.text_input("Edit Topik", soal['topik'])
                    edit_konten = st.text_area("Isi Soal & Kunci Jawaban", soal['konten_soal'], height=300)
                    
                    col_btn1, col_btn2 = st.columns([1, 1])
                    with col_btn1:
                        btn_update = st.form_submit_button("📝 Simpan Perubahan")
                    with col_btn2:
                        btn_hapus = st.form_submit_button("🗑️ Hapus Soal")
                        
                    if btn_update:
                        update_soal(soal['id'], edit_topik, edit_konten)
                        st.success("Data berhasil diperbarui! Silakan muat ulang halaman.")
                    if btn_hapus:
                        hapus_soal(soal['id'])
                        st.success("Data berhasil dihapus! Silakan muat ulang halaman.")

elif menu == "Pengaturan":
    st.header("⚙️ Pengaturan Sistem AI")
    st.info("Ingin mengaktifkan fitur AI canggih ini? Silakan hubungi Admin via WA untuk mendapatkan API Key khusus.")
    
    with st.form("form_pengaturan"):
        input_api = st.text_input("API Key", value=api_key, type="password")
        input_model = st.text_input("Model (Biarkan kosong untuk default)", value=model_name)
        
        simpan_set = st.form_submit_button("Simpan Pengaturan")
        if simpan_set:
            save_settings(input_api, input_model)
            st.success("Pengaturan berhasil disimpan!")

elif menu == "Bantuan":
    st.header("💡 Pusat Bantuan")
    st.markdown("""
    **Panduan Penggunaan GuruGenius:**
    1. **Pengaturan:** Sebelum memulai, pastikan Anda telah memasukkan API Key di menu 'Pengaturan'. Hubungi admin melalui WhatsApp untuk mendapatkannya.
    2. **Generate Soal:** Masuk ke menu 'Generator Soal'. Isi formulir mata pelajaran, kelas, dan topik dengan spesifik. Klik 'Mulai Generate' dan tunggu AI bekerja.
    3. **Menyimpan Soal:** Setelah naskah soal muncul, Anda bisa membacanya atau mengeditnya secara langsung di kotak teks. Jika sudah pas, klik 'Simpan ke Bank Soal'.
    4. **Bank Soal:** Semua soal yang Anda simpan dapat dilihat di sini. Anda bebas mengedit kembali materi (Update) atau menghapus soal (Delete) jika dirasa tidak relevan.
    """)