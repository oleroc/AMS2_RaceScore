"""RaceScore 1.6.2 high score pull (PANEL_PLAN 17c rev 2), headless: DatabaseThread.store_highscores and
HighScorePuller against a fake agent, on a COPY of a RaceDB in a temp folder. Never touches the live DB.

    python test_highscore_pull.py [path to a RaceDB to copy]   (default: a fresh empty schema)
"""
import importlib.util
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ok = True


def check(label, cond, extra=""):
    global ok
    ok &= bool(cond)
    print(("PASS " if cond else "FAIL ") + label, "" if cond else extra)


tmp = tempfile.mkdtemp(prefix="rs_hs_test_")
db = os.path.join(tmp, "RaceDB.db")
if len(sys.argv) > 1:
    shutil.copyfile(sys.argv[1], db)
os.chdir(tmp)                              # RS opens 'RaceDB.db' and 'config.ini' in the cwd

spec = importlib.util.spec_from_file_location("rs162", os.path.join(HERE, "RaceMonitor_v1.6.2.py"))
RS = importlib.util.module_from_spec(spec)
spec.loader.exec_module(RS)

# a DatabaseThread without starting the Qt thread: the same connection setup as run()
dbt = RS.DatabaseThread.__new__(RS.DatabaseThread)
dbt.ip_name_flag = {}
dbt.conn = sqlite3.connect(db, check_same_thread=False)
dbt.cursor = dbt.conn.cursor()
dbt.create_database()
c = dbt.cursor
c.execute("SELECT MAX(Phone) FROM Drivers")
max_phone = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM HighScore")
hs_before = c.fetchone()[0]

T, CAR = "Test Layout - Nowhere Ring", "Test Car GT"
res = []
dbt.store_highscores("1.2.3.4", [
    {"id": 1, "name": "Zz New Driver", "track": T, "car": CAR, "best": 80.5, "lap_no": 3, "session": "race"},
    {"id": 2, "name": "Bot (AI)", "track": T, "car": CAR, "best": 70.0},
    {"id": 3, "name": "Zz New Driver", "track": T, "car": "Other Car", "best": 90.0},
], res.append)
check("store: done(True)", res == [True], res)
c.execute("SELECT Phone FROM Drivers WHERE Name='Zz New Driver'")
ph = c.fetchone()
check("new driver made with MAX(Phone)+1", ph and ph[0] == (max_phone + 1 if max_phone else 90000001), (ph, max_phone))
c.execute("SELECT BestLap, lapnumber, phone FROM HighScore WHERE Name='Zz New Driver' AND mTrackvariation=? AND MCarName=?",
          (T, CAR))
check("high score inserted with phone + lap", c.fetchone() == (80.5, 3, ph[0]))
c.execute("SELECT COUNT(*) FROM HighScore WHERE Name='Bot (AI)'")
check("(AI) skipped", c.fetchone()[0] == 0)
c.execute("SELECT COUNT(*) FROM HighScore")
check("two rows added", c.fetchone()[0] == hs_before + 2)

res.clear()
dbt.store_highscores("1.2.3.4", [{"id": 4, "name": "Zz New Driver", "track": T, "car": CAR, "best": 81.0}], res.append)
c.execute("SELECT BestLap FROM HighScore WHERE Name='Zz New Driver' AND mTrackvariation=? AND MCarName=?", (T, CAR))
check("slower: no change", res == [True] and c.fetchone()[0] == 80.5)
dbt.store_highscores("1.2.3.4", [{"id": 5, "name": "Zz New Driver", "track": T, "car": CAR, "best": 79.25, "lap_no": 7}],
                     res.append)
c.execute("SELECT BestLap, lapnumber FROM HighScore WHERE Name='Zz New Driver' AND mTrackvariation=? AND MCarName=?",
          (T, CAR))
check("faster: updated", c.fetchone() == (79.25, 7))
c.execute("SELECT COUNT(*) FROM HighScore WHERE Name='Zz New Driver' AND mTrackvariation=? AND MCarName=?", (T, CAR))
check("still one row for driver + key", c.fetchone()[0] == 1)
c.execute("SELECT COUNT(*) FROM Drivers WHERE Name='Zz New Driver'")
check("still one Drivers row", c.fetchone()[0] == 1)

res.clear()
dbt.store_highscores("1.2.3.4", [{"id": 6, "name": "X", "track": T}], res.append)     # no car / best
check("bad row: done(False), rolled back", res == [False])
c.execute("SELECT COUNT(*) FROM Drivers WHERE Name='X'")
check("bad row: no Drivers row left", c.fetchone()[0] == 0)

# ---- the puller against a fake agent -------------------------------------------------------------
QUEUE = [{"id": 10, "name": "Zz Puller", "track": T, "car": CAR, "best": 77.7, "lap_no": 2, "session": "time trial",
          "when": "2026-11-10 12:00:00"}]
ACKS = []


class Agent(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/highscores":
            body = {"ok": True, "rows": [r for r in QUEUE if r["id"] > (ACKS[-1] if ACKS else 0)]}
        elif u.path == "/highscores/ack":
            ACKS.append(int(parse_qs(u.query)["upto"][0]))
            body = {"ok": True, "acked": 1}
        else:
            self.send_error(404)
            return
        b = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)


srv = ThreadingHTTPServer(("127.0.0.1", 0), Agent)
threading.Thread(target=srv.serve_forever, daemon=True).start()
with open("config.ini", "w") as f:
    f.write(f"[config]\nagent_port = {srv.server_address[1]}\nhighscore_pull_s = 60\n")

import queue as Q  # noqa: E402
tq = Q.Queue()


def db_worker():                      # what DatabaseThread.run does with the queue
    while True:
        op, args = tq.get()
        dbt.process_queue(op, *args)


threading.Thread(target=db_worker, daemon=True).start()
p = RS.HighScorePuller(tq, ["127.0.0.1", "127.0.0.9"])   # .9: nothing listens -> skipped
check("every() from config", p.every() == 60.0)
t0 = time.time()
for ip in p.ips:
    p.pull(ip)
check("pull: acked up to 10", ACKS == [10], ACKS)
c.execute("SELECT BestLap FROM HighScore WHERE Name='Zz Puller'")
check("pull: stored", c.fetchone() == (77.7,))
p.pull("127.0.0.1")
check("pull again: queue empty, no new ack", ACKS == [10], ACKS)
check("dead sim skipped quickly", time.time() - t0 < 10, time.time() - t0)

srv.shutdown()
dbt.conn.close()
os.chdir(HERE)
shutil.rmtree(tmp, ignore_errors=True)
print("\nALL PASSED" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
