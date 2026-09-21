# Interactive tutorial website

Static pages plus an optional **live lab** for cached demo / smoke / reproduce.

## Local (recommended)

```bash
python -m pip install -e ".[test]"
python scripts/tutorial_lab.py
```

Open `http://127.0.0.1:8000`. Lab buttons call `/api/run/*` on this machine.

## Static preview only

```bash
python -m http.server 8000 --directory website
```

Buttons fall back to `assets/lab_sample_*.json`.

## Screens

1. Intended use  
2. Testing / reproducibility checklists  
3. **Run the lab**  
4. **Score AI-generated tests** (prompt gallery)  
5. Pack evidence by scenario  
6. Summary  

Full written activity guide: [`activity.html`](activity.html) (source: [`docs/activity.md`](../docs/activity.md)).

## Publish

[`.github/workflows/pages.yml`](../.github/workflows/pages.yml) deploys this folder on pushes to `main`.
After the first successful run:

1. GitHub → **Settings → Pages**
2. Source: **GitHub Actions**

Site paths:

- Interactive check: `/` (`index.html`)
- Activity guide: `/activity.html`
