import streamlit as st
import sqlite3
import requests
import pandas as pd
from datetime import datetime

# ==========================================
# 1. KONFIGURASI HALAMAN & CSS INJECTION
# ==========================================
st.set_page_config(page_title="GuruMerdeka AI", page_icon="🎓", layout="wide")

# CSS untuk menyembunyikan elemen bawaan Streamlit dan mempercantik UI
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stTextArea textarea {font-size: 14px;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. FUNGSI DATABASE (SQLite3)
# ==========================================
DB_NAME = "guru_merdeka.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS modul_ajar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            judul_materi TEXT,
            mata_pelajaran TEXT,
            fase TEXT,
            kelas TEXT,
            capaian_pembelajaran TEXT,
            hasil_atp TEXT,
            hasil_modul TEXT,
            hasil_rubrik TEXT,
            created_at TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pengaturan (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            api_key TEXT,
            model_name TEXT
        )
    ''')
    cursor.execute('INSERT OR IGNORE INTO pengaturan (id, api_key, model_name) VALUES (1, "", "")')
    conn.commit()
    conn.close()

def get_settings():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT api_key, model_name FROM pengaturan WHERE id = 1')
    row = cursor.fetchone()
    conn.close()
    return {"api_key": row[0], "model_name": row[1]} if row else {"api_key": "", "model_name": ""}

def update_settings(api_key, model_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE pengaturan SET api_key = ?, model_name = ? WHERE id = 1', (api_key, model_name))
    conn.commit()
    conn.close()

def insert_modul(judul, mapel, fase, kelas, cp, atp, modul, rubrik):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO modul_ajar (judul_materi, mata_pelajaran, fase, kelas, capaian_pembelajaran, hasil_atp, hasil_modul, hasil_rubrik, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (judul, mapel, fase, kelas, cp, atp, modul, rubrik, now))
    conn.commit()
    conn.close()

def get_all_modul():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT id, judul_materi, mata_pelajaran, fase, kelas, created_at FROM modul_ajar ORDER BY id DESC", conn)
    conn.close()
    return df

def get_modul_by_id(modul_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM modul_ajar WHERE id = ?', (modul_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def update_modul(modul_id, judul, atp, modul, rubrik):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE modul_ajar 
        SET judul_materi = ?, hasil_atp = ?, hasil_modul = ?, hasil_rubrik = ?
        WHERE id = ?
    ''', (judul, atp, modul, rubrik, modul_id))
    conn.commit()
    conn.close()

def delete_modul(modul_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM modul_ajar WHERE id = ?', (modul_id,))
    conn.commit()
    conn.close()

# ==========================================
# 3. FUNGSI GENERATOR AI (SUDAH DIPERBAIKI)
# ==========================================
def generate_ai_content(api_key, model_name, mapel, fase, kelas, judul, cp):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    target_model = model_name if model_name.strip() != "" else "meta-llama/llama-3-8b-instruct:free"
    
    prompt = f"""
Anda adalah Ahli Kurikulum Merdeka. Tugas Anda adalah memecah Capaian Pembelajaran (CP) berikut menjadi administrasi ajar yang siap pakai.
Mata Pelajaran: {mapel}
Fase: {fase}
Kelas: {kelas}
Topik/Judul: {judul}
Teks CP: {cp}

PENTING: Berikan output dalam 3 bagian secara berurutan. JANGAN menuliskan kalimat pengantar/penutup apapun.
Pemisah ANTARA bagian wajib menggunakan kata kunci ini persis: ===BATAS===

Format Output yang WAJIB Anda ikuti:
[Tuliskan Isi Alur Tujuan Pembelajaran (ATP) di sini]
===BATAS===
[Tuliskan Isi Modul Ajar di sini]
===BATAS===
[Tuliskan Isi Rubrik Asesmen di sini]
"""
    
    payload = {
        "model": target_model,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            result_text = response.json()['choices'][0]['message']['content']
            
            # PERBAIKAN: Memecah teks dan langsung membuang string yang kosong (empty strings)
            # Ini mencegah ATP menjadi kosong jika AI memulai jawaban dengan ===BATAS===
            parts = [p.strip() for p in result_text.split("===BATAS===") if p.strip()]
            
            if len(parts) >= 3:
                return parts[0], parts[1], parts[2]
            elif len(parts) == 2:
                return parts[0], parts[1], "(Rubrik asesmen tidak ter-generate sempurna. Silakan periksa tab sebelumnya)"
            elif len(parts) == 1:
                return parts[0], "(Modul ajar tidak ter-generate sempurna)", "(Rubrik asesmen tidak ter-generate sempurna)"
            else:
                return result_text, "Silakan ekstrak manual dari tab ATP", "Silakan ekstrak manual dari tab ATP"
        else:
            return f"Error API: {response.text}", "", ""
    except Exception as e:
        return f"Error Koneksi: {str(e)}", "", ""

# ==========================================
# 4. ANTARMUKA APLIKASI (UI)
# ==========================================
def main():
    init_db()
    
    st.sidebar.title("🎓 GuruMerdeka AI")
    st.sidebar.markdown("Asisten Administrasi Mengajar")
    
    menu = st.sidebar.radio("Navigasi Menu", ["📝 Buat Modul Baru", "📚 Arsip Modul", "⚙️ Pengaturan", "❓ Bantuan"])
    
    # Footer Pembuat (Wajib)
    st.sidebar.markdown("<br><br><br><br><br><br><br><br><br>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Dibuat oleh pawandigital (Wa : 089696380422)**")

    settings = get_settings()

    if menu == "📝 Buat Modul Baru":
        st.header("📝 Buat Modul Ajar Baru (AI Generator)")
        st.write("Masukkan detail mata pelajaran dan Capaian Pembelajaran (CP) untuk di-generate otomatis.")
        
        with st.form("form_create"):
            col1, col2 = st.columns(2)
            with col1:
                mapel = st.text_input("Mata Pelajaran (Contoh: Matematika)")
                fase = st.selectbox("Fase", ["A", "B", "C", "D", "E", "F"])
            with col2:
                kelas = st.text_input("Kelas (Contoh: 7)")
                judul = st.text_input("Topik/Judul Materi")
                
            cp = st.text_area("Teks Capaian Pembelajaran (CP)", height=150, help="Copy-paste teks CP resmi dari kementerian di sini.")
            
            submit = st.form_submit_button("🚀 Generate dengan AI")
            
        if submit:
            if not settings["api_key"]:
                st.error("⚠️ API Key belum diatur! Silakan isi di menu **Pengaturan** terlebih dahulu.")
            elif not mapel or not judul or not cp:
                st.warning("⚠️ Harap lengkapi Mata Pelajaran, Judul, dan Teks CP.")
            else:
                with st.spinner("AI sedang menganalisis CP dan menyusun dokumen... (Tunggu sekitar 10-30 detik)"):
                    atp, modul, rubrik = generate_ai_content(settings["api_key"], settings["model_name"], mapel, fase, kelas, judul, cp)
                    
                    if "Error" in atp:
                        st.error(atp)
                    else:
                        # CREATE: Simpan ke DB
                        insert_modul(judul, mapel, fase, kelas, cp, atp, modul, rubrik)
                        st.success("✅ Modul berhasil di-generate dan disimpan ke Arsip!")
                        
                        st.markdown("### Preview Hasil")
                        tab1, tab2, tab3 = st.tabs(["Alur Tujuan Pembelajaran (ATP)", "Modul Ajar", "Rubrik Asesmen"])
                        with tab1: st.write(atp)
                        with tab2: st.write(modul)
                        with tab3: st.write(rubrik)

    elif menu == "📚 Arsip Modul":
        st.header("📚 Arsip Administrasi Pembelajaran")
        
        df = get_all_modul()
        if df.empty:
            st.info("Belum ada modul yang dibuat. Silakan ke menu 'Buat Modul Baru'.")
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.subheader("Kelola Dokumen (Read, Update, Delete)")
            
            # Pilihan modul untuk dikelola
            modul_options = {f"ID: {row['id']} - {row['judul_materi']} ({row['mata_pelajaran']})": row['id'] for _, row in df.iterrows()}
            selected_modul_key = st.selectbox("Pilih Modul untuk dilihat/diedit/dihapus:", list(modul_options.keys()))
            selected_id = modul_options[selected_modul_key]
            
            data = get_modul_by_id(selected_id)
            
            st.write(f"**Waktu Dibuat:** {data[9]}")
            
            with st.expander("Klik untuk Edit atau Hapus Dokumen ini", expanded=True):
                with st.form("form_update"):
                    edit_judul = st.text_input("Judul Materi", data[1])
                    st.markdown("**Alur Tujuan Pembelajaran (ATP)**")
                    edit_atp = st.text_area("Edit ATP", data[6], height=200)
                    st.markdown("**Modul Ajar**")
                    edit_modul = st.text_area("Edit Modul", data[7], height=300)
                    st.markdown("**Rubrik Asesmen**")
                    edit_rubrik = st.text_area("Edit Rubrik", data[8], height=200)
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        btn_update = st.form_submit_button("💾 Simpan Perubahan (Update)")
                    with col_btn2:
                        btn_delete = st.form_submit_button("❌ Hapus Modul (Delete)")
                        
                if btn_update:
                    update_modul(selected_id, edit_judul, edit_atp, edit_modul, edit_rubrik)
                    st.success("✅ Dokumen berhasil diperbarui!")
                    st.rerun()
                    
                if btn_delete:
                    delete_modul(selected_id)
                    st.warning("🗑️ Dokumen berhasil dihapus!")
                    st.rerun()

    elif menu == "⚙️ Pengaturan":
        st.header("⚙️ Pengaturan AI")
        st.info("Ingin mengaktifkan fitur AI canggih ini? Silakan hubungi Admin via WA untuk mendapatkan API Key khusus.")
        
        with st.form("form_settings"):
            new_api_key = st.text_input("API Key", value=settings["api_key"], type="password")
            new_model = st.text_input("Model (Biarkan kosong untuk default)", value=settings["model_name"])
            
            save_settings = st.form_submit_button("Simpan Pengaturan")
            if save_settings:
                update_settings(new_api_key, new_model)
                st.success("Pengaturan berhasil disimpan!")
                st.rerun()

    elif menu == "❓ Bantuan":
        st.header("❓ Panduan Penggunaan")
        st.markdown("""
        Selamat datang di **GuruMerdeka AI**! Aplikasi ini dirancang khusus untuk membantu guru mengurangi beban administrasi.
        
        **Langkah-langkah Penggunaan:**
        1. **Aktivasi AI:** Buka menu **⚙️ Pengaturan**. Masukkan API Key yang Anda dapatkan dari Admin. Klik Simpan.
        2. **Buat Modul:** Buka menu **📝 Buat Modul Baru**. 
           - Isi Mata Pelajaran, Fase, Kelas, dan Topik.
           - Copy-Paste teks *Capaian Pembelajaran (CP)* resmi ke dalam kotak yang disediakan.
           - Klik **Generate dengan AI**.
        3. **Tunggu Proses:** Asisten AI akan memecah CP Anda menjadi ATP, Modul Ajar, dan Rubrik dalam beberapa detik.
        4. **Arsip & Revisi:** Semua hasil akan otomatis tersimpan. Buka menu **📚 Arsip Modul** untuk melihat kembali, mengedit manual secara leluasa, atau menghapus modul lama.
        
        *Aplikasi ini berjalan secara lokal. Data tersimpan dengan aman di perangkat Anda.*
        """)

if __name__ == "__main__":
    main()
