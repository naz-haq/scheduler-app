from flask import Flask, render_template, request, send_file
import pandas as pd
from scheduler import generate_schedule
from collections import defaultdict
from datetime import datetime


def calculate_frequency(schedule):
    freq = defaultdict(int)

    for row in schedule:
        for key, value in row.items():
            if key in ["Hari", "Sesi"]:
                continue
            if value and value != "-":
                mk = value.split(" ")[0]
                freq[mk] += 1

    return dict(sorted(freq.items()))


app = Flask(__name__)
current_schedule = []

@app.route("/", methods=["GET", "POST"])
def index():
    global current_schedule
    freq = {}

    # nilai default
    form_data = {
        "days": 5,
        "num_rooms": 16,
        "num_classes": 12,
        "kelas_pagi": "3,4,7,8,11,12",
        "kelas_siang": "1,2,5,6,9,10",
        "num_sessions": 4,
        "distribusi": "8,7,7",
        "num_pilihan": 10,
        "freq_pilihan": 2,
    }

    if request.method == "POST":

        # ambil data dari form
        for key in form_data.keys():
            if key in request.form:
                form_data[key] = request.form[key]

        days = int(form_data["days"])
        num_rooms = int(form_data["num_rooms"])
        num_classes = int(form_data["num_classes"])

        kelas_pagi = [int(x) for x in form_data["kelas_pagi"].split(",")]
        kelas_siang = [int(x) for x in form_data["kelas_siang"].split(",")]

        distribusi = [int(x) for x in form_data["distribusi"].split(",")]

        num_pilihan = int(form_data["num_pilihan"])
        freq_pilihan = int(form_data["freq_pilihan"])

        sessions = []
        for i in range(1, int(form_data["num_sessions"]) + 1):
            tipe = request.form.get(f"sesi_{i}_type", "pagi")
            sessions.append({
                "name": f"Sesi {i}",
                "type": tipe
            })

        mode = request.form.get("mode", "stable")

        config = {
            "days": days,
            "sessions": sessions,
            "num_rooms": num_rooms,
            "num_classes": num_classes,
            "kelas_pagi": kelas_pagi,
            "kelas_siang": kelas_siang,
            "mk_semester": distribusi,
            "mk_pilihan": num_pilihan,
            "freq_pilihan": freq_pilihan,
            "mode": mode,
}

        try:
            current_schedule = generate_schedule(config)
            freq = calculate_frequency(current_schedule)
        except Exception as e:
            return render_template(
                "index.html",
                error=str(e),
                schedule=[],
                form_data=form_data
            )

    else:
        current_schedule = []

    return render_template(
        "index.html",
        schedule=current_schedule,
        freq=freq,
        error=None,
        form_data=form_data
    )


@app.route("/export")
def export():
    global current_schedule

    if not current_schedule:
        return "Belum ada jadwal"

    df = pd.DataFrame(current_schedule)

    # ambil waktu sekarang
    now = datetime.now()
    timestamp = now.strftime("%d-%m-%Y_%H-%M")

    file_name = f"Jadwal_MK_{timestamp}.xlsx"
    file_path = file_name

    df.to_excel(file_path, index=False)

    return send_file(file_path, as_attachment=True, download_name=file_name)


if __name__ == "__main__":
    app.run(debug=True)
