import sqlite3
import os
from config import DATABASE as DATABASE

# Simulasi isi config DATABASE jika file eksternal tidak ada
#DATABASE = "portfolio_test.db"

skills = [ (_,) for _ in (['Python', 'SQL', 'API', 'Discord'])]
statuses = [ (_,) for _ in (['Pembuatan Prototipe', 'Dalam Pengembangan', 'Selesai, siap digunakan', 'Diperbarui', 'Selesai, tapi tidak sedang dilanjutkan'])]

class DB_Manager:
    def __init__(self, database):
        self.database = database
        
    def create_tables(self):
        # Tambahkan DROP TABLE IF EXISTS agar setiap kali diuji, database bersih kembali
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('DROP TABLE IF EXISTS project_skills')
            conn.execute('DROP TABLE IF EXISTS projects')
            conn.execute('DROP TABLE IF EXISTS skills')
            conn.execute('DROP TABLE IF EXISTS status')
            
            # Membuat tabel dengan urutan terbalik dari relasinya (status dahulu baru projects)
            conn.execute('''CREATE TABLE status (
                            status_id INTEGER PRIMARY KEY,
                            status_name TEXT UNIQUE
                        )''')
            conn.execute('''CREATE TABLE projects (
                            project_id INTEGER PRIMARY KEY,
                            user_id INTEGER,
                            project_name TEXT NOT NULL,
                            description TEXT,
                            url TEXT,
                            status_id INTEGER,
                            FOREIGN KEY(status_id) REFERENCES status(status_id)
                        )''') 
            conn.execute('''CREATE TABLE skills (
                            skill_id INTEGER PRIMARY KEY,
                            skill_name TEXT UNIQUE
                        )''')
            conn.execute('''CREATE TABLE project_skills (
                            project_id INTEGER,
                            skill_id INTEGER,
                            PRIMARY KEY(project_id, skill_id),
                            FOREIGN KEY(project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
                            FOREIGN KEY(skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE
                        )''')
            conn.commit()

    def __executemany(self, sql, data):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.executemany(sql, data)
            conn.commit()
    
    def __select_data(self, sql, data = tuple()):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute(sql, data)
            return cur.fetchall()
        
    def default_insert(self):
        sql = 'INSERT OR IGNORE INTO skills (skill_name) values(?)'
        data = skills
        self.__executemany(sql, data)
        sql = 'INSERT OR IGNORE INTO status (status_name) values(?)'
        data = statuses
        self.__executemany(sql, data)

    def insert_project(self, data):
        # Kueri SQL yang benar untuk memasukkan proyek baru
        sql = "INSERT INTO projects (user_id, project_name, description, url, status_id) VALUES (?, ?, ?, ?, ?)" 
        self.__executemany(sql, data)

    def insert_skill(self, user_id, project_name, skill):
        sql = 'SELECT project_id FROM projects WHERE project_name = ? AND user_id = ?'
        project_id = self.__select_data(sql, (project_name, user_id))[0][0]
        skill_id = self.__select_data('SELECT skill_id FROM skills WHERE skill_name = ?', (skill,))[0][0]
        data = [(project_id, skill_id)]
        sql = 'INSERT OR IGNORE INTO project_skills VALUES(?, ?)'
        self.__executemany(sql, data)

    def get_statuses(self):
        # Kueri SQL yang benar untuk mengambil semua data status
        sql = "SELECT * FROM status" 
        return self.__select_data(sql)
        
    def get_status_id(self, status_name):
        sql = 'SELECT status_id FROM status WHERE status_name = ?'
        res = self.__select_data(sql, (status_name,))
        if res: return res[0][0]
        else: return None

    def get_projects(self, user_id):
        # Kueri SQL yang benar untuk mengambil semua proyek milik user tertentu
        sql = "SELECT * FROM projects WHERE user_id = ?" 
        return self.__select_data(sql, data = (user_id,))
        
    def get_project_id(self, project_name, user_id):
        return self.__select_data(sql='SELECT project_id FROM projects WHERE project_name = ? AND user_id = ?  ', data = (project_name, user_id,))[0][0]
        
    def get_skills(self):
        return self.__select_data(sql='SELECT * FROM skills')
    
    def get_project_skills(self, project_name):
        res = self.__select_data(sql='''SELECT skill_name FROM projects 
JOIN project_skills ON projects.project_id = project_skills.project_id 
JOIN skills ON skills.skill_id = project_skills.skill_id 
WHERE project_name = ?''', data = (project_name,) )
        return ', '.join([x[0] for x in res])
    
    def get_project_info(self, user_id, project_name):
        # Memperbaiki kelebihan tanda kurung tutup pada JOIN status ON ...
        sql = """
SELECT project_name, description, url, status_name FROM projects 
JOIN status ON status.status_id = projects.status_id
WHERE project_name=? AND user_id=?
"""
        return self.__select_data(sql=sql, data = (project_name, user_id))

    def update_projects(self, param, data):
        # Kueri SQL dinamis berdasarkan kolom (param) yang ingin diubah
        sql = f"UPDATE projects SET {param} = ? WHERE project_id = ?" 
        self.__executemany(sql, [data]) 

    def delete_project(self, user_id, project_id):
        # Kueri SQL untuk menghapus proyek berdasarkan user_id dan project_id
        sql = "DELETE FROM projects WHERE user_id = ? AND project_id = ?" 
        self.__executemany(sql, [(user_id, project_id)])
    
    def delete_skill(self, project_id, skill_id):
        # Kueri SQL untuk menghapus relasi skill pada proyek tertentu
        sql = "DELETE FROM project_skills WHERE project_id = ? AND skill_id = ?" 
        # Menyelaraskan urutan tuple data dengan kueri (project_id, skill_id)
        self.__executemany(sql, [(project_id, skill_id)])


# --- BAGIAN PENGUJIAN METODE ---
if __name__ == '__main__':
    manager = DB_Manager(DATABASE)
    
    print("1. Menyiapkan database dan tabel...")
    manager.create_tables()
    manager.default_insert()
    
    print("\n2. Menguji Get Statuses:")
    print(manager.get_statuses())
    
    # Ambil ID status "Dalam Pengembangan" untuk testing data baru
    status_id = manager.get_status_id('Dalam Pengembangan')
    user_test_id = 99
    
    print("\n3. Menguji Insert Project...")
    # Format data: (user_id, project_name, description, url, status_id)
    project_data = [(user_test_id, "Bot Discord Keren", "Bot untuk mengelola server", "https://github.com", status_id)]
    manager.insert_project(project_data)
    
    # Ambil ID Proyek yang baru dibuat
    pid = manager.get_project_id("Bot Discord Keren", user_test_id)
    print(f"-> Proyek berhasil dibuat dengan ID: {pid}")
    
    print("\n4. Menguji Insert Skill ke dalam Proyek...")
    manager.insert_skill(user_test_id, "Bot Discord Keren", "Python")
    manager.insert_skill(user_test_id, "Bot Discord Keren", "Discord")
    
    print("\n5. Menguji Get Project Skills:")
    print(f"Skills: {manager.get_project_skills('Bot Discord Keren')}")
    
    print("\n6. Menguji Get Project Info Lengkap:")
    print(manager.get_project_info(user_test_id, "Bot Discord Keren"))
    
    print("\n7. Menguji Update Deskripsi Proyek...")
    # Mengubah deskripsi proyek menggunakan update_projects
    # data format: (nilai_baru, project_id)
    manager.update_projects("description", ("Bot Discord canggih berbasis AI", pid))
    print(manager.get_project_info(user_test_id, "Bot Discord Keren"))
    
    print("\n8. Menguji Hapus Hubungan Skill ('Discord' id=4)...")
    manager.delete_skill(pid, 4)
    print(f"Skills tersisa: {manager.get_project_skills('Bot Discord Keren')}")
    
    print("\n9. Menguji Hapus Total Proyek...")
    manager.delete_project(user_test_id, pid)
    print(f"Daftar proyek user {user_test_id} sekarang: {manager.get_projects(user_test_id)}")
