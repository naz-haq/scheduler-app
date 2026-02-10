from collections import defaultdict
import random


def validate_capacity(config):
    days = config["days"]
    sessions = config["sessions"]
    num_rooms = config["num_rooms"]
    distribusi_semester = config["mk_semester"]
    kelas_pagi = config["kelas_pagi"]
    kelas_siang = config["kelas_siang"]
    num_mk_pilihan = config["mk_pilihan"]
    freq_pilihan = config["freq_pilihan"]

    total_slots = days * len(sessions) * num_rooms

    total_mk_wajib = sum(distribusi_semester) * (
        len(kelas_pagi) + len(kelas_siang)
    )

    total_mk_pilihan = num_mk_pilihan * freq_pilihan

    total_kebutuhan = total_mk_wajib + total_mk_pilihan

    if total_kebutuhan > total_slots:
        return (
            False,
            f"Kapasitas tidak cukup: butuh {total_kebutuhan} slot, "
            f"tersedia {total_slots} slot"
        )

    return True, "OK"


def generate_schedule(config):
    valid, message = validate_capacity(config)
    if not valid:
        raise Exception(message)

    days = config["days"]
    sessions = config["sessions"]
    num_rooms = config["num_rooms"]
    num_classes = config["num_classes"]
    kelas_pagi = config["kelas_pagi"]
    kelas_siang = config["kelas_siang"]
    distribusi_semester = config["mk_semester"]
    num_mk_pilihan = config["mk_pilihan"]
    freq_pilihan = config["freq_pilihan"]
    mode = config.get("mode", "stable")

    # Mode stabil → hasil selalu sama
    if mode == "stable":
        random.seed(1)

    rooms = [f"R{i}" for i in range(1, num_rooms + 1)]

    # Buat struktur jadwal kosong
    schedule = []
    for d in range(days):
        for sesi in sessions:
            row = {"Hari": f"Hari {d+1}", "Sesi": sesi["name"]}
            for r in rooms:
                row[r] = "-"
            schedule.append(row)

    def get_slot_index(hari_idx, sesi_idx):
        return hari_idx * len(sessions) + sesi_idx

    # -----------------------------
    # Generate MK per semester
    # -----------------------------
    mk_counter = 1
    semester_mk = []
    for jumlah in distribusi_semester:
        mk_list = []
        for _ in range(jumlah):
            mk_list.append(f"W{mk_counter}")
            mk_counter += 1
        semester_mk.append(mk_list)

    # Mode random → acak urutan MK wajib
    if mode == "random":
        for mk_list in semester_mk:
            random.shuffle(mk_list)

    # -----------------------------
    # Jadwal MK wajib
    # -----------------------------
    for mk_list in semester_mk:
        for mk in mk_list:

            # kelas pagi
            for kelas in kelas_pagi:
                placed = False
                for hari_idx in range(days):
                    for sesi_idx, sesi in enumerate(sessions):
                        if sesi["type"] != "pagi":
                            continue
                        slot_idx = get_slot_index(hari_idx, sesi_idx)
                        row = schedule[slot_idx]

                        for room in rooms:
                            if row[room] == "-":
                                row[room] = f"{mk} (K{kelas})"
                                placed = True
                                break
                        if placed:
                            break
                    if placed:
                        break
                if not placed:
                    raise Exception(f"Gagal menjadwalkan {mk} (K{kelas})")

            # kelas siang
            for kelas in kelas_siang:
                placed = False
                for hari_idx in range(days):
                    for sesi_idx, sesi in enumerate(sessions):
                        if sesi["type"] != "siang":
                            continue
                        slot_idx = get_slot_index(hari_idx, sesi_idx)
                        row = schedule[slot_idx]

                        for room in rooms:
                            if row[room] == "-":
                                row[room] = f"{mk} (K{kelas})"
                                placed = True
                                break
                        if placed:
                            break
                    if placed:
                        break
                if not placed:
                    raise Exception(f"Gagal menjadwalkan {mk} (K{kelas})")

    # -----------------------------
    # MK pilihan
    # -----------------------------
    kelas_atas = [k for k in range(7, num_classes + 1)]

    for i in range(1, num_mk_pilihan + 1):
        mk = f"P{i}"

        if mode == "random":
            kelas = random.choice(kelas_atas)
        else:
            kelas = kelas_atas[i % len(kelas_atas)]

        tipe = "pagi" if kelas in kelas_pagi else "siang"
        placed = 0

        for hari_idx in range(days):
            for sesi_idx, sesi in enumerate(sessions):

                if sesi["type"] != tipe:
                    continue

                if placed >= freq_pilihan:
                    break

                slot_idx = get_slot_index(hari_idx, sesi_idx)
                row = schedule[slot_idx]

                for room in rooms:
                    if row[room] == "-":
                        row[room] = f"{mk} (K{kelas})"
                        placed += 1
                        break
            if placed >= freq_pilihan:
                break

    return schedule
