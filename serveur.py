#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serveur central SODEXAM — partage de la rubrique « Suivi transmissions ».

Role
----
- Sert l'application (le fichier HTML) a toutes les stations.
- Stocke les fichiers source (.ods METAR/SYNOP) charges par l'administrateur.
- Renvoie ces memes fichiers aux stations, qui rejouent l'analyse a l'identique.

Lancement
---------
    pip install -r requirements.txt
    python serveur.py
puis, depuis chaque poste du reseau :  http://ADRESSE_DU_SERVEUR:5000/

Variables d'environnement (optionnelles)
----------------------------------------
    SODEXAM_ADMIN_KEY   cle d'ecriture (defaut : "sodexam-admin")
                        -> doit etre identique a SUIVI_ADMIN_KEY dans le HTML.
    SODEXAM_HTML        nom du fichier HTML a servir (defaut : app.html)
    SODEXAM_PORT        port d'ecoute (defaut : 5000)
    SODEXAM_DB          chemin de la base SQLite (defaut : data/suivi.db)
"""

import os
import sqlite3
import datetime
from flask import Flask, request, jsonify, send_from_directory, abort

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
HTML_FILE = os.environ.get("SODEXAM_HTML", "app.html")
ADMIN_KEY = os.environ.get("SODEXAM_ADMIN_KEY", "sodexam-admin")
DB_PATH   = os.environ.get("SODEXAM_DB", os.path.join(BASE_DIR, "data", "suivi.db"))
PORT      = int(os.environ.get("SODEXAM_PORT", "5000"))

# Limite de taille des requetes (fichiers .ods en base64) : 32 Mo
MAX_CONTENT_LENGTH = 32 * 1024 * 1024

app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH


# --------------------------------------------------------------------------- #
#  Base de donnees (une seule ligne : l'etat courant du suivi)
# --------------------------------------------------------------------------- #
def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute(
        """CREATE TABLE IF NOT EXISTS suivi (
               id         INTEGER PRIMARY KEY CHECK (id = 1),
               metar      TEXT,
               synop      TEXT,
               updated_at TEXT
           )"""
    )
    con.commit()
    con.close()


def read_suivi():
    con = sqlite3.connect(DB_PATH)
    row = con.execute(
        "SELECT metar, synop, updated_at FROM suivi WHERE id = 1"
    ).fetchone()
    con.close()
    if not row:
        return {"metar": None, "synop": None, "updatedAt": None}
    return {"metar": row[0], "synop": row[1], "updatedAt": row[2]}


def write_suivi(metar, synop):
    now = datetime.datetime.now().isoformat(timespec="seconds")
    con = sqlite3.connect(DB_PATH)
    con.execute(
        """INSERT INTO suivi (id, metar, synop, updated_at)
               VALUES (1, ?, ?, ?)
           ON CONFLICT(id) DO UPDATE SET
               metar = excluded.metar,
               synop = excluded.synop,
               updated_at = excluded.updated_at""",
        (metar, synop, now),
    )
    con.commit()
    con.close()
    return now


# --------------------------------------------------------------------------- #
#  CORS (utile si le HTML est ouvert depuis un autre hote que le serveur)
# --------------------------------------------------------------------------- #
@app.after_request
def add_cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Admin-Key"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return resp


# --------------------------------------------------------------------------- #
#  Routes
# --------------------------------------------------------------------------- #
@app.route("/")
def index():
    return send_from_directory(BASE_DIR, HTML_FILE)


@app.route("/api/suivi", methods=["GET", "POST", "OPTIONS"])
def api_suivi():
    if request.method == "OPTIONS":
        return ("", 204)

    if request.method == "GET":
        # Lecture ouverte (consultation seule pour les stations)
        return jsonify(read_suivi())

    # POST : reserve a l'administrateur (cle partagee)
    if request.headers.get("X-Admin-Key", "") != ADMIN_KEY:
        abort(403, description="Cle administrateur invalide.")

    data = request.get_json(silent=True) or {}
    metar = data.get("metar")
    synop = data.get("synop")
    if not metar and not synop:
        abort(400, description="Aucune donnee fournie (metar/synop).")

    updated_at = write_suivi(metar, synop)
    return jsonify({"ok": True, "updatedAt": updated_at})


@app.errorhandler(403)
@app.errorhandler(400)
@app.errorhandler(413)
def _err(e):
    return jsonify({"ok": False, "error": getattr(e, "description", str(e))}), e.code


# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    init_db()
    print("=" * 64)
    print(" Serveur SODEXAM — Suivi transmissions")
    print(" Application :  http://0.0.0.0:%d/" % PORT)
    print(" Base        :  %s" % DB_PATH)
    print(" Cle admin   :  %s  (modifiable via SODEXAM_ADMIN_KEY)" % ADMIN_KEY)
    print("=" * 64)
    # host=0.0.0.0 -> accessible depuis les autres postes du reseau local
    app.run(host="0.0.0.0", port=PORT, debug=False)
