import streamlit as st
import sqlite3
import pandas as pd
import random
import time

# ==========================================
# KONFIGURASI HALAMAN & CSS INJECTION
# ==========================================
st.set_page_config(page_title="SmartClass Equalizer", layout="wide")

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ==========================================
# FUNGSI DATABASE (SQLite)
# ==========================================
DB_NAME = "smartclass.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Tabel Kelas
    c.execute('''CREATE TABLE IF NOT EXISTS classes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    class_name TEXT UNIQUE, 
                    description TEXT)''')
    # Tabel Siswa
    c.execute('''CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    class_id INTEGER, 
                    name TEXT, 
                    academic_score REAL, 
                    character_type TEXT, 
                    has_participated INTEGER DEFAULT 0, 
                    FOREIGN KEY(class_id) REFERENCES classes(id))''')
    conn.commit()
    conn.close()

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

# Inisialisasi DB saat pertama kali jalan
init_db()

# ==========================================
# SIDEBAR NAVIGATION & FOOTER
# ==========================================
st.sidebar.title("🎓 SmartClass")
st.sidebar.subheader("Menu Navigasi")
menu = st.sidebar.radio("Pilih Menu:", 
    ["📊 Dashboard & Group", "🎯 Fair Student Picker", "🏢 Kelola Kelas", "👥 Kelola Siswa", "ℹ️ Bantuan"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("<p style='text-align: center; font-weight: bold;'>Dibuat oleh pawandigital<br>(Wa : 089696380422)</p>", unsafe_allow_html=True)

# ==========================================
# HALAMAN: KELOLA KELAS (CRUD)
# ==========================================
if menu == "🏢 Kelola Kelas":
    st.header("🏢 Kelola Data Kelas")
    
    df_classes = fetch_data("SELECT id AS ID, class_name AS 'Nama Kelas', description AS 'Keterangan' FROM classes")
    st.subheader("Daftar Kelas Saat Ini")
    st.dataframe(df_classes, use_container_width=True, hide_index=True)

    col1, col2, col3 = st.columns(3)
    
    # CREATE
    with col1:
        st.markdown("#### ➕ Tambah Kelas")
        with st.form("tambah_kelas"):
            c_name = st.text_input("Nama Kelas")
            c_desc = st.text_area("Keterangan")
            submit_add = st.form_submit_button("Simpan Kelas")
            if submit_add:
                if c_name.strip():
                    try:
                        run_query("INSERT INTO classes (class_name, description) VALUES (?, ?)", (c_name, c_desc))
                        st.success("Kelas berhasil ditambahkan!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal! (Nama kelas mungkin sudah ada). Error: {e}")
                else:
                    st.warning("Nama kelas tidak boleh kosong.")

    # UPDATE
    with col2:
        st.markdown("#### ✏️ Edit Kelas")
        if not df_classes.empty:
            edit_id_raw = st.selectbox("Pilih Kelas (Edit)", df_classes['ID'])
            edit_id = int(edit_id_raw) # Konversi paksa ke integer native
            
            curr_name = str(df_classes.loc[df_classes['ID'] == edit_id, 'Nama Kelas'].values[0])
            curr_desc = str(df_classes.loc[df_classes['ID'] == edit_id, 'Keterangan'].values[0])
            
            with st.form("edit_kelas"):
                new_name = st.text_input("Nama Kelas Baru", curr_name)
                new_desc = st.text_area("Keterangan Baru", curr_desc)
                submit_edit = st.form_submit_button("Update Kelas")
                if submit_edit:
                    try:
                        run_query("UPDATE classes SET class_name=?, description=? WHERE id=?", (new_name, new_desc, edit_id))
                        st.success("Kelas berhasil diupdate!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal Edit: {e}")
        else:
            st.info("Belum ada data.")

    # DELETE
    with col3:
        st.markdown("#### 🗑️ Hapus Kelas")
        if not df_classes.empty:
            del_id_raw = st.selectbox("Pilih Kelas (Hapus)", df_classes['ID'])
            del_id = int(del_id_raw) # Konversi paksa
            with st.form("hapus_kelas"):
                st.warning("Menghapus kelas akan menghapus semua siswa di dalamnya!")
                submit_del = st.form_submit_button("Hapus Permanen")
                if submit_del:
                    try:
                        run_query("DELETE FROM students WHERE class_id=?", (del_id,))
                        run_query("DELETE FROM classes WHERE id=?", (del_id,))
                        st.success("Kelas dihapus!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal Hapus: {e}")

# ==========================================
# HALAMAN: KELOLA SISWA (CRUD)
# ==========================================
elif menu == "👥 Kelola Siswa":
    st.header("👥 Kelola Data Siswa")
    
    df_classes = fetch_data("SELECT * FROM classes")
    if df_classes.empty:
        st.warning("Silakan buat Kelas terlebih dahulu di menu 'Kelola Kelas'.")
    else:
        selected_class_view = st.selectbox("Pilih Kelas:", df_classes['class_name'])
        class_id_view = int(df_classes.loc[df_classes['class_name'] == selected_class_view, 'id'].values[0])
        
        df_students = fetch_data("SELECT id AS ID, name AS Nama, academic_score AS Nilai, character_type AS Karakter, has_participated AS 'Sudah Tampil' FROM students WHERE class_id=?", (class_id_view,))
        st.dataframe(df_students, use_container_width=True, hide_index=True)

        col1, col2 = st.columns(2)
        
        # CREATE
        with col1:
            st.markdown("#### ➕ Tambah Siswa")
            with st.form("tambah_siswa"):
                s_name = st.text_input("Nama Siswa")
                s_score = st.number_input("Nilai Akademik (0-100)", min_value=0.0, max_value=100.0, value=75.0)
                s_char = st.selectbox("Karakter / Peran Sosial", ["Pintar / Leader", "Rajin / Pekerja", "Ramai / Ekstrovert", "Pasif / Introvert"])
                submit_add_s = st.form_submit_button("Tambah Siswa")
                
                if submit_add_s:
                    if s_name.strip():
                        try:
                            run_query("INSERT INTO students (class_id, name, academic_score, character_type) VALUES (?, ?, ?, ?)", 
                                      (class_id_view, s_name, float(s_score), s_char))
                            st.success(f"{s_name} ditambahkan!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal Tambah Siswa: {e}")
                    else:
                        st.warning("Nama siswa tidak boleh kosong!")

        # DELETE
        with col2:
            st.markdown("#### 🗑️ Hapus Siswa")
            if not df_students.empty:
                # Ambil ID saja, handle error mapping nama
                del_s_id_raw = st.selectbox(
                    "Pilih Siswa yang dihapus", 
                    df_students['ID'], 
                    format_func=lambda x: df_students.loc[df_students['ID']==x, 'Nama'].values[0] if not df_students.loc[df_students['ID']==x].empty else x
                )
                del_s_id = int(del_s_id_raw)
                
                with st.form("hapus_siswa"):
                    submit_del_s = st.form_submit_button("Hapus Siswa")
                    if submit_del_s:
                        try:
                            run_query("DELETE FROM students WHERE id=?", (del_s_id,))
                            st.success("Siswa dihapus!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal Hapus Siswa: {e}")

# ==========================================
# HALAMAN: DASHBOARD & GROUP GENERATOR
# ==========================================
elif menu == "📊 Dashboard & Group":
    st.header("📊 Pembagian Kelompok Seimbang (1-Click)")
    
    df_classes = fetch_data("SELECT * FROM classes")
    if df_classes.empty:
        st.warning("Belum ada data kelas.")
    else:
        col_c, col_g = st.columns(2)
        with col_c:
            selected_class = st.selectbox("Pilih Kelas", df_classes['class_name'])
            class_id = int(df_classes.loc[df_classes['class_name'] == selected_class, 'id'].values[0])
        
        df_students = fetch_data("SELECT * FROM students WHERE class_id=?", (class_id,))
        
        with col_g:
            if not df_students.empty:
                num_groups = st.number_input("Jumlah Kelompok", min_value=2, max_value=len(df_students), value=min(4, len(df_students)))
        
        if not df_students.empty:
            st.info(f"Total Siswa di {selected_class}: {len(df_students)} Siswa")
            
            if st.button("🚀 Bagi Kelompok Sekarang", use_container_width=True, type="primary"):
                df_sorted = df_students.sort_values(by='academic_score', ascending=False).reset_index(drop=True)
                groups = [[] for _ in range(int(num_groups))]
                
                for i, row in df_sorted.iterrows():
                    round_num = i // num_groups
                    group_idx = (i % num_groups) if round_num % 2 == 0 else (num_groups - 1 - (i % num_groups))
                    groups[int(group_idx)].append(row)
                
                st.markdown("---")
                st.subheader("🎉 Hasil Pembagian Kelompok")
                cols = st.columns(int(num_groups))
                for i, (col, group) in enumerate(zip(cols, groups)):
                    with col:
                        avg_score = sum([s['academic_score'] for s in group]) / len(group) if group else 0
                        st.markdown(f"### Kelompok {i+1}")
                        st.markdown(f"**Rata-rata Nilai: {avg_score:.2f}**")
                        for s in group:
                            char_type = str(s['character_type'])
                            char_icon = "👑" if "Leader" in char_type else "🔥" if "Rajin" in char_type else "🗣️" if "Ramai" in char_type else "👤"
                            st.markdown(f"- {char_icon} **{s['name']}** ({s['academic_score']})")
                        st.markdown("---")
        else:
            st.warning("Belum ada siswa di kelas ini.")

# ==========================================
# HALAMAN: FAIR STUDENT PICKER
# ==========================================
elif menu == "🎯 Fair Student Picker":
    st.header("🎯 Penunjuk Siswa Acak (Fair Picker)")
    
    df_classes = fetch_data("SELECT * FROM classes")
    if df_classes.empty:
        st.warning("Belum ada data kelas.")
    else:
        selected_class = st.selectbox("Pilih Kelas", df_classes['class_name'])
        class_id = int(df_classes.loc[df_classes['class_name'] == selected_class, 'id'].values[0])
        
        df_all_students = fetch_data("SELECT * FROM students WHERE class_id=?", (class_id,))
        if df_all_students.empty:
            st.warning("Tidak ada siswa di kelas ini.")
        else:
            sudah_tampil = len(df_all_students[df_all_students['has_participated'] == 1])
            total_siswa = len(df_all_students)
            
            st.progress(sudah_tampil / total_siswa, text=f"Progres Giliran Kelas: {sudah_tampil} dari {total_siswa} siswa sudah terpanggil.")
            df_available = df_all_students[df_all_students['has_participated'] == 0]
            
            col1, col2 = st.columns([3, 1])
            with col1:
                if df_available.empty:
                    st.success("✨ Semua siswa di kelas ini sudah mendapat giliran!")
                else:
                    if st.button("🎲 Panggil Siswa Berikutnya", use_container_width=True, type="primary"):
                        with st.spinner("Mengacak nama siswa..."):
                            time.sleep(1) 
                            chosen = random.choice(df_available.to_dict('records'))
                            chosen_id = int(chosen['id'])
                            
                            try:
                                run_query("UPDATE students SET has_participated=1 WHERE id=?", (chosen_id,))
                                st.balloons()
                                st.markdown(f"""
                                <div style="background-color:#d4edda; padding:20px; border-radius:10px; text-align:center; border: 2px solid #28a745;">
                                    <h2 style="color:#155724; margin:0;">🎉 {chosen['name']} 🎉</h2>
                                    <p style="color:#155724; font-size:18px; margin:0;">Karakter: <b>{chosen['character_type']}</b> | Nilai: <b>{chosen['academic_score']}</b></p>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                if st.button("🔄 Lanjut Panggil Lagi", use_container_width=True):
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Gagal mengupdate memori giliran: {e}")
            
            with col2:
                if st.button("♻️ Reset Giliran", use_container_width=True):
                    try:
                        run_query("UPDATE students SET has_participated=0 WHERE class_id=?", (class_id,))
                        st.success("Giliran direset!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal mereset: {e}")

# ==========================================
# HALAMAN: BANTUAN
# ==========================================
elif menu == "ℹ️ Bantuan":
    st.header("ℹ️ Panduan Penggunaan Aplikasi")
    st.markdown("""
    Selamat datang di **SmartClass Equalizer**! Berikut cara menggunakannya:
    
    1. **🏢 Kelola Kelas**: Mulai dengan membuat nama kelas Anda (misal: "Kelas 10-IPA 1"). Anda bisa mengedit dan menghapus kelas di sini.
    2. **👥 Kelola Siswa**: Masukkan data siswa (Nama, Nilai Akademik, dan Karakter Sosial) ke dalam kelas yang sudah dibuat.
    3. **📊 Dashboard & Group**: Pilih kelas dan tentukan jumlah kelompok yang diinginkan. Sistem akan membagi kelompok menggunakan metode *Snake Draft* berdasarkan nilai.
    4. **🎯 Fair Student Picker**: Gunakan saat sesi tanya-jawab. Klik "Panggil Siswa Berikutnya". Siswa yang sudah terpanggil tidak akan dipanggil lagi. Klik "Reset Giliran" jika ingin mengulang dari awal.
    """)
