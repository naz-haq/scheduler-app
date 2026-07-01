import re
from collections import defaultdict

HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat"]
SESI = ["Sesi 1", "Sesi 2", "Sesi 3", "Sesi 4"]

SESI_PAGI = [0, 1]    # kuliah pagi (praktikum siang)
SESI_SIANG = [2, 3]   # kuliah siang (praktikum pagi)


class ScheduleError(Exception):
    """Kesalahan yang bisa ditampilkan ke pengguna saat jadwal tidak muat."""


def get_slot_index(hari_idx, sesi_idx):
    return hari_idx * len(SESI) + sesi_idx


def generate_schedule(
    num_rooms,
    distribusi_semester,   # MKW per angkatan, contoh: [8, 7, 7]
    num_mk_pilihan,        # jumlah MK pilihan
    kelas_per_mkw,         # jumlah kelas tiap MK wajib (mis. 12)
    kelas_per_mkp,         # jumlah kelas tiap MK pilihan (mis. 2)
    angkatan_pilihan,      # index angkatan penerima MKP (0-based), mis. [1, 2]
):
    if num_rooms < 1:
        raise ScheduleError("Jumlah ruangan minimal 1.")
    if kelas_per_mkw < 1:
        raise ScheduleError("Kelas per MK wajib minimal 1.")

    rooms = [f"R{i}" for i in range(1, num_rooms + 1)]

    # Jadwal kosong: 5 hari x 4 sesi, tiap sel = ruang
    schedule = []
    for hari in HARI:
        for sesi in SESI:
            row = {"Hari": hari, "Sesi": sesi}
            for r in rooms:
                row[r] = "-"
            schedule.append(row)

    kelas_terpakai = [set() for _ in schedule]  # kelas yg sudah ada kuliah di slot

    # Tiap kelas dikunci ke 1 blok: pagi-only atau siang-only (sisanya praktikum)
    blok_kelas = {}

    def blok(kelas):
        return SESI_PAGI if blok_kelas.get(kelas, 0) == 0 else SESI_SIANG

    def tempatkan(mk, kelas):
        """Tempatkan satu MK untuk satu kelas; cegah bentrok kelas, sebar beban antar slot."""
        kandidat = []
        for hari_idx in range(len(HARI)):
            for sesi_idx in blok(kelas):
                slot_idx = get_slot_index(hari_idx, sesi_idx)
                if kelas in kelas_terpakai[slot_idx]:
                    continue
                row = schedule[slot_idx]
                kosong = sum(1 for room in rooms if row[room] == "-")
                if kosong:
                    kandidat.append((kosong, slot_idx))
        if not kandidat:
            return False
        # pilih slot paling lengang agar beban menyebar (15 ruang cukup)
        _, slot_idx = max(kandidat)
        row = schedule[slot_idx]
        for room in rooms:
            if row[room] == "-":
                row[room] = f"{mk} ({kelas})"
                kelas_terpakai[slot_idx].add(kelas)
                return True
        return False

    # Bentuk daftar kelas per angkatan + bagi blok pagi/siang seimbang
    angkatan_kelas = []
    for a_idx in range(len(distribusi_semester)):
        kelas_list = []
        for k in range(1, kelas_per_mkw + 1):
            nama = f"A{a_idx + 1}K{k}"
            pair = (k - 1) // 2  # pasangan kelas (K1-K2, K3-K4, ...) berbagi blok
            blok_kelas[nama] = 0 if pair % 2 == 0 else 1  # 0=pagi, 1=siang
            kelas_list.append(nama)
        angkatan_kelas.append(kelas_list)

    # MK wajib: tiap angkatan punya MKW sendiri untuk seluruh kelasnya
    mk_counter = 1
    for a_idx, jumlah in enumerate(distribusi_semester):
        for _ in range(jumlah):
            mk = f"W{mk_counter}"
            mk_counter += 1
            for kelas in angkatan_kelas[a_idx]:
                if not tempatkan(mk, kelas):
                    raise ScheduleError(
                        f"Gagal menjadwalkan {mk} untuk {kelas}. "
                        "Tambah ruangan, kurangi MK, atau perbanyak kelas/sesi."
                    )

    # MK pilihan: kelas_per_mkp kelas dari angkatan terpilih, tanpa bentrok
    pool = []
    for a_idx in angkatan_pilihan:
        if 0 <= a_idx < len(angkatan_kelas):
            pool.extend(angkatan_kelas[a_idx])
    if not pool:
        pool = [k for kl in angkatan_kelas for k in kl]

    for i in range(1, num_mk_pilihan + 1):
        mk = f"P{i}"
        target = [pool[(j + i) % len(pool)] for j in range(kelas_per_mkp)]
        for kelas in target:
            if not tempatkan(mk, kelas):
                raise ScheduleError(
                    f"Gagal menjadwalkan {mk} untuk {kelas}. "
                    "Kurangi MK pilihan atau tambah ruangan/sesi."
                )

    return schedule


HARI_PRAK = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"]
BLOK_PRAK = ["Pagi", "Siang"]  # praktikum hanya 2 blok, bukan 4 sesi


def generate_praktikum(
    lab_kapasitas,         # ruang tiap lab, contoh: [3, 2, 2, 1] -> 4 lab
    distribusi_praktikum,  # MATRIKS baris=angkatan, kolom=lab. Mis. [[2,1,1,0],[1,1,1,0]]
    kelas_per_mkw,         # jumlah kelas kuliah/angkatan (mis. 12), digabung 2->1
):
    """Praktikum 2 blok (pagi/siang) di blok lawan kuliah, tiap MK terikat ke lab tertentu.

    distribusi_praktikum berupa matriks: tiap baris satu angkatan, tiap kolom satu
    lab (urut sesuai lab_kapasitas). Nilai = jumlah MK praktikum angkatan itu di lab
    tersebut. Nol berarti angkatan itu tidak mengakses lab itu.
    """
    if not lab_kapasitas or sum(lab_kapasitas) < 1:
        raise ScheduleError("Kapasitas lab minimal 1 ruang.")

    # Tiap lab berkapasitas N ruang -> N kolom paralel (mis. L1-1, L1-2)
    lab_cols = []  # lab_cols[i] = daftar kolom ruang milik lab ke-(i+1)
    labs = []
    for i, cap in enumerate(lab_kapasitas, 1):
        cols = [f"L{i}-{r}" for r in range(1, cap + 1)]
        lab_cols.append(cols)
        labs.extend(cols)

    schedule = []
    for hari in HARI_PRAK:
        for blok in BLOK_PRAK:
            row = {"Hari": hari, "Blok": blok}
            for l in labs:
                row[l] = "-"
            schedule.append(row)

    kelas_terpakai = [set() for _ in schedule]

    def blok_prak(g):
        # grup g = pasangan kelas. Kuliah pasangan: pagi bila pasangan genap,
        # siang bila ganjil; praktikum di blok KEBALIKANNYA -> kuliah pagi = praktikum siang.
        return 1 if (g - 1) % 2 == 0 else 0  # 1=Siang, 0=Pagi

    def tempatkan(mk, kelas, blok_idx, allowed):
        kandidat = []
        for hari_idx in range(len(HARI_PRAK)):
            b = blok_idx  # praktikum selalu di blok kebalikan kuliah (termasuk Sabtu)
            slot = hari_idx * len(BLOK_PRAK) + b
            if kelas in kelas_terpakai[slot]:
                continue
            kosong = sum(1 for l in allowed if schedule[slot][l] == "-")
            if kosong:
                kandidat.append((kosong, slot))
        if not kandidat:
            return False
        _, slot = max(kandidat)
        for l in allowed:
            if schedule[slot][l] == "-":
                schedule[slot][l] = f"{mk} ({kelas})"
                kelas_terpakai[slot].add(kelas)
                return True
        return False

    grup_per_angkatan = max(1, kelas_per_mkw // 2)
    mk_counter = 1
    for a_idx, baris in enumerate(distribusi_praktikum):
        for lab_idx, jumlah in enumerate(baris):
            if jumlah <= 0:
                continue
            if lab_idx >= len(lab_cols):
                raise ScheduleError(
                    f"Angkatan {a_idx + 1}: kolom lab ke-{lab_idx + 1} tidak ada. "
                    "Jumlah kolom tiap baris harus = jumlah lab."
                )
            allowed = lab_cols[lab_idx]
            for _ in range(jumlah):
                mk = f"PR{mk_counter}"
                mk_counter += 1
                for g in range(1, grup_per_angkatan + 1):
                    lo, hi = 2 * g - 1, min(2 * g, kelas_per_mkw)
                    kelas = f"A{a_idx + 1}K{lo}" + (f"+K{hi}" if hi != lo else "")
                    if not tempatkan(mk, kelas, blok_prak(g), allowed):
                        raise ScheduleError(
                            f"Gagal menjadwalkan {mk} (Lab {lab_idx + 1}) untuk {kelas}. "
                            "Tambah ruang lab itu atau kurangi MK praktikum."
                        )

    return schedule


# ==========================================================================
# Engine berbasis data nyata (Master Data): MK + dosen, cegah bentrok
# kelas, dosen, dan ruang.
# ==========================================================================

def generate_from_db(angkatan, rooms, labs, mk_wajib, mk_pilihan, mk_praktikum,
                     kelas_per_mkp=2):
    """
    angkatan      : list dict {id, tahun, jml_kelas, jml_grup}
    rooms         : list kode ruang kuliah
    labs          : list dict {kode, nama} ruang lab (boleh juga list kode)
    mk_*          : list dict {kode, nama, dosen, angkatan_id, lab}
    Mengembalikan (jadwal_kuliah, jadwal_praktikum).
    """
    if not rooms:
        raise ScheduleError("Belum ada ruang kuliah. Tambahkan di menu Ruang.")
    if mk_praktikum and not labs:
        raise ScheduleError("Ada MK praktikum tapi belum ada ruang lab.")

    # Normalisasi labs -> daftar kode + peta kode->nama lab
    lab_kodes = [l["kode"] if isinstance(l, dict) else l for l in labs]
    lab_nama = {
        (l["kode"] if isinstance(l, dict) else l): (l.get("nama") if isinstance(l, dict) else None)
        for l in labs
    }

    dosen_busy = {}  # (hari_idx, sesi_idx) -> set(dosen)

    def dosen_bentrok(dosen, hari_idx, sesi_list):
        if not dosen:
            return False
        return any(dosen in dosen_busy.get((hari_idx, s), set()) for s in sesi_list)

    def tandai_dosen(dosen, hari_idx, sesi_list):
        if not dosen:
            return
        for s in sesi_list:
            dosen_busy.setdefault((hari_idx, s), set()).add(dosen)

    # ---------------- Jadwal Kuliah (5 hari x 4 sesi) ----------------
    kuliah = []
    for hari in HARI:
        for sesi in SESI:
            row = {"Hari": hari, "Sesi": sesi}
            for r in rooms:
                row[r] = "-"
            kuliah.append(row)
    kelas_busy = [set() for _ in kuliah]

    def blok_kelas_idx(k):
        # Sepasang kelas (K1-K2, K3-K4, ...) berbagi blok yang sama supaya bisa
        # praktikum bersama; antar pasangan bergantian pagi/siang.
        pair = (k - 1) // 2
        return SESI_PAGI if pair % 2 == 0 else SESI_SIANG

    def tempatkan_kuliah(mk, dosen, kelas, sesi_block):
        kandidat = []
        for hari_idx in range(len(HARI)):
            for sesi_idx in sesi_block:
                slot = hari_idx * len(SESI) + sesi_idx
                if kelas in kelas_busy[slot]:
                    continue
                if dosen_bentrok(dosen, hari_idx, [sesi_idx]):
                    continue
                kosong = sum(1 for r in rooms if kuliah[slot][r] == "-")
                if kosong:
                    kandidat.append((kosong, slot, hari_idx, sesi_idx))
        if not kandidat:
            return False
        kandidat.sort(reverse=True)
        _, slot, hari_idx, sesi_idx = kandidat[0]
        for r in rooms:
            if kuliah[slot][r] == "-":
                label = f"{mk} ({kelas})" + (f" · {dosen}" if dosen else "")
                kuliah[slot][r] = label
                kelas_busy[slot].add(kelas)
                tandai_dosen(dosen, hari_idx, [sesi_idx])
                return True
        return False

    ang_by_id = {a["id"]: a for a in angkatan}

    # MK wajib -> semua kelas pada angkatannya
    for mk in mk_wajib:
        a = ang_by_id.get(mk["angkatan_id"])
        if not a:
            continue
        for k in range(1, a["jml_kelas"] + 1):
            kelas = f"{a['tahun']}-K{k}"
            if not tempatkan_kuliah(mk["kode"], mk.get("dosen"), kelas, blok_kelas_idx(k)):
                raise ScheduleError(
                    f"Gagal menjadwalkan {mk['kode']} untuk {kelas} "
                    "(bentrok dosen/kelas atau ruang penuh)."
                )

    # MK pilihan -> kelas_per_mkp kelas pada angkatannya
    for mk in mk_pilihan:
        a = ang_by_id.get(mk["angkatan_id"])
        if not a:
            continue
        for k in range(1, kelas_per_mkp + 1):
            kelas = f"{a['tahun']}-K{k}"
            if not tempatkan_kuliah(mk["kode"], mk.get("dosen"), kelas, blok_kelas_idx(k)):
                raise ScheduleError(
                    f"Gagal menjadwalkan pilihan {mk['kode']} untuk {kelas}."
                )

    # ---------------- Jadwal Praktikum (6 hari x 2 blok) ----------------
    praktikum = []
    for hari in HARI_PRAK:
        for blok in BLOK_PRAK:
            row = {"Hari": hari, "Blok": blok}
            for l in lab_kodes:
                row[l] = "-"
            praktikum.append(row)
    grup_busy = [set() for _ in praktikum]
    SABTU = len(HARI_PRAK) - 1

    def sesi_dari_blok(blok_idx):
        return SESI_SIANG if blok_idx == 1 else SESI_PAGI

    def tempatkan_prak(mk, dosen, grup, blok_idx, allowed):
        kandidat = []
        for hari_idx in range(len(HARI_PRAK)):
            # Praktikum selalu di blok kebalikan blok kuliah grup (termasuk Sabtu),
            # supaya aturan kuliah pagi = praktikum siang terjaga ketat.
            b = blok_idx
            slot = hari_idx * len(BLOK_PRAK) + b
            if grup in grup_busy[slot]:
                continue
            if dosen_bentrok(dosen, hari_idx, sesi_dari_blok(b)):
                continue
            kosong = sum(1 for l in allowed if praktikum[slot][l] == "-")
            if kosong:
                kandidat.append((kosong, slot, hari_idx, b))
        if not kandidat:
            return False
        kandidat.sort(reverse=True)
        _, slot, hari_idx, b = kandidat[0]
        for l in allowed:
            if praktikum[slot][l] == "-":
                label = f"{mk} ({grup})" + (f" · {dosen}" if dosen else "")
                praktikum[slot][l] = label
                grup_busy[slot].add(grup)
                tandai_dosen(dosen, hari_idx, sesi_dari_blok(b))
                return True
        return False

    for mk in mk_praktikum:
        a = ang_by_id.get(mk["angkatan_id"])
        if not a:
            continue
        # Lab yang boleh dipakai MK ini: kalau MK punya 'lab', batasi ke ruang lab
        # dengan nama itu; kalau kosong, semua lab boleh (kompatibel data lama).
        mk_lab = (mk.get("lab") or "").strip()
        allowed = [k for k in lab_kodes if not mk_lab or lab_nama.get(k) == mk_lab]
        if not allowed:
            raise ScheduleError(
                f"MK praktikum {mk['kode']} ditetapkan ke lab '{mk_lab}', "
                "tapi belum ada ruang lab dengan nama itu di menu Ruang."
            )
        # Grup praktikum = gabungan 2 kelas (K1+K2, K3+K4, ...). Kedua kelas dalam
        # satu pasangan berkuliah di blok yang sama, sehingga praktikumnya
        # ditempatkan di blok KEBALIKANNYA -> kuliah pagi = praktikum siang.
        num_grup = (a["jml_kelas"] + 1) // 2
        for g in range(1, num_grup + 1):
            lo, hi = 2 * g - 1, min(2 * g, a["jml_kelas"])
            grup = f"{a['tahun']}-K{lo}" + (f"+K{hi}" if hi != lo else "")
            pair_kuliah_pagi = ((g - 1) % 2 == 0)   # blok kuliah pasangan ini
            blok_idx = 1 if pair_kuliah_pagi else 0  # praktikum = kebalikan (1=Siang, 0=Pagi)
            if not tempatkan_prak(mk["kode"], mk.get("dosen"), grup, blok_idx, allowed):
                raise ScheduleError(
                    f"Gagal menjadwalkan praktikum {mk['kode']} untuk {grup} "
                    f"di lab '{mk_lab or 'mana saja'}' (bentrok dosen atau lab penuh)."
                )

    return kuliah, praktikum


# ==========================================================================
# Deteksi bentrok (untuk validasi setelah edit manual)
# ==========================================================================

def _parse_cell(val):
    """Pisah sel 'MK (ident) · dosen' jadi (ident, dosen). None jika kosong."""
    if not val or val == "-":
        return None
    dosen = None
    main = val
    if "\u00b7" in val:  # karakter ·
        main, dosen = val.split("\u00b7", 1)
        dosen = dosen.strip() or None
    m = re.search(r"\(([^)]*)\)", main)
    ident = m.group(1).strip() if m else main.strip()
    return ident, dosen


def detect_conflicts(schedule, praktikum):
    """Kembalikan daftar string bentrok: kelas/grup dobel & dosen bentrok."""
    conflicts = []
    dosen_at = defaultdict(list)   # (hari, sesi_idx) -> [dosen]
    kelas_at = defaultdict(list)   # (hari, sesi_idx) -> [ident kuliah]
    grup_at = defaultdict(list)    # (hari, blok)     -> [ident praktikum]

    for row in schedule or []:
        hari, sesi = row.get("Hari"), row.get("Sesi")
        if sesi not in SESI:
            continue
        s = SESI.index(sesi)
        for col, val in row.items():
            if col in ("Hari", "Sesi"):
                continue
            parsed = _parse_cell(val)
            if not parsed:
                continue
            ident, dosen = parsed
            kelas_at[(hari, s)].append(ident)
            if dosen:
                dosen_at[(hari, s)].append(dosen)

    for row in praktikum or []:
        hari, blok = row.get("Hari"), row.get("Blok")
        sesi_list = SESI_PAGI if blok == "Pagi" else SESI_SIANG
        for col, val in row.items():
            if col in ("Hari", "Blok"):
                continue
            parsed = _parse_cell(val)
            if not parsed:
                continue
            ident, dosen = parsed
            grup_at[(hari, blok)].append(ident)
            if dosen:
                for s in sesi_list:
                    dosen_at[(hari, s)].append(dosen)

    for (hari, s), idents in kelas_at.items():
        for x in sorted({i for i in idents if idents.count(i) > 1}):
            conflicts.append(f"Kelas {x} terjadwal ganda di {hari} {SESI[s]} (kuliah).")
    for (hari, blok), idents in grup_at.items():
        for x in sorted({i for i in idents if idents.count(i) > 1}):
            conflicts.append(f"Grup {x} terjadwal ganda di {hari} {blok} (praktikum).")
    for (hari, s), names in dosen_at.items():
        for x in sorted({n for n in names if names.count(n) > 1}):
            conflicts.append(f"Dosen {x} bentrok di {hari} {SESI[s]}.")

    return conflicts
