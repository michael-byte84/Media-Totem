import datetime
import csv
import os
import shutil
from fastapi import FastAPI, Depends, Form, UploadFile, File, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import io
import json

# =====================================================================
# CONFIGURAZIONE DATABASE E CARTELLE MEDIA
# =====================================================================
DATABASE_URL = "sqlite:///./media_totem.db"
engine_db = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_db)
Base = declarative_base()

MEDIA_DIR = "static/uploads"
os.makedirs(MEDIA_DIR, exist_ok=True)

class ImpostazioniMedia(Base):
    __tablename__ = "impostazioni_media"
    id = Column(Integer, primary_key=True)
    chiave = Column(String, unique=True)
    valore = Column(String)

class ContenutoMultimediale(Base):
    __tablename__ = "contenuti_multimediali"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome_file = Column(String)  
    tipo_file = Column(String)  # 'video', 'immagine', 'youtube', 'googledrive', 'sito'
    ordine = Column(Integer, default=0)

class NotiziaIstituzionale(Base):
    __tablename__ = "notizie_istituzionali"
    id = Column(Integer, primary_key=True, autoincrement=True)
    titolo = Column(String, nullable=False)
    testo = Column(Text, nullable=True)
    data_creazione = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine_db)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# =====================================================================
# INIZIALIZZAZIONE FASTAPI E ROTTE DI REINDIRIZZAMENTO
# =====================================================================
app = FastAPI()

@app.get("/")
def home_redirect():
    return RedirectResponse(url="/login", status_code=303)

app.mount("/static", StaticFiles(directory="static"), name="static")

# =====================================================================
# STILI CSS GENERALI (DESIGNERS ITALIA)
# =====================================================================
STILE_ITALIA = """
<link href="https://fonts.googleapis.com/css2?family=Titillium+Web:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
    :root { 
        --blue-italia: #0066cc; 
        --blue-dark: #00264d; 
        --blue-light: #f0f6fc;
        --blue-hover: #0052a3;
        --gray-bg: #f4f5f7; 
        --text-dark: #1c2024;
        --success: #008758; 
        --error: #c52d3a; 
        --border: #d2d6da;
        --warning: #ffab00;
    }
    body { 
        font-family: 'Titillium Web', sans-serif; 
        background-color: var(--gray-bg); 
        margin: 0; 
        padding: 0; 
        color: var(--text-dark); 
        width: 100vw;
        height: 100vh;
    }
    .navbar { background: var(--blue-italia); color: white; padding: 15px 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); display: flex; justify-content: space-between; align-items: center; }
    .navbar h1 { margin: 0; font-size: 22px; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; }
    .container { max-width: 1000px; margin: 20px auto; padding: 0 15px; padding-bottom: 60px; }
    .card { background: white; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); padding: 20px; border-top: 4px solid var(--blue-italia); margin-bottom: 15px; }
    .card h2 { margin-top: 0; color: var(--blue-dark); font-size: 19px; border-bottom: 1px solid #ddd; padding-bottom: 8px; text-transform: uppercase; font-weight: 600; }
    label { font-weight: 600; display: block; margin-bottom: 4px; color: var(--blue-dark); margin-top: 10px; }
    select, input, textarea { width: 100%; padding: 8px; border: 1px solid var(--border); border-radius: 4px; font-size: 15px; box-sizing: border-box; background-color: #fff; font-family: inherit; }
    .btn { background: var(--blue-italia); color: white; border: none; padding: 10px 20px; border-radius: 4px; font-weight: 600; cursor: pointer; text-transform: uppercase; font-size: 12px; transition: 0.2s; text-decoration: none; display: inline-block; }
    .btn:hover { background: var(--blue-hover); }
    .btn-danger { background: var(--error); }
    .btn-danger:hover { background: #96222b; }
    .btn-success { background: var(--success); }
    .alert { background: #d1e7dd; color: #0f5132; padding: 12px; border-radius: 4px; border: 1px solid #badbcc; font-weight: 600; margin-bottom: 15px; }
    table { width: 100%; border-collapse: collapse; margin-top: 10px; background: white; }
    th { background: var(--blue-light); color: var(--blue-dark); text-align: left; padding: 10px; border-bottom: 2px solid var(--border); font-size: 13px; text-transform: uppercase; }
    td { padding: 10px 12px; border-bottom: 1px solid #eee; font-size: 15px; max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    
    .sortable-row { cursor: grab; transition: background 0.15s; }
    .sortable-row:active { cursor: grabbing; background: #e6f2ff !important; }
    .sortable-ghost { opacity: 0.4; background: #0066cc !important; color: white !important; }
    .drag-handle { color: #888; font-weight: bold; padding-right: 10px; cursor: grab; }
</style>
"""

# =====================================================================
# GESTIONE ACCESSI
# =====================================================================
def utente_autenticato(request: Request) -> bool:
    cookie = request.cookies.get("totem_session")
    return cookie == "autenticato_media_admin"

def get_info_scuola(db: Session):
    nome = db.query(ImpostazioniMedia).filter(ImpostazioniMedia.chiave == "nome_scuola").first()
    pwd = db.query(ImpostazioniMedia).filter(ImpostazioniMedia.chiave == "password_istituto").first()
    return nome.valore if nome else None, pwd.valore if pwd else None

@app.get("/login", response_class=HTMLResponse)
def pagina_login(request: Request, error: str = None, db: Session = Depends(get_db)):
    nome_scuola, password_salvata = get_info_scuola(db)
    
    if not nome_scuola or not password_salvata:
        return f"""
        <!DOCTYPE html><html><head>{STILE_ITALIA}<title>Sosty Media - Configurazione</title>
        <style>
            body {{ display: flex; justify-content: center; align-items: center; height: 100vh; background-color: var(--gray-bg); }}
            .card-onboarding {{ background: white; padding: 30px; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); width: 100%; max-width: 450px; border-top: 4px solid var(--success); }}
            .card-onboarding h2 {{ margin-top: 0; color: var(--blue-dark); font-size: 22px; border-bottom: 1px solid #ddd; padding-bottom: 8px; text-transform: uppercase; font-weight: 600; text-align: center; }}
            .card-onboarding p {{ font-size: 15px; color: #555; text-align: center; margin-bottom: 20px; line-height: 1.5; }}
            .card-onboarding input {{ margin-bottom: 15px; margin-top: 5px; }}
        </style>
        </head><body>
            <div class="card-onboarding">
                <h2>Iscrizione d'Istituto</h2>
                <p>Benvenuto in Sosty Media. Configura la denominazione ufficiale della scuola e crea la chiave d'accesso per attivare il palinsesto del monitor.</p>
                <form action="/setup-scuola" method="post">
                    <label>Nome dell'Istituto Scolastico:</label>
                    <input type="text" name="nome_scuola" placeholder="Inserisci nome scuola" required>
                    
                    <label>Crea Password Amministrativa (Gestione):</label>
                    <input type="password" name="nuova_password" placeholder="Scegli una password" required>
                    
                    <button type="submit" class="btn btn-success" style="width:100%; padding:12px; margin-top:10px; font-size:13px;">Attiva Hub Multimediale</button>
                </form>
            </div>
        </body></html>
        """
        
    msg_errore = f"<div class='alert' style='background:var(--error); color:white;'>Attenzione: {error}</div>" if error else ""
    return f"""
    <!DOCTYPE html><html><head>{STILE_ITALIA}<title>Sosty Media - Login</title>
    <style>
        body {{ display: flex; justify-content: center; align-items: center; height: 100vh; background-color: var(--gray-bg); }}
        .card-login {{ background: white; padding: 35px; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); width: 100%; max-width: 400px; border-top: 4px solid var(--blue-italia); }}
        .card-login h2 {{ margin-top: 0; color: var(--blue-dark); font-size: 20px; text-align: center; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 5px; }}
        .card-login h3 {{ text-align: center; color: var(--blue-italia); font-size: 13px; margin-top: 0; margin-bottom: 25px; font-weight: 600; letter-spacing: 0.5px; }}
        .card-login input {{ margin-bottom: 20px; margin-top: 5px; }}
    </style>
    </head><body>
        <div class="card-login">
            <h2>{nome_scuola.upper()}</h2>
            <h3>PANNELLO DI CONTROLLO MEDIA</h3>
            {msg_errore}
            <form action="/login" method="post">
                <label>Password di Gestione Istituto:</label>
                <input type="password" name="password" placeholder="Inserisci la password" required>
                <button type="submit" class="btn" style="width:100%; padding:12px; font-size:13px;">Accedi al Pannello</button>
            </form>
        </div>
    </body></html>
    """

@app.post("/setup-scuola")
def esegui_setup_scuola(nome_scuola: str = Form(...), nuova_password: str = Form(...), db: Session = Depends(get_db)):
    esiste_nome = db.query(ImpostazioniMedia).filter(ImpostazioniMedia.chiave == "nome_scuola").first()
    if not esiste_nome:
        db.add(ImpostazioniMedia(chiave="nome_scuola", valore=nome_scuola.strip()))
        db.add(ImpostazioniMedia(chiave="password_istituto", valore=nuova_password.strip()))
        db.commit()
    
    response = RedirectResponse(url="/admin", status_code=303)
    response.set_cookie(key="totem_session", value="autenticato_media_admin", httponly=True, samesite="lax")
    return response

@app.post("/login")
def esegui_login(password: str = Form(...), db: Session = Depends(get_db)):
    _, password_corretta = get_info_scuola(db)
    if password_corretta and password == password_corretta:
        response = RedirectResponse(url="/admin", status_code=303)
        response.set_cookie(key="totem_session", value="autenticato_media_admin", httponly=True, samesite="lax")
        return response
    return RedirectResponse(url="/login?error=Password+errata", status_code=303)

@app.get("/logout")
def esegui_logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("totem_session")
    return response

# =====================================================================
# AREA AMMINISTRATIVA (GESTIONE ATTIVITÀ)
# =====================================================================
@app.get("/admin", response_class=HTMLResponse)
def area_admin(request: Request, msg: str = None, db: Session = Depends(get_db)):
    if not utente_autenticato(request): return RedirectResponse(url="/login", status_code=303)
    nome_scuola, _ = get_info_scuola(db)
    
    playlist = db.query(ContenutoMultimediale).order_by(ContenutoMultimediale.ordine.asc()).all()
    righe_playlist = ""
    for item in playlist:
        righe_playlist += f"""
        <tr class="sortable-row" data-id="{item.id}">
            <td><span class="drag-handle">☰</span> {item.id}</td>
            <td title="{item.nome_file}">{item.nome_file}</td>
            <td><strong>{item.tipo_file.upper()}</strong></td>
            <td><a href="/elimina-media?id={item.id}" class="btn btn-danger" style="font-size:11px; padding:4px 8px;">Rimuovi</a></td>
        </tr>
        """

    notizie_salvate = db.query(NotiziaIstituzionale).order_by(NotiziaIstituzionale.data_creazione.desc()).all()
    righe_notizie = ""
    for n in notizie_salvate:
        righe_notizie += f"""
        <tr>
            <td>{n.id}</td>
            <td><strong>{n.titolo}</strong></td>
            <td title="{n.testo or ''}">{n.testo or ''}</td>
            <td><a href="/elimina-notizia?id={n.id}" class="btn btn-danger" style="font-size:11px; padding:4px 8px;">Cancella</a></td>
        </tr>
        """

    banner = f"<div class='alert'>{msg}</div>" if msg else ""
    return f"""
    <!DOCTYPE html><html><head>{STILE_ITALIA}
    <title>Sosty Media - Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Sortable/1.15.0/Sortable.min.js"></script>
    </head>
    <body>
        <div class="navbar">
            <h1>Sosty Media - {nome_scuola.upper()}</h1>
            <a href="/logout" class="btn btn-danger">Disconnetti</a>
        </div>
        <div class="container">
            {banner}
            
            <div class="card" style="border-top-color: var(--success);">
                <h2>📰 Bacheca Notizie (Stile WordPress Interno)</h2>
                <form action="/scrivi-notizia" method="post">
                    <label>Titolo della Notizia / Avviso:</label>
                    <input type="text" name="titolo" placeholder="Esempio: Circolare n.124 - Assemblea d'Istituto..." required>
                    <label>Testo aggiuntivo opzionale:</label>
                    <textarea name="testo" rows="2"></textarea>
                    <br><br>
                    <button type="submit" class="btn btn-success">Pubblica Notizia sul Totem</button>
                </form>
                <br>
                <table>
                    <thead><tr><th>ID</th><th>Titolo</th><th>Dettagli</th><th>Azione</th></tr></thead>
                    <tbody>{righe_notizie if righe_notizie else "<tr><td colspan='4' style='text-align:center; color:gray;'>Nessuna notizia scritta.</td></tr>"}</tbody>
                </table>
            </div>
            
            <div class="card">
                <h2>🎬 Incolla Link Esterno (YouTube, Google Drive o Sito Web)</h2>
                <form action="/aggiungi-link" method="post">
                    <label>Incolla qui l'URL completo della risorsa:</label>
                    <input type="url" name="url_esterno" placeholder="https://..." required>
                    <br><br>
                    <button type="submit" class="btn" style="background:#ffab00; color:#00264d;">Aggiungi Link Web</button>
                </form>
            </div>
            
            <div class="card">
                <h2>📁 Carica File Locale (Solo MP4 orizzontali o Immagini)</h2>
                <form action="/carica-file" method="post" enctype="multipart/form-data">
                    <label>Seleziona File (.mp4 / .jpg / .png):</label>
                    <input type="file" name="file" accept="video/mp4, image/jpeg, image/png" required>
                    <br><br>
                    <button type="submit" class="btn">Carica File</button>
                </form>
            </div>

            <div class="card" style="border-top-color: var(--warning);">
                <h2>📺 Playlist File e Streaming (Trascina le righe per ordinare ↕)</h2>
                <div id="reorder-badge" style="display:none; background:#d1e7dd; color:#0f5132; padding:10px; border-radius:4px; margin-bottom:10px; font-weight:bold; font-size:13px;">✓ Ordinamento salvato con successo!</div>
                <table>
                    <thead><tr><th>ID</th><th>Sorgente / File</th><th>Tipo Riproduzione</th><th>Azione</th></tr></thead>
                    <tbody id="playlist-sortable-body">{righe_playlist if righe_playlist else "<tr><td colspan='4' style='text-align:center; color:gray;'>Nessun contenuto multimediale caricato.</td></tr>"}</tbody>
                </table>
                <br>
                <a href="/totem" target="_blank" class="btn" style="background:var(--blue-dark); color:white; width:100%; text-align:center; box-sizing:border-box; font-weight:700;">Apri Schermo Intero Totem Metropolitana Scuola</a>
            </div>
        </div>

        <script>
            const el = document.getElementById('playlist-sortable-body');
            if (el && el.children.length > 1 && !el.innerText.includes("Nessun contenuto")) {{
                Sortable.create(el, {{
                    animation: 150,
                    ghostClass: 'sortable-ghost',
                    handle: '.drag-handle',
                    onEnd: async function () {{
                        const righe = el.querySelectorAll('.sortable-row');
                        let ordineIds = [];
                        righe.forEach(riga => {{ ordineIds.push(parseInt(riga.getAttribute('data-id'))); }});

                        try {{
                            const response = await fetch('/api/salva-ordine-palinsesto', {{
                                method: 'POST',
                                headers: {{ 'Content-Type': 'application/json' }},
                                body: JSON.stringify({{ ids: ordineIds }})
                            }});
                            if (response.ok) {{
                                const badge = document.getElementById('reorder-badge');
                                badge.style.display = 'block';
                                setTimeout(() => {{ badge.style.display = 'none'; }}, 2500);
                            }}
                        }} catch (err) {{ console.error("Errore ordinamento", err); }}
                    }}
                }});
            }}
        </script>
    </body></html>
    """

# =====================================================================
# ROTTE INTERNE DEI SERVIZI
# =====================================================================
@app.post("/api/salva-ordine-palinsesto")
async def salva_ordine_palinsesto(request: Request, db: Session = Depends(get_db)):
    if not utente_autenticato(request): return JSONResponse(status_code=403, content={"error": "Non autorizzato"})
    data = await request.json()
    lista_ids = data.get("ids", [])
    for indice, media_id in enumerate(lista_ids):
        item = db.query(ContenutoMultimediale).filter(ContenutoMultimediale.id == media_id).first()
        if item: item.ordine = indice
    db.commit()
    return {"status": "success"}

@app.post("/scrivi-notizia")
def scrivi_notizia(request: Request, titolo: str = Form(...), testo: str = Form(None), db: Session = Depends(get_db)):
    if not utente_autenticato(request): return RedirectResponse(url="/login", status_code=303)
    db.add(NotiziaIstituzionale(titolo=titolo.strip(), testo=testo.strip() if testo else None))
    db.commit()
    return RedirectResponse(url="/admin?msg=Notizia+inserita+in+bacheca.", status_code=303)

@app.get("/elimina-notizia")
def elimina_notizia(request: Request, id: int, db: Session = Depends(get_db)):
    if not utente_autenticato(request): return RedirectResponse(url="/login", status_code=303)
    n = db.query(NotiziaIstituzionale).filter(NotiziaIstituzionale.id == id).first()
    if n:
        db.delete(n)
        db.commit()
    return RedirectResponse(url="/admin?msg=Notizia+rimossa.", status_code=303)

@app.post("/aggiungi-link")
def aggiungi_link(request: Request, url_esterno: str = Form(...), db: Session = Depends(get_db)):
    if not utente_autenticato(request): return RedirectResponse(url="/login", status_code=303)
    url_clean = url_esterno.strip()
    tipo = "sito"  
    if "youtube.com" in url_clean or "youtu.be" in url_clean: tipo = "youtube"
    elif "drive.google.com" in url_clean: tipo = "googledrive"
    elif url_clean.lower().endswith(".mp4"): tipo = "video"
    
    max_ordine = db.query(ContenutoMultimediale).order_by(ContenutoMultimediale.ordine.desc()).first()
    nuovo_ordine = (max_ordine.ordine + 1) if max_ordine else 0
    
    db.add(ContenutoMultimediale(nome_file=url_clean, tipo_file=tipo, ordine=nuovo_ordine))
    db.commit()
    return RedirectResponse(url="/admin?msg=Link+aggiunto.", status_code=303)

@app.post("/carica-file")
async def carica_file(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not utente_autenticato(request): return RedirectResponse(url="/login", status_code=303)
    file_path = os.path.join(MEDIA_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    tipo = "immagine"
    if file.filename.lower().endswith(".mp4"): tipo = "video"
    
    max_ordine = db.query(ContenutoMultimediale).order_by(ContenutoMultimediale.ordine.desc()).first()
    nuovo_ordine = (max_ordine.ordine + 1) if max_ordine else 0
    
    db.add(ContenutoMultimediale(nome_file=file.filename, tipo_file=tipo, ordine=nuovo_ordine))
    db.commit()
    return RedirectResponse(url="/admin?msg=File+caricato.", status_code=303)

@app.get("/elimina-media")
def micro_elimina_media(request: Request, id: int, db: Session = Depends(get_db)):
    if not utente_autenticato(request): return RedirectResponse(url="/login", status_code=303)
    item = db.query(ContenutoMultimediale).filter(ContenutoMultimediale.id == id).first()
    if item:
        if not item.nome_file.startswith("http"):
            try: os.remove(os.path.join(MEDIA_DIR, item.nome_file))
            except: pass
        db.delete(item)
        db.commit()
    return RedirectResponse(url="/admin?msg=Contenuto+rimosso.", status_code=303)

# =====================================================================
# VISTA FRONT-END: MONITOR INTERO CON ATTIVATORE AUTOMATICO INTEGRATO
# =====================================================================
@app.get("/api/playlist")
def api_playlist(db: Session = Depends(get_db)):
    contents = db.query(ContenutoMultimediale).order_by(ContenutoMultimediale.ordine.asc()).all()
    return [{"url": c.nome_file if c.nome_file.startswith("http") else f"/static/uploads/{c.nome_file}", "tipo": c.tipo_file} for c in contents]

@app.get("/totem", response_class=HTMLResponse)
def vista_totem(db: Session = Depends(get_db)):
    nome_scuola, _ = get_info_scuola(db)
    if not nome_scuola: return RedirectResponse(url="/login", status_code=303)
    
    notizie_db = db.query(NotiziaIstituzionale).order_by(NotiziaIstituzionale.data_creazione.desc()).all()
    blocchi_testo = []
    for n in notizie_db:
        stringa_notizia = n.titolo.upper()
        if n.testo: stringa_notizia += f" ({n.testo.upper()})"
        blocchi_testo.append(stringa_notizia)
        
    if blocchi_testo:
        news_string = f"*** CIRCOLARI E NEWS D'ISTITUTO: " + "  •—•  ".join(blocchi_testo) + " ***"
    else:
        news_string = f"*** BENVENUTI NELL'HUB INFORMATIVO DI {nome_scuola.upper()} ***"

    return f"""
    <!DOCTYPE html><html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sosty Media - Totem Monitor</title>
        {STILE_ITALIA}
        <style>
            html, body {{ 
                height: 100%; margin: 0; padding: 0; background: #000000; 
                overflow: hidden; display: flex; flex-direction: column; 
                width: 100vw; height: 100vh; position: relative;
            }}
            
            /* 🌟 PULSANTE COPERTURA INVISIBILE DI SBLOCCO COMPLETO */
            #totem-click-trigger {{
                position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
                background: rgba(0, 0, 0, 0.9); color: #ffffff; z-index: 99999;
                display: flex; flex-direction: column; justify-content: center; align-items: center;
                cursor: pointer; text-align: center; box-sizing: border-box; padding: 20px;
            }}
            #totem-click-trigger h2 {{ font-size: 32px; text-transform: uppercase; margin: 0 0 10px 0; color: var(--warning); letter-spacing: 1px; }}
            #totem-click-trigger p {{ font-size: 18px; margin: 0; opacity: 0.8; font-weight: 600; }}

            .totem-top-overlay {{ 
                position: absolute; top: 0; left: 0; width: 100%; 
                background: rgba(0, 38, 77, 0.85); color: white; padding: 15px 30px; 
                display: flex; justify-content: space-between; align-items: center; 
                z-index: 10; box-shadow: 0 4px 10px rgba(0,0,0,0.5); box-sizing: border-box;
            }}
            .totem-top-overlay h1 {{ margin: 0; font-size: 26px; text-transform: uppercase; letter-spacing: 1px; color: #ffffff; }}
            .totem-top-overlay p {{ margin: 0; font-size: 16px; color: var(--warning); font-weight: 600; text-transform: uppercase; }}
            
            .media-display-area {{ 
                flex-grow: 1; width: 100vw; height: calc(100vh - 60px); position: relative; 
                display: flex; justify-content: center; align-items: center; background: #000000; overflow: hidden; 
            }}
            .media-display-area video, .media-display-area img, .media-display-area iframe {{ 
                max-width: 100%; max-height: 100%; width: 100%; height: 100%; object-fit: contain; border: none; display: none; 
            }}
            
            .ticker-bottom-wrapper {{ 
                background: var(--blue-dark); color: white; height: 60px; overflow: hidden; 
                display: flex; align-items: center; z-index: 99; border-top: 4px solid var(--warning); 
                box-shadow: 0 -4px 15px rgba(0,0,0,0.5); flex-shrink: 0; width: 100vw; box-sizing: border-box;
            }}
            .ticker-header {{ background: var(--warning); color: var(--blue-dark); padding: 0 30px; height: 100%; display: flex; align-items: center; font-weight: 700; font-size: 16px; text-transform: uppercase; white-space: nowrap; z-index: 100; box-shadow: 5px 0 10px rgba(0,0,0,0.4); }}
            .ticker-scroll-container {{ width: 100%; overflow: hidden; display: flex; align-items: center; }}
            .ticker-text-movement {{ display: inline-block; white-space: nowrap; padding-left: 100%; animation: maratona-media 45s linear infinite; font-size: 22px; color: #ffffff; letter-spacing: 0.5px; }}
            @keyframes maratona-media {{ 0% {{ transform: translate3d(0, 0, 0); }} 100% {{ transform: translate3d(-100%, 0, 0); }} }}
        </style>
    </head>
    <body>

        <div id="totem-click-trigger" onclick="attivaTotemSchermoIntero()">
            <h2>{nome_scuola.upper()}</h2>
            <p>Clicca in un punto qualsiasi per lanciare il monitor a tutto schermo con audio attivo</p>
        </div>

        <div class="totem-top-overlay">
            <h1>{nome_scuola.upper()}</h1>
            <p id="live-timer">00:00:00</p>
        </div>
        <div class="media-display-area" id="display-container">
            <div id="empty-state" style="color: white; font-size: 20px; text-align: center;">In attesa di contenuti multimediali...</div>
        </div>
        <div class="ticker-bottom-wrapper">
            <div class="ticker-header">BACHECA NEWS</div>
            <div class="ticker-scroll-container">
                <div class="ticker-text-movement">{news_string}</div>
            </div>
        </div>

        <script>
            let playlist = [];
            let currentIndex = 0;
            let timerImmagine = null;
            let riproduttoreAttivo = false;

            const container = document.getElementById("display-container");
            const tempoSlideMs = 15000; 
            const tempoSitoMs = 30000;  
            const tempoYouTubeMs = 900000; 

            // 🌟 LA FUNZIONE CHE PROPAGA LO SCHERMO INTERO E SBLOCCA L'AUDIO IN AUTOMATICO
            function attivaTotemSchermoIntero() {{
                const elementoCorpo = document.documentElement;
                
                // Forza l'attivazione della modalità Kiosk Schermo Intero nativa del browser
                if (elementoCorpo.requestFullscreen) {{ elementoCorpo.requestFullscreen(); }}
                else if (elementoCorpo.mozRequestFullScreen) {{ elementoCorpo.mozRequestFullScreen(); }}
                else if (elementoCorpo.webkitRequestFullscreen) {{ elementoCorpo.webkitRequestFullscreen(); }}
                else if (elementoCorpo.msRequestFullscreen) {{ elementoCorpo.msRequestFullscreen(); }}
                
                // Distrugge la schermata nera iniziale e scopre il palinsesto sottostante
                document.getElementById("totem-click-trigger").style.display = "none";
                
                // Avvia la playlist con audio autorizzato a tutto volume
                caricaPlaylist().then(() => {{
                    if (playlist.length > 0) avviaRiproduttore();
                }});
            }}

            async function caricaPlaylist() {{
                try {{
                    const res = await fetch('/api/playlist');
                    const nuovaPlaylist = await res.json();
                    
                    if (nuovaPlaylist.length > 0) {{
                        if (JSON.stringify(playlist) !== JSON.stringify(nuovaPlaylist)) {{
                            playlist = nuovaPlaylist;
                            if (riproduttoreAttivo) {{
                                // Se l'ordine è cambiato dal drag and drop, resetta fluidamente
                                let videoCorrente = document.querySelector('video');
                                if (!videoCorrente) avviaRiproduttore();
                            }}
                        }}
                    }} else {{
                        playlist = [];
                        riproduttoreAttivo = false;
                        puliisciTimerPrecedente();
                        container.innerHTML = '<div id="empty-state" style="color: white; font-size: 20px; text-align: center;">In attesa di contenuti multimediali...</div>';
                    }}
                }} catch (err) {{ console.error("Errore sincro playlist", err); }}
            }}

            function puliisciTimerPrecedente() {{
                if (timerImmagine) {{ clearTimeout(timerImmagine); timerImmagine = null; }}
            }}

            function avviaRiproduttore() {{
                puliisciTimerPrecedente();
                if (playlist.length === 0) {{ riproduttoreAttivo = false; return; }}
                
                riproduttoreAttivo = true;
                container.innerHTML = ""; 
                const item = playlist[currentIndex];
                
                if (item.tipo === "video") {{
                    const video = document.createElement("video");
                    video.src = item.url;
                    video.autoplay = true;
                    video.muted = false; // 🔊 AUDIO SBLOCCATO
                    video.playsInline = true;
                    video.style.display = "block"; video.style.width = "100%"; video.style.height = "100%";
                    video.onended = passaAlProssimo; container.appendChild(video);
                    
                }} else if (item.tipo === "immagine") {{
                    const img = document.createElement("img");
                    img.src = item.url; img.style.display = "block"; container.appendChild(img);
                    timerImmagine = setTimeout(passaAlProssimo, tempoSlideMs);
                    
                }} else if (item.tipo === "youtube") {{
                    let videoId = "";
                    if (item.url.includes("v=")) {{
                        let parts = item.url.split("v="); videoId = parts[1].split("&")[0];
                    }} else if (item.url.includes("youtu.be/")) {{
                        let parts = item.url.split("youtu.be/"); videoId = parts[1].split("?")[0];
                    }} else {{ videoId = item.url; }}
                    
                    if(videoId) {{
                        const iframe = document.createElement("iframe");
                        // 🔊 MUTE=0 AUDIO SBLOCCATO PER DIRETTE E PLAYLIST
                        iframe.src = "https://www.youtube.com/embed/" + videoId + "?autoplay=1&mute=0&controls=0&loop=1&playlist=" + videoId;
                        iframe.style.display = "block"; iframe.style.width = "100%"; iframe.style.height = "100%";
                        container.appendChild(iframe);
                        timerImmagine = setTimeout(passaAlProssimo, tempoYouTubeMs);
                    }} else {{ passaAlProssimo(); }}
                    
                }} else if (item.tipo === "googledrive") {{
                    let driveId = "";
                    if (item.url.includes("/d/")) {{ driveId = item.url.split("/d/")[1].split("/")[0]; }}
                    else if (item.url.includes("id=")) {{ driveId = item.url.split("id=")[1].split("&")[0]; }}
                    
                    const iframe = document.createElement("iframe");
                    iframe.src = "https://drive.google.com/file/d/" + driveId + "/preview";
                    iframe.style.display = "block"; iframe.style.width = "100%"; iframe.style.height = "100%";
                    container.appendChild(iframe);
                    timerImmagine = setTimeout(passaAlProssimo, tempoSlideMs);
                    
                }} else if (item.tipo === "sito") {{
                    const iframe = document.createElement("iframe");
                    iframe.src = item.url; iframe.style.display = "block"; iframe.style.width = "100%"; iframe.style.height = "100%"; iframe.style.background = "#ffffff";
                    container.appendChild(iframe);
                    timerImmagine = setTimeout(passaAlProssimo, tempoSitoMs);
                }}
            }}

            function passaAlProssimo() {{
                if (playlist.length === 0) return;
                currentIndex = (currentIndex + 1) % playlist.length;
                avviaRiproduttore();
            }}

            function aggiornaOrologio() {{
                const d = new Date();
                document.getElementById('live-timer').innerHTML = String(d.getHours()).padStart(2, '0') + ":" + String(d.getMinutes()).padStart(2, '0') + ":" + String(d.getSeconds()).padStart(2, '0');
            }}

            aggiornaOrologio();
            setInterval(aggiornaOrologio, 1000);
            
            // Carica la playlist in background per intercettare i cambi Drag & Drop
            setInterval(caricaPlaylist, 5000);
        </script>
    </body>
    </html>
    """