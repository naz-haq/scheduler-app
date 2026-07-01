import os
import sqlite3
import sys

DB_NAME = "scheduler.db"


def db_path():
    base = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) \
        else os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, DB_NAME)


def get_db():
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS angkatan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tahun TEXT NOT NULL,
    jml_kelas INTEGER NOT NULL DEFAULT 12,
    jml_grup INTEGER NOT NULL DEFAULT 6
);
CREATE TABLE IF NOT EXISTS ruang (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kode TEXT NOT NULL,
    nama TEXT,
    kapasitas INTEGER NOT NULL DEFAULT 0,
    tipe TEXT NOT NULL DEFAULT 'kuliah'  -- kuliah / lab
);
CREATE TABLE IF NOT EXISTS dosen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama TEXT NOT NULL,
    nidn TEXT,
    tidak_tersedia TEXT  -- catatan hari/jam tak bisa
);
CREATE TABLE IF NOT EXISTS matakuliah (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kode TEXT NOT NULL,
    nama TEXT NOT NULL,
    sks INTEGER NOT NULL DEFAULT 2,
    jenis TEXT NOT NULL DEFAULT 'wajib',  -- wajib / pilihan / praktikum
    angkatan_id INTEGER,
    dosen_id INTEGER,
    lab TEXT,  -- nama lab tujuan (hanya untuk praktikum)
    FOREIGN KEY (angkatan_id) REFERENCES angkatan(id) ON DELETE SET NULL,
    FOREIGN KEY (dosen_id) REFERENCES dosen(id) ON DELETE SET NULL
);
"""


def init_db():
    conn = get_db()
    conn.executescript(SCHEMA)
    # Migrasi: tambah kolom 'lab' pada DB lama yang belum punya.
    cols = [r["name"] for r in conn.execute("PRAGMA table_info(matakuliah)")]
    if "lab" not in cols:
        conn.execute("ALTER TABLE matakuliah ADD COLUMN lab TEXT")
    conn.commit()
    conn.close()
