import streamlit as st
import sqlite3
import requests
import json
from datetime import datetime

# ==========================================
# 1. KONFIGURASI HALAMAN & CSS INJECTION
# ==========================================
st.set_page_config(page_title="TIPS AI Instant Converter", page_icon="🚀", layout="wide")

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# ==========================================
# 2. KONFIGURASI DATABASE SQLITE
# ==========================================
DB_NAME = "history.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tips_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            user_problem TEXT,
            tips_breakdown TEXT,
            ai_output TEXT,
            category TEXT,
            model_used TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_history(problem, tips, output, category, model):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''INSERT INTO tips_history (timestamp, user_problem, tips_breakdown, ai_output, category, model_used)
                 VALUES (?, ?, ?, ?, ?, ?)''', (timestamp, problem, tips, output, category, model))
    conn.commit()
    conn.close()

def get_all_history():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT * FROM tips_history ORDER BY id DESC')
    data = c.fetchall()
    conn.close()
    return data

def update_history(record_id, new_output, new_category):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('UPDATE tips_history SET ai_output=?, category=? WHERE id=?', (new_output, new_category, record_id))
    conn.commit()
    conn.close()

def delete_history(record_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM tips_history WHERE id=?', (record_id,))
    conn.commit()
    conn.close()

def delete_all_history():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM tips_history')
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 3. FUNGSI API OPENROUTER & PARSER
# ==========================================
def call_openrouter(api_key, model, user_input):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    system_prompt = """Anda adalah 'TIPS AI Instant Converter'. Pengguna akan memberikan 1 kalimat masalah yang mereka alami. 
    Tugas Anda:
    1. Buat kategori masalah (maksimal 2 kata, misal: Bisnis, Keuangan, Mental).
    2. Ubah masalah itu menjadi kerangka TIPS (Task, Instruction, Persona, Step-by-step).
    3. Bertindaklah sebagai Persona tersebut dan berikan solusi eksekusi langkah demi langkah yang matang.
    
    Anda WAJIB memberikan balasan dengan format persis seperti di bawah ini (gunakan pemisah ---):
    ---KATEGORI---
    [Tulis kategori di sini]
    ---TIPS---
    [Tulis pemecahan Task, Instruction, Persona, dan Step-by-step di sini]
    ---SOLUSI---
    [Tulis hasil eksekusi/solusi final di sini]"""

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def parse_ai_response(text):
    category, tips, solusi = "Umum", "Gagal memparsing struktur TIPS.", text
    try:
        if "---KATEGORI---" in text and "---TIPS---" in text and "---SOLUSI---" in text:
            parts = text.split("---KATEGORI---")[1]
            cat_part = parts.split("---TIPS---")[0].strip()
            tips_part = parts.split("---TIPS---")[1].split("---SOLUSI---")[0].strip()
            sol_part = text.split("---SOLUSI---")[1].strip()
            return cat_part, tips_part, sol_part
    except Exception:
        pass
    return category, tips, solusi

# ==========================================
# 4. SIDEBAR & NAVIGASI UTAMA
# ==========================================
st.sidebar.title("⚙️ Pengaturan AI")
api_key = st.sidebar.text_input("OpenRouter API Key", type="password", help="Masukkan API Key dari Admin")

model_options = [
    "openai/gpt-4o-mini",
    "anthropic/claude-3-haiku",
    "google/gemini-flash-1.5",
    "meta-llama/llama-3.1-8b-instruct"
]
selected_model = st.sidebar.selectbox("Pilih Model AI", model_options)
custom_model = st.sidebar.text_input("Atau ketik model manual (opsional)")
final_model = custom_model if custom_model else selected_model

st.sidebar.markdown("---")
menu = st.sidebar.radio("Navigasi", ["🚀 AI Converter", "📜 Riwayat Solusi (CRUD)", "ℹ️ Bantuan / Help"])

st.sidebar.markdown("---")
st.sidebar.markdown("**Dibuat oleh pawandigital (Wa : 089696380422)**")

# ==========================================
# 5. HALAMAN UTAMA (ROUTING)
# ==========================================
if menu == "🚀 AI Converter":
    st.title("🚀 TIPS AI Instant Converter & Executor")
    st.write("Ketik 1 kalimat masalah Anda. Sistem akan memecahnya menggunakan metode **TIPS** dan AI akan langsung mengeksekusi solusinya.")
    
    user_problem = st.text_input("Apa masalah yang ingin Anda selesaikan hari ini?", placeholder="Contoh: Saya mau jualan kue sus tapi sepi...")
    
    if st.button("Generate Solusi Instan", type="primary"):
        if not api_key:
            st.error("⚠️ Silakan masukkan API Key di menu Sidebar terlebih dahulu.")
        elif not user_problem:
            st.warning("⚠️ Masukkan masalah Anda terlebih dahulu.")
        else:
            with st.spinner("Memproses keajaiban AI..."):
                api_response = call_openrouter(api_key, final_model, user_problem)
                
                if "error" in api_response:
                    st.error(f"Terjadi kesalahan saat menghubungi API: {api_response['error']}")
                elif "choices" in api_response:
                    raw_text = api_response["choices"][0]["message"]["content"]
                    cat, tips_str, solution_str = parse_ai_response(raw_text)
                    
                    # Simpan ke Database (Create)
                    add_history(user_problem, tips_str, solution_str, cat, final_model)
                    
                    st.success("✅ Solusi berhasil digenerate dan disimpan ke riwayat!")
                    
                    tab1, tab2 = st.tabs(["💡 Solusi Eksekusi (Siap Pakai)", "🧠 Struktur TIPS (Di Balik Layar)"])
                    with tab1:
                        st.markdown(f"### Kategori: {cat}")
                        st.markdown(solution_str)
                    with tab2:
                        st.info("Berikut adalah bagaimana sistem merangkai prompt profesional untuk masalah Anda:")
                        st.markdown(tips_str)
                else:
                    st.error("Respons API tidak valid. Periksa API Key atau kuota Anda.")

elif menu == "📜 Riwayat Solusi (CRUD)":
    st.title("📜 Riwayat Interaksi AI")
    st.write("Kelola (Baca, Edit, Hapus) semua solusi yang pernah Anda hasilkan.")
    
    records = get_all_history()
    
    if not records:
        st.info("Belum ada riwayat. Silakan gunakan menu AI Converter terlebih dahulu.")
    else:
        if st.button("🗑️ Kosongkan Semua Riwayat"):
            delete_all_history()
            st.rerun()
            
        st.markdown("---")
        for row in records:
            rec_id, ts, prob, tips, out, cat, mod = row
            with st.expander(f"[{cat}] {prob} - {ts}"):
                st.write(f"**Model digunakan:** `{mod}`")
                st.write("**TIPS Breakdown:**")
                st.info(tips)
                
                # Form Update
                with st.form(f"form_update_{rec_id}"):
                    st.write("**Edit Hasil Solusi AI:**")
                    new_cat = st.text_input("Kategori", value=cat, key=f"cat_{rec_id}")
                    new_out = st.text_area("Solusi Eksekusi", value=out, height=200, key=f"out_{rec_id}")
                    
                    col1, col2 = st.columns([1, 5])
                    with col1:
                        if st.form_submit_button("💾 Update"):
                            update_history(rec_id, new_out, new_cat)
                            st.success("Data berhasil diupdate!")
                            st.rerun()
                
                # Tombol Delete
                if st.button("🗑️ Hapus Baris Ini", key=f"del_{rec_id}"):
                    delete_history(rec_id)
                    st.rerun()

elif menu == "ℹ️ Bantuan / Help":
    st.title("ℹ️ Pusat Bantuan")
    
    st.markdown("""
    ### 📖 Cara Menggunakan Aplikasi
    1. **Dapatkan API Key:** Hubungi Admin untuk mendapatkan kunci API.
    2. **Masukkan Kunci:** Paste API Key tersebut di menu Sidebar sebelah kiri pada kolom **OpenRouter API Key**. Pilih juga model AI yang ingin digunakan.
    3. **Generate Solusi:** Masuk ke menu **🚀 AI Converter**, ketik masalah Anda dalam 1 kalimat singkat, lalu klik tombol **Generate Solusi Instan**.
    4. **Kelola Riwayat:** Masuk ke menu **📜 Riwayat Solusi (CRUD)** untuk membaca ulang, mengedit, atau menghapus hasil AI yang pernah Anda buat.

    ---
    ### 🔑 Cara Mendapatkan API Key
    Untuk mendapatkan API Key yang valid agar bisa menggunakan aplikasi ini, silakan hubungi Admin melalui WhatsApp:
    
    📱 **[Chat Admin via WhatsApp (089696380422)](https://wa.me/6289696380422)**
    """)
