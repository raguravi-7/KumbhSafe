# KumbhSafe

AI-assisted **crowd safety and health triage** system for Kumbh Mela.
Built for the HSC Hackathon by **Team LogicFlux** (Team ID: HSC|TN|03330, Tamil Nadu).

## Team
- Ragu R
- Abinaya M
- Deepika P

## Features
- **Live control-room dashboard** with a zone map, KPIs, zone table and alert feed (auto-refresh every 2 s).
- **Crowd Risk Engine**: people/m2 plus inflow growth gives SAFE / MODERATE / HIGH / CRITICAL with a recommended action. Rapid inflow escalates risk one level.
- **Health Triage Engine**: symptoms, age and vulnerability give RED / ORANGE / YELLOW / GREEN, routed to the nearest suitable facility with an ETA.
- **SOS reporting**: crowd crush, fire, medical, lost child, dispatched to the nearest police / fire / medical unit.
- **Incident log** and a **Simulate surge** button to demo alerts live.
- REST API, no third-party dependencies.

> Note: the live crowd feed is **simulated** from `data/sample/zones.csv`. In production, the same `System.tick()` input is replaced by counts from CCTV / drone / sensor models. Coordinates in sample data are illustrative.

## Setup
Requires **Python 3.9+**. No packages to install.

```bash
git clone https://github.com/<your-username>/KumbhSafe.git
cd KumbhSafe
```

## Run the dashboard
```bash
# Mac / Linux
PYTHONPATH=src python -m kumbhsafe
# Windows PowerShell
$env:PYTHONPATH="src"; python -m kumbhsafe
```
Open **http://127.0.0.1:8000**. Optional: `--port 9000`, `--seed 1` (repeatable demo).

Demo flow: pick a zone, click **Simulate surge**, watch the map turn red and an alert appear. Then submit a triage case or SOS and see which facility is dispatched.

## Command-line demo
```bash
PYTHONPATH=src python -m kumbhsafe.cli
```

## Run tests
```bash
PYTHONPATH=src python -m unittest discover -s tests -t . -v
```

## API
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/zones` | Live zone counts, density, risk level |
| GET | `/api/alerts` | Active HIGH/CRITICAL alerts |
| GET | `/api/facilities` | Hospitals, first-aid, police, fire units |
| GET | `/api/incidents` | Incident log |
| POST | `/api/triage` | `{zone, age, symptoms[], pregnant, chronic}` returns priority and routing |
| POST | `/api/sos` | `{zone, type, note}` returns dispatch |
| POST | `/api/surge` | `{zone}` demo crowd surge |

## Project structure
```
src/kumbhsafe/
  crowd.py     risk engine        triage.py   triage engine
  engine.py    state, alerts, incidents, dispatch
  geo.py       distance + nearest facility
  server.py    HTTP API + static server
  web/         dashboard (HTML/CSS/JS)
data/sample/   zones.csv, facilities.csv, patients.csv
tests/         22 unit and API tests
docs/          architecture.md
```

## Roadmap
- Computer-vision people counting from CCTV/drone feeds
- Real map tiles (Leaflet/OpenStreetMap) and live GPS for responders
- ML triage model trained on real data
- SMS / push alerts, multilingual pilgrim app

## Disclaimer
Prototype for demonstration. Triage output is decision support, not a medical diagnosis.

## License
MIT. See [LICENSE](LICENSE).
