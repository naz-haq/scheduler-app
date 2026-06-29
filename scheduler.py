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
            blok_kelas[nama] = 0 if k % 2 == 1 else 1  # ganjil pagi, genap siang
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
    lab_kapasitas,         # ruang tiap lab, contoh: [3, 2, 2, 1] -> total 8 ruang
    distribusi_praktikum,  # MK praktikum per angkatan, contoh: [5, 4, 3]
    kelas_per_mkw,         # jumlah kelas kuliah/angkatan (mis. 12), digabung 2->1
):
    """Praktikum 2 blok (pagi/siang) di blok lawan kuliah + Sabtu bebas, lab terpisah, tanpa bentrok."""
    if not lab_kapasitas or sum(lab_kapasitas) < 1:
        raise ScheduleError("Kapasitas lab minimal 1 ruang.")

    # Tiap lab berkapasitas N ruang -> N kolom paralel (mis. L1-1, L1-2)
    labs = [f"L{i}-{r}" for i, cap in enumerate(lab_kapasitas, 1) for r in range(1, cap + 1)]

    schedule = []
    for hari in HARI_PRAK:
        for blok in BLOK_PRAK:
            row = {"Hari": hari, "Blok": blok}
            for l in labs:
                row[l] = "-"
            schedule.append(row)

    kelas_terpakai = [set() for _ in schedule]
    SABTU = len(HARI_PRAK) - 1

    def blok_prak(kel_idx):
        # grup separuh awal kuliah pagi -> praktikum siang; sisanya kuliah siang -> praktikum pagi
        return 1 if kel_idx <= grup_per_angkatan // 2 else 0  # 1=Siang, 0=Pagi

    def tempatkan(mk, kelas, blok_idx):
        kandidat = []
        for hari_idx in range(len(HARI_PRAK)):
            blok_list = [0, 1] if hari_idx == SABTU else [blok_idx]
            for b in blok_list:
                slot = hari_idx * len(BLOK_PRAK) + b
                if kelas in kelas_terpakai[slot]:
                    continue
                kosong = sum(1 for l in labs if schedule[slot][l] == "-")
                if kosong:
                    kandidat.append((kosong, slot))
        if not kandidat:
            return False
        _, slot = max(kandidat)
        for l in labs:
            if schedule[slot][l] == "-":
                schedule[slot][l] = f"{mk} ({kelas})"
                kelas_terpakai[slot].add(kelas)
                return True
        return False

    grup_per_angkatan = max(1, kelas_per_mkw // 2)
    mk_counter = 1
    for a_idx, jumlah in enumerate(distribusi_praktikum):
        for _ in range(jumlah):
            mk = f"PR{mk_counter}"
            mk_counter += 1
            for g in range(1, grup_per_angkatan + 1):
                kelas = f"A{a_idx + 1}C{g}"
                if not tempatkan(mk, kelas, blok_prak(g)):
                    raise ScheduleError(
                        f"Gagal menjadwalkan {mk} untuk {kelas}. "
                        "Tambah lab atau kurangi MK praktikum."
                    )

    return schedule
