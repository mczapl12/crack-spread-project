# 3–2–1 Crack Spread — tiny quant walkthrough  
*by **Michal Czaplinski***

Refineries buy **crude oil** and sell **gasoline + diesel**.  
A quick proxy for gross margin is the **3–2–1 crack** (all in $/bbl):


**Live HTML (GitHub Pages):** https://mczapl12.github.io/crack-spread-project/

---

## What’s inside

- Build the crack series from free Yahoo Finance tickers  
  (`CL=F` crude $/bbl, `RB=F` & `HO=F` are $/gal → ×42 to $/bbl, `CRAK` refiners ETF)
- Z-score regimes (rich / neutral / cheap) with event markers (COVID, Russia–Ukraine)
- Seasonality check (driving season: May–Sep)
- Tiny *toy rule* to visualize behavior in different regimes (educational only)

**Main notebook:** `notebooks/Crack_Spread_Project.ipynb`  
**One-page web view:** `docs/index.html` (served by GitHub Pages)

---

## Repo layout


> Note: charts are generated at runtime and saved to `reports/` (ignored by git).  
> The notebook displays images inline so you can view them on the web page.

---

## Run locally

```bash
# 1) create and activate a virtual env
python -m venv .venv
# mac/linux:
source .venv/bin/activate
# windows (powershell):
# .venv\Scripts\Activate.ps1

# 2) install packages
pip install -r requirements.txt

# 3) start Jupyter
jupyter lab
# open notebooks/Crack_Spread_Project.ipynb and Run All


## Save and push it

In your project root terminal:

```bash
# open and paste the README content above, or do it via terminal:
cat > README.md << 'EOF'
# 3–2–1 Crack Spread — tiny quant walkthrough  
*by **Michal Czaplinski***

Refineries buy **crude oil** and sell **gasoline + diesel**.  
A quick proxy for gross margin is the **3–2–1 crack** (all in $/bbl):

\[
\text{crack} = 2 \times \text{gasoline} + 1 \times \text{diesel} - 3 \times \text{crude}
\]

**Live HTML (GitHub Pages):** https://mczapl12.github.io/crack-spread-project/

---

## What’s inside

- Build the crack series from free Yahoo Finance tickers  
  (`CL=F` crude $/bbl, `RB=F` & `HO=F` are $/gal → ×42 to $/bbl, `CRAK` refiners ETF)
- Z-score regimes (rich / neutral / cheap) with event markers (COVID, Russia–Ukraine)
- Seasonality check (driving season: May–Sep)
- Tiny *toy rule* to visualize behavior in different regimes (educational only)

**Main notebook:** `notebooks/Crack_Spread_Project.ipynb`  
**One-page web view:** `docs/index.html` (served by GitHub Pages)

---

## Repo layout

src/              # reusable code (cracklib.py)
notebooks/        # the Jupyter notebook walkthrough
docs/             # exported HTML (index.html) for GitHub Pages
requirements.txt  # exact Python packages to reproduce
.gitignore        # keeps data/ and reports/ out of git

> Note: charts are generated at runtime and saved to `reports/` (ignored by git).  
> The notebook displays images inline so you can view them on the web page.

---

## Run locally

```bash
# 1) create and activate a virtual env
python -m venv .venv
# mac/linux:
source .venv/bin/activate
# windows (powershell):
# .venv\Scripts\Activate.ps1

# 2) install packages
pip install -r requirements.txt

# 3) start Jupyter
jupyter lab
# open notebooks/Crack_Spread_Project.ipynb and Run All

python -m jupyter nbconvert --to html notebooks/Crack_Spread_Project.ipynb \
  --output index.html --output-dir docs
