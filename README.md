# Media Totem 📺

**Media Totem** è un hub multimediale leggero, autonomo e reattivo progettato per la gestione dei monitor di corridoio e dei totem informativi digitali all'interno degli istituti scolastici. 

Il sistema permette di gestire facilmente le comunicazioni quotidiane e il palinsesto video direttamente da un pannello amministrativo protetto, ispirato alle linee guida di design per la PA (*Designers Italia*).

---

## 🚀 Caratteristiche Principali

* **Bacheca News d'Istituto (Stile WordPress):** Un mini-CMS interno permanente per scrivere avvisi, circolari e comunicazioni urgenti che scorrono continuamente in un serpentone in basso sul monitor.
* **Palinsesto Multimediale Versatile:** Supporto nativo per video locali (`.mp4`), immagini delle circolari (`.jpg`, `.png`), e integrazione diretta tramite URL per lo streaming di **YouTube** (dirette o TG) e anteprime di **Google Drive**.
* **Ordinamento Drag & Drop:** Controllo totale sulla sequenza di riproduzione trascinando semplicemente le righe della playlist in tempo reale (grazie a *SortableJS*).
* **Monitor Totem "Zero-Click":** Interfaccia front-end pensata per le TV di corridoio. Include un sistema di attivazione a schermo intero assoluto che aggira i blocchi dei browser, sbloccando automaticamente anche l'audio dei video.

---

## 🛠️ Stack Tecnologico

* **Backend:** Python 3.11+, FastAPI, Uvicorn
* **Database:** SQLite con SQLAlchemy (ORM)
* **Frontend:** HTML5, CSS3 (Designers Italia / UI Reattiva), Vanilla JavaScript Engine, SortableJS

---

## 💻 Installazione Rapida

1. Clona il repository sul computer o sul server della scuola:
   ```bash
   git clone [https://github.com/michael-byte84/sosty-media.git](https://github.com/michael-byte84/sosty-media.git)
   cd sosty-media
