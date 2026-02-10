from flask import Flask, render_template, request, send_file
import pandas as pd
from scheduler import generate_schedule

app = Flask(__name__)
current_schedule = []

@app.route("/", methods=["GET", "POST"])
def index():
    global current_schedule

    if request.method == "POST":
        days = int(request.form["days"])
        num_rooms = int(request.form["num_rooms"])
        num_classes = int(request.form["num_classes"])

        kelas_pagi = [int(x) for x in request.form["kelas_pagi"].split(",")]
        kelas_siang = [int(x) for x in request.form["kelas_siang"].split(",")]

        distribusi = [int(x) for x in request.form["distribusi"].split(",")]

        num_pilihan = int(request.form["num_pilihan"])
        freq_pilihan = int(request.form["freq_pilihan"])

        sessions = []
        for i in range(1, int(request.form["num_sessions"]) + 1):
            tipe = request.form.get(f"sesi_{i}_type", "pagi")
            sessions.append({
                "name": f"Sesi {i}",
                "type": tipe
            })

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
        }

        current_schedule = generate_schedule(config)

    return render_template("index.html", schedule=current_schedule)


@app.route("/export")
def export():
    global current_schedule
    df = pd.DataFrame(current_schedule)
    file_path = "jadwal.xlsx"
    df.to_excel(file_path, index=False)
    return send_file(file_path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
