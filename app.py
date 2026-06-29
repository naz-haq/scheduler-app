import os
import sys
import tempfile
import threading
import webbrowser

from flask import Flask, render_template, request, send_file
import pandas as pd
from scheduler import generate_schedule, generate_praktikum, ScheduleError


def resource_path(relative):
    """Resolve path to bundled resources (works in dev and PyInstaller)."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


app = Flask(
    __name__,
    template_folder=resource_path("templates"),
    static_folder=resource_path("static"),
)
current_schedule = []
current_praktikum = []


def _parse_int(value, label, minimum=0):
    try:
        n = int(str(value).strip())
    except (ValueError, TypeError):
        raise ScheduleError(f"{label} harus berupa angka.")
    if n < minimum:
        raise ScheduleError(f"{label} minimal {minimum}.")
    return n


@app.route("/", methods=["GET", "POST"])
def index():
    global current_schedule, current_praktikum
    error = None

    if request.method == "POST":
        try:
            num_rooms = _parse_int(request.form.get("num_rooms"), "Jumlah ruangan", 1)
            num_pilihan = _parse_int(request.form.get("num_pilihan"), "Jumlah MK pilihan", 0)
            kelas_mkw = _parse_int(request.form.get("kelas_mkw"), "Kelas per MK wajib", 1)
            kelas_mkp = _parse_int(request.form.get("kelas_mkp"), "Kelas per MK pilihan", 1)

            raw = (request.form.get("distribusi") or "").split(",")
            distribusi = [_parse_int(x, "Distribusi MK wajib", 0) for x in raw if x.strip()]
            if not distribusi:
                raise ScheduleError("Distribusi MK wajib tidak boleh kosong.")

            raw_lab = (request.form.get("lab_kapasitas") or "").split(",")
            lab_kapasitas = [_parse_int(x, "Kapasitas lab", 1) for x in raw_lab if x.strip()]
            if not lab_kapasitas:
                raise ScheduleError("Kapasitas lab tidak boleh kosong.")

            raw_p = (request.form.get("distribusi_prak") or "").split(",")
            distribusi_prak = [_parse_int(x, "Distribusi praktikum", 0) for x in raw_p if x.strip()]

            # MKP untuk angkatan 2024 & 2025 = 2 angkatan terakhir
            angkatan_pilihan = [len(distribusi) - 2, len(distribusi) - 1]
            angkatan_pilihan = [a for a in angkatan_pilihan if a >= 0]

            current_schedule = generate_schedule(
                num_rooms=num_rooms,
                distribusi_semester=distribusi,
                num_mk_pilihan=num_pilihan,
                kelas_per_mkw=kelas_mkw,
                kelas_per_mkp=kelas_mkp,
                angkatan_pilihan=angkatan_pilihan,
            )
            current_praktikum = generate_praktikum(
                lab_kapasitas=lab_kapasitas,
                distribusi_praktikum=distribusi_prak,
                kelas_per_mkw=kelas_mkw,
            )
        except ScheduleError as e:
            error = str(e)

    return render_template(
        "index.html",
        schedule=current_schedule,
        praktikum=current_praktikum,
        error=error,
    )


@app.route("/export")
def export():
    global current_schedule, current_praktikum
    if not current_schedule:
        return "Belum ada jadwal untuk diekspor. Buat jadwal dulu.", 400
    file_path = os.path.join(tempfile.gettempdir(), "jadwal.xlsx")
    with pd.ExcelWriter(file_path) as writer:
        pd.DataFrame(current_schedule).to_excel(writer, sheet_name="Kuliah", index=False)
        if current_praktikum:
            pd.DataFrame(current_praktikum).to_excel(writer, sheet_name="Praktikum", index=False)
    return send_file(file_path, as_attachment=True, download_name="jadwal.xlsx")


if __name__ == "__main__":
    port = 5000
    if not getattr(sys, "frozen", False):
        # dev mode: hot reload
        app.run(debug=True, port=port)
    else:
        # desktop mode: open browser then serve
        threading.Timer(1.0, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()
        app.run(host="127.0.0.1", port=port, debug=False)
