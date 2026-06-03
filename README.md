# SODEXAM — Suivi transmissions partagé

Partage de la rubrique **« Suivi transmissions »** entre toutes les stations.
L'administrateur charge les fichiers `.ods` et lance l'analyse ; les autres
stations voient automatiquement le **même** résultat (consultation seule),
sans avoir à recharger les fichiers.

## Contenu

| Fichier            | Rôle                                                        |
|--------------------|-------------------------------------------------------------|
| `serveur.py`       | Serveur central (Flask) : sert l'app + stocke les données   |
| `app.html`         | L'application (servie par le serveur)                       |
| `requirements.txt` | Dépendances Python                                          |

## Installation (sur le poste « serveur »)

```bash
pip install -r requirements.txt
python serveur.py
```

Le serveur affiche son adresse, par exemple `http://0.0.0.0:5000/`.

## Accès depuis les postes (admin et stations)

Ouvrir dans un navigateur :

```
http://ADRESSE_DU_SERVEUR:5000/
```

(`ADRESSE_DU_SERVEUR` = l'IP du poste où tourne `serveur.py`, ex. `192.168.1.10`.)

## Fonctionnement

1. **Admin** → onglet *Suivi transmissions* → charge les `.ods` → *Analyser*.
   Les fichiers sont publiés sur le serveur (un bandeau le confirme).
2. **Station** → onglet *Suivi transmissions* → l'analyse s'affiche
   automatiquement, en consultation seule. Si aucune donnée n'a encore été
   publiée, un message d'attente est affiché.

Chaque nouvelle analyse de l'admin remplace la précédente pour tout le monde.

## Configuration

Variables d'environnement (toutes optionnelles) :

| Variable             | Défaut          | Description                                   |
|----------------------|-----------------|-----------------------------------------------|
| `SODEXAM_ADMIN_KEY`  | `sodexam-admin` | Clé d'écriture (publication des données)      |
| `SODEXAM_PORT`       | `5000`          | Port d'écoute                                 |
| `SODEXAM_DB`         | `data/suivi.db` | Base SQLite                                   |
| `SODEXAM_HTML`       | `app.html`      | Fichier HTML servi                            |

**Important — clé administrateur :** si vous changez `SODEXAM_ADMIN_KEY`,
modifiez la même valeur dans `app.html` :

```js
const SUIVI_ADMIN_KEY = 'sodexam-admin';   // ~ ligne 5 du <script>
```

> La clé empêche les écritures accidentelles. Elle est visible côté client :
> elle protège contre une publication par erreur, pas contre un utilisateur
> déterminé du réseau interne. Pour une sécurité forte, ajouter une vraie
> authentification (jeton de session) côté serveur.

## Notes techniques

- Données partagées = les fichiers source `.ods` (encodés base64), stockés en
  base SQLite (une seule ligne, dernière analyse). L'analyse est **rejouée**
  dans le navigateur de chaque station via le moteur déjà intégré à l'outil :
  le rendu est identique à celui de l'admin.
- Communication app ↔ outil intégré : `postMessage` (poignée de main
  `READY` / `DATA` / `PUSH`).
- Si le serveur est injoignable, l'onglet reste fonctionnel localement (aucun
  blocage) : la synchronisation reprend dès que le serveur répond.
- Le reste de l'application (Personnel, Matériel, Comptes…) continue de
  fonctionner exactement comme avant, en local.

## Lancement permanent (optionnel)

Pour que le serveur tourne en continu, utilisez un service système
(`systemd`, `nssm` sous Windows) ou un serveur WSGI de production
(`waitress`, `gunicorn`), par ex. :

```bash
pip install waitress
waitress-serve --host=0.0.0.0 --port=5000 serveur:app
```
