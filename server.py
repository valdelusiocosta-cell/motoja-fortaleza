#!/usr/bin/env python3
"""MotoJá Fortaleza local MVP: stdlib HTTP API + SQLite persistence.

This server intentionally keeps integrations behind small adapter functions (quote,
notifications, payments and identity checks) so they can be replaced in production.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import datetime as dt
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import threading

ROOT = Path(__file__).parent
PUBLIC = ROOT / "public"
DB_PATH = Path(os.environ.get("MOTOJA_DB", ROOT / "motoja.sqlite3"))
PORT = int(os.environ.get("PORT", "3000"))
DB_LOCK = threading.RLock()

STATUSES = ("searching", "accepted", "in_progress", "finished", "cancelled")
TRANSITIONS = {
    "accept": ("searching", "accepted"),
    "start": ("accepted", "in_progress"),
    "finish": ("in_progress", "finished"),
    "cancel": (("searching", "accepted", "in_progress"), "cancelled"),
}


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def db():
    con = sqlite3.connect(DB_PATH, timeout=15)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()
    return salt + "$" + digest


def verify_password(password, stored):
    try:
        salt, digest = stored.split("$", 1)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()
        return hmac.compare_digest(actual, digest)
    except ValueError:
        return False


def init_db():
    with DB_LOCK, db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
          phone TEXT UNIQUE, email TEXT UNIQUE, password_hash TEXT NOT NULL,
          role TEXT NOT NULL CHECK(role IN ('passenger','driver','admin')),
          status TEXT NOT NULL DEFAULT 'active', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS driver_profiles (
          user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
          approval_status TEXT NOT NULL DEFAULT 'pending', online INTEGER NOT NULL DEFAULT 0,
          cpf TEXT, cnh TEXT, ear INTEGER NOT NULL DEFAULT 0,
          vehicle_model TEXT DEFAULT 'Honda CG 160', vehicle_plate TEXT DEFAULT 'A CONFIRMAR',
          vehicle_year INTEGER, rating REAL NOT NULL DEFAULT 5.0,
          updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS documents (
          id INTEGER PRIMARY KEY AUTOINCREMENT, driver_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          kind TEXT NOT NULL, filename TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
          submitted_at TEXT NOT NULL, reviewed_at TEXT, review_note TEXT
        );
        CREATE TABLE IF NOT EXISTS fare_config (
          id INTEGER PRIMARY KEY CHECK(id=1), base REAL NOT NULL, per_km REAL NOT NULL,
          per_min REAL NOT NULL, minimum REAL NOT NULL, commission REAL NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS rides (
          id TEXT PRIMARY KEY, passenger_id INTEGER NOT NULL REFERENCES users(id), driver_id INTEGER REFERENCES users(id),
          origin TEXT NOT NULL, destination TEXT NOT NULL, origin_lat REAL, origin_lng REAL,
          destination_lat REAL, destination_lng REAL, payment_method TEXT NOT NULL,
          distance_km REAL NOT NULL, duration_min INTEGER NOT NULL, fare REAL NOT NULL,
          status TEXT NOT NULL, created_at TEXT NOT NULL, accepted_at TEXT, started_at TEXT,
          finished_at TEXT, cancelled_at TEXT, cancel_reason TEXT
        );
        CREATE TABLE IF NOT EXISTS ride_events (
          id INTEGER PRIMARY KEY AUTOINCREMENT, ride_id TEXT NOT NULL REFERENCES rides(id) ON DELETE CASCADE,
          actor_id INTEGER, event TEXT NOT NULL, detail TEXT, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS ratings (
          id INTEGER PRIMARY KEY AUTOINCREMENT, ride_id TEXT UNIQUE NOT NULL REFERENCES rides(id),
          passenger_id INTEGER NOT NULL, driver_id INTEGER, score INTEGER NOT NULL, comment TEXT, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS incidents (
          id INTEGER PRIMARY KEY AUTOINCREMENT, ride_id TEXT, reporter_id INTEGER NOT NULL, type TEXT NOT NULL,
          description TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'open', created_at TEXT NOT NULL, resolved_at TEXT
        );
        CREATE TABLE IF NOT EXISTS sessions (
          token TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, created_at TEXT NOT NULL
        );
        INSERT OR IGNORE INTO fare_config(id,base,per_km,per_min,minimum,commission,updated_at)
          VALUES(1, 3.50, 1.35, 0.18, 7.50, 0.20, datetime('now'));
        """)
        # Safe, local-only demo accounts make all three surfaces testable immediately.
        seed = [
            ("Passageiro Demo", "85999990001", "passageiro@demo.motoja.local", "passenger", "active"),
            ("Motorista Demo", "85999990002", "motorista@demo.motoja.local", "driver", "active"),
            ("Admin Demo", "85999990003", "admin@demo.motoja.local", "admin", "active"),
        ]
        for name, phone, email, role, status in seed:
            con.execute("INSERT OR IGNORE INTO users(name,phone,email,password_hash,role,status,created_at) VALUES(?,?,?,?,?,?,?)",
                        (name, phone, email, hash_password("demo1234"), role, status, now()))
        driver = con.execute("SELECT id FROM users WHERE email=?", ("motorista@demo.motoja.local",)).fetchone()
        if driver:
            con.execute("""INSERT OR IGNORE INTO driver_profiles(user_id,approval_status,online,cpf,cnh,ear,vehicle_model,vehicle_plate,vehicle_year,updated_at)
                         VALUES(?,?,?,?,?,?,?,?,?,?)""", (driver[0], "approved", 0, "000.000.000-00", "00000000000", 1, "Honda CG 160", "MJA-2026", 2024, now()))


def clean(value, field, required=True, max_len=240):
    if value is None:
        if required: raise ValueError(f"Informe {field}.")
        return ""
    value = str(value).strip()
    if required and not value: raise ValueError(f"Informe {field}.")
    if len(value) > max_len: raise ValueError(f"{field.capitalize()} excede o limite permitido.")
    return value


def quote(origin, destination):
    """Temporary deterministic quote adapter; replace with map/route provider."""
    with db() as con:
        row = con.execute("SELECT base,per_km,per_min,minimum FROM fare_config WHERE id=1").fetchone()
    # Until a route provider is configured, a bounded deterministic estimate is explicit in UI.
    distance = min(35.0, max(2.0, 3.5 + ((len(origin) * 3 + len(destination)) % 145) / 10))
    duration = max(5, round(distance * 3.1))
    fare = max(row[3], row[0] + distance * row[1] + duration * row[2])
    return {"distanceKm": round(distance, 1), "durationMin": duration, "fare": round(fare, 2), "currency": "BRL", "estimate": True}


def user_dict(row):
    if not row: return None
    return {"id": row["id"], "name": row["name"], "phone": row["phone"], "email": row["email"], "role": row["role"], "status": row["status"], "createdAt": row["created_at"]}


def driver_dict(con, user_id):
    row = con.execute("SELECT u.*,p.* FROM users u JOIN driver_profiles p ON p.user_id=u.id WHERE u.id=?", (user_id,)).fetchone()
    if not row: return None
    docs = con.execute("SELECT id,kind,filename,status,submitted_at,review_note FROM documents WHERE driver_id=? ORDER BY id DESC", (user_id,)).fetchall()
    return {"id": row["id"], "name": row["name"], "phone": row["phone"], "email": row["email"], "role": "driver", "status": row["status"],
            "approvalStatus": row["approval_status"], "online": bool(row["online"]), "rating": row["rating"], "cpf": row["cpf"], "cnh": row["cnh"], "ear": bool(row["ear"]),
            "vehicle": {"model": row["vehicle_model"], "plate": row["vehicle_plate"], "year": row["vehicle_year"]},
            "documents": [{"id":d["id"],"kind":d["kind"],"filename":d["filename"],"status":d["status"],"submittedAt":d["submitted_at"],"reviewNote":d["review_note"]} for d in docs]}


def ride_dict(con, ride):
    if not ride: return None
    passenger = con.execute("SELECT id,name,phone FROM users WHERE id=?", (ride["passenger_id"],)).fetchone()
    driver = con.execute("SELECT id,name,phone FROM users WHERE id=?", (ride["driver_id"],)).fetchone() if ride["driver_id"] else None
    rating = con.execute("SELECT score,comment FROM ratings WHERE ride_id=?", (ride["id"],)).fetchone()
    events = con.execute("SELECT event,detail,created_at FROM ride_events WHERE ride_id=? ORDER BY id", (ride["id"],)).fetchall()
    return {"id": ride["id"], "status": ride["status"], "origin": ride["origin"], "destination": ride["destination"],
            "paymentMethod": ride["payment_method"], "quote": {"distanceKm":ride["distance_km"],"durationMin":ride["duration_min"],"fare":ride["fare"],"currency":"BRL","estimate":True},
            "passenger": dict(passenger) if passenger else None,
            "driver": ({"id":driver["id"],"name":driver["name"],"phone":driver["phone"],"rating":4.9,"motorcycle":"Honda CG 160","plate":"a confirmar"} if driver else None),
            "createdAt":ride["created_at"], "acceptedAt":ride["accepted_at"], "startedAt":ride["started_at"], "finishedAt":ride["finished_at"],
            "cancelReason":ride["cancel_reason"], "rating":dict(rating) if rating else None,
            "events":[{"event":e["event"],"detail":e["detail"],"createdAt":e["created_at"]} for e in events]}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def headers_common(self, content_type="application/json; charset=utf-8"):
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Cache-Control", "no-store")

    def send_json(self, status, data):
        raw = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status); self.headers_common(); self.send_header("Content-Length", str(len(raw))); self.end_headers(); self.wfile.write(raw)

    def body(self):
        try:
            length = min(int(self.headers.get("Content-Length", 0)), 2_000_000)
            return json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            raise ValueError("JSON inválido.")

    def auth(self, roles=None, optional=False):
        token = self.headers.get("Authorization", "").replace("Bearer ", "", 1).strip()
        with db() as con:
            row = con.execute("SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token=?", (token,)).fetchone() if token else None
        if not row:
            if optional: return None
            raise PermissionError("Faça login para continuar.")
        if row["status"] != "active": raise PermissionError("Esta conta está suspensa.")
        if roles and row["role"] not in roles: raise PermissionError("Você não tem permissão para esta ação.")
        return row

    def do_OPTIONS(self):
        self.send_response(204); self.headers_common(); self.send_header("Content-Length", "0"); self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        try:
            if path == "/api/health": return self.send_json(200, {"ok":True,"service":"motoja-api","database":"sqlite","time":now()})
            if path.startswith("/api/"): return self.api_get(path)
            self.static(path)
        except PermissionError as e: self.send_json(401, {"error":str(e)})
        except (ValueError, KeyError) as e: self.send_json(400, {"error":str(e)})
        except Exception as e: self.send_json(500, {"error":"Erro interno do servidor.","detail":str(e)})

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            if path.startswith("/api/"): return self.api_post(path)
            self.send_json(404, {"error":"Rota não encontrada."})
        except PermissionError as e: self.send_json(401, {"error":str(e)})
        except ValueError as e: self.send_json(400, {"error":str(e)})
        except sqlite3.IntegrityError: self.send_json(409, {"error":"Registro já existe ou é inválido."})
        except Exception as e: self.send_json(500, {"error":"Erro interno do servidor.","detail":str(e)})

    def static(self, path):
        requested = "index.html" if path == "/" else path.lstrip("/")
        file = (PUBLIC / requested).resolve()
        if not str(file).startswith(str(PUBLIC.resolve())) or not file.is_file(): return self.send_json(404,{"error":"Página não encontrada."})
        types = {".html":"text/html; charset=utf-8", ".js":"text/javascript; charset=utf-8", ".css":"text/css; charset=utf-8"}
        raw = file.read_bytes(); self.send_response(200); self.headers_common(types.get(file.suffix,"application/octet-stream")); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)

    def api_get(self, path):
        user = self.auth(optional=path in ("/api/me",))
        if path == "/api/me":
            if not user: return self.send_json(401,{"error":"Faça login para continuar."})
            with db() as con: result = user_dict(user); result["driver"] = driver_dict(con,user["id"]) if user["role"]=="driver" else None
            return self.send_json(200,result)
        if path == "/api/rides":
            with db() as con:
                if user["role"] == "admin": rows=con.execute("SELECT * FROM rides ORDER BY created_at DESC LIMIT 100").fetchall()
                elif user["role"] == "driver": rows=con.execute("SELECT * FROM rides WHERE driver_id=? ORDER BY created_at DESC LIMIT 100",(user["id"],)).fetchall()
                else: rows=con.execute("SELECT * FROM rides WHERE passenger_id=? ORDER BY created_at DESC LIMIT 100",(user["id"],)).fetchall()
                return self.send_json(200,[ride_dict(con,r) for r in rows])
        match = re.fullmatch(r"/api/rides/([A-Za-z0-9_-]+)",path)
        if match:
            with db() as con: row=con.execute("SELECT * FROM rides WHERE id=?",(match.group(1),)).fetchone(); result=ride_dict(con,row) if row else None
            if not result: return self.send_json(404,{"error":"Corrida não encontrada."})
            if user["role"] != "admin" and user["id"] not in (result["passenger"]["id"], result["driver"]["id"] if result["driver"] else -1): return self.send_json(403,{"error":"Acesso negado."})
            return self.send_json(200,result)
        if path == "/api/driver/profile":
            if user["role"] != "driver": return self.send_json(403,{"error":"Área exclusiva do motorista."})
            with db() as con: return self.send_json(200,driver_dict(con,user["id"]))
        if path == "/api/driver/offers":
            if user["role"] != "driver": return self.send_json(403,{"error":"Área exclusiva do motorista."})
            with db() as con:
                rows=con.execute("SELECT * FROM rides WHERE status='searching' ORDER BY created_at DESC LIMIT 30").fetchall()
                return self.send_json(200,[ride_dict(con,r) for r in rows])
        if path == "/api/driver/earnings":
            if user["role"] != "driver": return self.send_json(403,{"error":"Área exclusiva do motorista."})
            with db() as con:
                row=con.execute("SELECT COUNT(*) count,COALESCE(SUM(fare),0) gross FROM rides WHERE driver_id=? AND status='finished'",(user["id"],)).fetchone()
                config=con.execute("SELECT commission FROM fare_config WHERE id=1").fetchone()
                rides=con.execute("SELECT id,origin,destination,fare,finished_at FROM rides WHERE driver_id=? AND status='finished' ORDER BY finished_at DESC LIMIT 30",(user["id"],)).fetchall()
                return self.send_json(200,{"rides":row["count"],"gross":round(row["gross"],2),"commission":config[0],"net":round(row["gross"]*(1-config[0]),2),"history":[dict(x) for x in rides]})
        if path == "/api/admin/summary": return self.admin_summary(user)
        if path == "/api/admin/users": return self.admin_users(user)
        if path == "/api/admin/drivers": return self.admin_drivers(user)
        if path == "/api/admin/rides": return self.admin_rides(user)
        if path == "/api/admin/incidents": return self.admin_incidents(user)
        if path == "/api/admin/fare-config":
            if user["role"]!="admin": return self.send_json(403,{"error":"Área exclusiva da administração."})
            with db() as con: row=con.execute("SELECT base,per_km,per_min,minimum,commission,updated_at FROM fare_config WHERE id=1").fetchone()
            return self.send_json(200,dict(row))
        return self.send_json(404,{"error":"Rota não encontrada."})

    def api_post(self, path):
        data=self.body()
        if path == "/api/auth/signup": return self.signup(data)
        if path == "/api/auth/login": return self.login(data)
        if path == "/api/quote":
            origin=clean(data.get("origin"),"origem"); destination=clean(data.get("destination"),"destino"); return self.send_json(200,quote(origin,destination))
        if path == "/api/rides": return self.create_ride(data)
        if path == "/api/driver/online": return self.driver_online(data)
        if path == "/api/driver/documents": return self.driver_document(data)
        if path == "/api/support/incidents": return self.incident(data)
        m=re.fullmatch(r"/api/rides/([A-Za-z0-9_-]+)/(accept|start|finish|cancel|share|emergency|rate)",path)
        if m: return self.ride_action(m.group(1),m.group(2),data)
        m=re.fullmatch(r"/api/admin/drivers/(\d+)/(approve|suspend)",path)
        if m: return self.admin_driver_action(int(m.group(1)),m.group(2))
        m=re.fullmatch(r"/api/admin/users/(\d+)/suspend",path)
        if m: return self.admin_user_suspend(int(m.group(1)))
        m=re.fullmatch(r"/api/admin/incidents/(\d+)/resolve",path)
        if m: return self.admin_resolve_incident(int(m.group(1)))
        if path == "/api/admin/fare-config": return self.admin_fare(data)
        return self.send_json(404,{"error":"Rota não encontrada."})

    def signup(self,data):
        name=clean(data.get("name"),"nome",max_len=100); phone=clean(data.get("phone"),"telefone",max_len=30); email=clean(data.get("email"),"e-mail",max_len=160).lower(); password=clean(data.get("password"),"senha",max_len=100)
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email): raise ValueError("Informe um e-mail válido.")
        if len(re.sub(r"\D", "", phone)) < 8: raise ValueError("Informe um telefone válido.")
        if len(password)<6: raise ValueError("A senha deve ter pelo menos 6 caracteres.")
        role=data.get("role","passenger")
        if role not in ("passenger","driver"): raise ValueError("Perfil inválido.")
        with DB_LOCK,db() as con:
            cur=con.execute("INSERT INTO users(name,phone,email,password_hash,role,status,created_at) VALUES(?,?,?,?,?,?,?)",(name,phone,email,hash_password(password),role,"active",now())); uid=cur.lastrowid
            if role=="driver": con.execute("INSERT INTO driver_profiles(user_id,updated_at) VALUES(?,?)",(uid,now()))
            token=secrets.token_urlsafe(32); con.execute("INSERT INTO sessions(token,user_id,created_at) VALUES(?,?,?)",(token,uid,now())); row=con.execute("SELECT * FROM users WHERE id=?",(uid,)).fetchone()
        return self.send_json(201,{"token":token,"user":user_dict(row),"message":"Conta criada. Motoristas aguardam aprovação documental." if role=="driver" else "Conta criada."})

    def login(self,data):
        identity=clean(data.get("identity") or data.get("email") or data.get("phone"),"e-mail ou telefone",max_len=160); password=clean(data.get("password"),"senha",max_len=100)
        with DB_LOCK,db() as con:
            row=con.execute("SELECT * FROM users WHERE lower(email)=lower(?) OR phone=?",(identity,identity)).fetchone()
            if not row or not verify_password(password,row["password_hash"]): raise PermissionError("Credenciais inválidas.")
            if row["status"]!="active": raise PermissionError("Esta conta está suspensa.")
            token=secrets.token_urlsafe(32); con.execute("INSERT INTO sessions(token,user_id,created_at) VALUES(?,?,?)",(token,row["id"],now()))
        return self.send_json(200,{"token":token,"user":user_dict(row)})

    def create_ride(self,data):
        user=self.auth(["passenger"]); origin=clean(data.get("origin"),"origem"); destination=clean(data.get("destination"),"destino"); payment=data.get("paymentMethod","Pix")
        if payment not in ("Pix","Cartão","Dinheiro"): raise ValueError("Forma de pagamento inválida.")
        q=quote(origin,destination); ride_id=secrets.token_hex(6)
        with DB_LOCK,db() as con:
            active=con.execute("SELECT id FROM rides WHERE passenger_id=? AND status IN ('searching','accepted','in_progress')",(user["id"],)).fetchone()
            if active: return self.send_json(409,{"error":"Você já possui uma corrida ativa.","rideId":active[0]})
            con.execute("INSERT INTO rides(id,passenger_id,origin,destination,payment_method,distance_km,duration_min,fare,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",(ride_id,user["id"],origin,destination,payment,q["distanceKm"],q["durationMin"],q["fare"],"searching",now()))
            con.execute("INSERT INTO ride_events(ride_id,actor_id,event,detail,created_at) VALUES(?,?,?,?,?)",(ride_id,user["id"],"requested","Solicitação criada",now())); row=con.execute("SELECT * FROM rides WHERE id=?",(ride_id,)).fetchone()
        with db() as con: return self.send_json(201,ride_dict(con,row))

    def driver_online(self,data):
        user=self.auth(["driver"]); online=bool(data.get("online"))
        with DB_LOCK,db() as con:
            profile=con.execute("SELECT approval_status FROM driver_profiles WHERE user_id=?",(user["id"],)).fetchone()
            if online and profile[0]!="approved": return self.send_json(409,{"error":"Seu cadastro ainda não foi aprovado pela administração."})
            con.execute("UPDATE driver_profiles SET online=?,updated_at=? WHERE user_id=?",(int(online),now(),user["id"]))
            return self.send_json(200,driver_dict(con,user["id"]))

    def driver_document(self,data):
        user=self.auth(["driver"]); kind=clean(data.get("kind"),"tipo do documento",max_len=60); filename=clean(data.get("filename") or "arquivo informado", "arquivo", max_len=120)
        if kind not in ("CNH + EAR","Documento da moto","Comprovante/seguro","Foto do veículo"): raise ValueError("Tipo de documento inválido.")
        with DB_LOCK,db() as con:
            con.execute("INSERT INTO documents(driver_id,kind,filename,status,submitted_at) VALUES(?,?,?,?,?)",(user["id"],kind,filename,"pending",now())); return self.send_json(201,{"ok":True,"message":"Documento enviado para análise.","driver":driver_dict(con,user["id"])})

    def ride_action(self,ride_id,action,data):
        user=self.auth();
        with DB_LOCK,db() as con:
            ride=con.execute("SELECT * FROM rides WHERE id=?",(ride_id,)).fetchone()
            if not ride: return self.send_json(404,{"error":"Corrida não encontrada."})
            if action in TRANSITIONS:
                if action=="accept":
                    if user["role"]!="driver": return self.send_json(403,{"error":"Somente motorista pode aceitar."})
                    p=con.execute("SELECT approval_status,online FROM driver_profiles WHERE user_id=?",(user["id"],)).fetchone()
                    if not p or p["approval_status"]!="approved" or not p["online"]: return self.send_json(409,{"error":"Motorista precisa estar aprovado e online."})
                    if ride["status"]!="searching": return self.send_json(409,{"error":"Esta corrida já recebeu outra atualização."})
                    con.execute("UPDATE rides SET driver_id=?,status='accepted',accepted_at=? WHERE id=?",(user["id"],now(),ride_id)); detail="Motorista aceitou a corrida"
                else:
                    allowed, target=TRANSITIONS[action]
                    if ride["status"] not in allowed: return self.send_json(409,{"error":"Transição de status inválida.","status":ride["status"]})
                    if user["role"] not in ("admin","driver","passenger") or (user["role"]=="passenger" and ride["passenger_id"]!=user["id"]) or (user["role"]=="driver" and ride["driver_id"]!=user["id"]): return self.send_json(403,{"error":"Você não participa desta corrida."})
                    fields={"start":"started_at","finish":"finished_at","cancel":"cancelled_at"}; con.execute(f"UPDATE rides SET status=?,{fields[action]}=? WHERE id=?",(target,now(),ride_id)); detail={"start":"Corrida iniciada","finish":"Corrida finalizada","cancel":"Corrida cancelada"}[action]
                con.execute("INSERT INTO ride_events(ride_id,actor_id,event,detail,created_at) VALUES(?,?,?,?,?)",(ride_id,user["id"],action,detail,now()))
            elif action in ("share","emergency"):
                if user["role"] not in ("admin",) and user["id"] not in (ride["passenger_id"],ride["driver_id"]): return self.send_json(403,{"error":"Você não participa desta corrida."})
                typ="emergency" if action=="emergency" else "share"; desc=clean(data.get("description") or ("Acionamento de emergência solicitado" if typ=="emergency" else "Compartilhamento solicitado"),"descrição")
                con.execute("INSERT INTO incidents(ride_id,reporter_id,type,description,created_at) VALUES(?,?,?,?,?)",(ride_id,user["id"],typ,desc,now())); con.execute("INSERT INTO ride_events(ride_id,actor_id,event,detail,created_at) VALUES(?,?,?,?,?)",(ride_id,user["id"],typ,desc,now()));
                if typ=="emergency": return self.send_json(201,{"ok":True,"message":"Alerta registrado. Em produção, acione também o serviço público de emergência.","placeholder":True})
                return self.send_json(201,{"ok":True,"message":"Link de compartilhamento placeholder registrado.","placeholder":True,"rideId":ride_id})
            elif action=="rate":
                if user["role"]!="passenger" or ride["passenger_id"]!=user["id"] or ride["status"]!="finished": return self.send_json(409,{"error":"Só é possível avaliar uma corrida finalizada própria."})
                try: score=int(data.get("score"))
                except: raise ValueError("Informe uma nota de 1 a 5.")
                if score<1 or score>5: raise ValueError("Informe uma nota de 1 a 5.")
                con.execute("INSERT INTO ratings(ride_id,passenger_id,driver_id,score,comment,created_at) VALUES(?,?,?,?,?,?)",(ride_id,user["id"],ride["driver_id"],score,clean(data.get("comment"),"comentário",False,500),now())); con.execute("INSERT INTO ride_events(ride_id,actor_id,event,detail,created_at) VALUES(?,?,?,?,?)",(ride_id,user["id"],"rated",f"Nota {score}/5",now()))
            row=con.execute("SELECT * FROM rides WHERE id=?",(ride_id,)).fetchone(); result=ride_dict(con,row)
        return self.send_json(200,result)

    def incident(self,data):
        user=self.auth(); ride_id=data.get("rideId"); typ=clean(data.get("type") or "support","tipo"); description=clean(data.get("description"),"descrição",max_len=1000)
        with DB_LOCK,db() as con: cur=con.execute("INSERT INTO incidents(ride_id,reporter_id,type,description,created_at) VALUES(?,?,?,?,?)",(ride_id,user["id"],typ,description,now())); return self.send_json(201,{"id":cur.lastrowid,"status":"open","message":"Chamado registrado para a equipe de suporte."})

    def admin_guard(self,user):
        if user["role"]!="admin": raise PermissionError("Área exclusiva da administração.")

    def admin_summary(self,user):
        self.admin_guard(user)
        with db() as con:
            def n(q): return con.execute(q).fetchone()[0]
            return self.send_json(200,{"users":n("SELECT COUNT(*) FROM users WHERE role='passenger'"),"drivers":n("SELECT COUNT(*) FROM users WHERE role='driver'"),"pendingDrivers":n("SELECT COUNT(*) FROM driver_profiles WHERE approval_status='pending'"),"activeRides":n("SELECT COUNT(*) FROM rides WHERE status IN ('searching','accepted','in_progress')"),"finishedRides":n("SELECT COUNT(*) FROM rides WHERE status='finished'"),"openIncidents":n("SELECT COUNT(*) FROM incidents WHERE status='open'")})

    def admin_users(self,user):
        self.admin_guard(user); qs=parse_qs(urlparse(self.path).query); role=qs.get("role",[None])[0]
        with db() as con:
            rows=con.execute("SELECT id,name,phone,email,role,status,created_at FROM users WHERE (? IS NULL OR role=?) ORDER BY id DESC",(role,role)).fetchall(); return self.send_json(200,[user_dict(x) for x in rows])

    def admin_drivers(self,user):
        self.admin_guard(user)
        with db() as con: rows=con.execute("SELECT id FROM users WHERE role='driver' ORDER BY id DESC").fetchall(); return self.send_json(200,[driver_dict(con,x[0]) for x in rows])

    def admin_rides(self,user):
        self.admin_guard(user)
        with db() as con: rows=con.execute("SELECT * FROM rides ORDER BY created_at DESC LIMIT 100").fetchall(); return self.send_json(200,[ride_dict(con,x) for x in rows])

    def admin_incidents(self,user):
        self.admin_guard(user)
        with db() as con: rows=con.execute("SELECT i.*,u.name reporter FROM incidents i JOIN users u ON u.id=i.reporter_id ORDER BY i.created_at DESC").fetchall(); return self.send_json(200,[dict(x) for x in rows])

    def admin_driver_action(self,driver_id,action):
        user=self.auth(["admin"]); status="approved" if action=="approve" else "suspended"
        with DB_LOCK,db() as con:
            if not con.execute("SELECT id FROM users WHERE id=? AND role='driver'",(driver_id,)).fetchone(): return self.send_json(404,{"error":"Motorista não encontrado."})
            con.execute("UPDATE driver_profiles SET approval_status=?,online=0,updated_at=? WHERE user_id=?",(status,now(),driver_id)); return self.send_json(200,{"ok":True,"approvalStatus":status})

    def admin_user_suspend(self,user_id):
        admin=self.auth(["admin"])
        with DB_LOCK,db() as con: con.execute("UPDATE users SET status='suspended' WHERE id=? AND id!=?",(user_id,admin["id"])); return self.send_json(200,{"ok":True})

    def admin_resolve_incident(self,incident_id):
        self.auth(["admin"])
        with DB_LOCK,db() as con: con.execute("UPDATE incidents SET status='resolved',resolved_at=? WHERE id=?",(now(),incident_id)); return self.send_json(200,{"ok":True,"status":"resolved"})

    def admin_fare(self,data):
        self.auth(["admin"])
        try: values={k:float(data[k]) for k in ("base","per_km","per_min","minimum","commission")}
        except (KeyError,ValueError): raise ValueError("Informe todos os valores da tarifa.")
        if values["commission"]<0 or values["commission"]>=1 or min(values.values())<0: raise ValueError("Valores de tarifa inválidos.")
        with DB_LOCK,db() as con: con.execute("UPDATE fare_config SET base=?,per_km=?,per_min=?,minimum=?,commission=?,updated_at=? WHERE id=1",(*[values[k] for k in ("base","per_km","per_min","minimum","commission")],now()))
        return self.send_json(200,{"ok":True,"message":"Configuração de tarifa atualizada."})

    def log_message(self,*args): pass


if __name__ == "__main__":
    init_db()
    print(f"MotoJá MVP rodando em http://localhost:{PORT}")
    ThreadingHTTPServer(("0.0.0.0",PORT),Handler).serve_forever()
