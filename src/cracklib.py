# src/cracklib.py
from __future__ import annotations
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.ioff() # Turn off auto-display of figures in notebooks


# ---- Always save under the project root ----
SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR   = SCRIPT_DIR.parent
DATA_DIR   = (BASE_DIR / "data/processed"); DATA_DIR.mkdir(parents=True, exist_ok=True)
REPO_DIR   = (BASE_DIR / "reports");        REPO_DIR.mkdir(parents=True, exist_ok=True)

# Outputs
PANEL_CSV = DATA_DIR / "crack_321_panel.csv"
COND_TXT  = REPO_DIR / "crack_conditional_returns.txt"
PLOT_LVL  = REPO_DIR / "crack_321.png"
PLOT_ZS   = REPO_DIR / "crack_321_zscore.png"
DASH_TXT  = REPO_DIR / "crack_dashboard.txt"
SEASONAL_PNG = REPO_DIR / "crack_seasonality.png"
TOY_EQUITY_PNG    = REPO_DIR / "crack_toy_rule_equity.png"
TOY_EQUITY_CL_PNG = REPO_DIR / "crack_toy_rule_equity_CL.png"
TOY_SUMMARY_TXT   = REPO_DIR / "crack_toy_rule_summary.txt"

# Yahoo tickers & events
TICKERS = ["CL=F", "RB=F", "HO=F", "CRAK"]
EVENTS: List[Tuple[str,str]] = [("2020-03-09","COVID"), ("2022-02-24","Russia invades Ukraine")]

# ------------- Functions (same as your script) -------------
def _extract_close_frame(raw: pd.DataFrame) -> pd.DataFrame:
    if isinstance(raw.columns, pd.MultiIndex):
        top = set(raw.columns.get_level_values(0))
        if "Adj Close" in top: df = raw["Adj Close"].copy()
        elif "Close" in top:   df = raw["Close"].copy()
        else: raise SystemExit("Yahoo response missing Adj Close/Close.")
    else:
        if "Adj Close" in raw.columns:
            df = raw[["Adj Close"]].copy(); df.columns = ["Adj Close"]
        elif "Close" in raw.columns:
            df = raw[["Close"]].copy(); df.columns = ["Close"]
        else: raise SystemExit("Yahoo response missing Adj Close/Close.")
    return df

def download_prices(tickers: List[str], start: str="2010-01-01") -> pd.DataFrame:
    raw = yf.download(tickers, start=start, auto_adjust=False, progress=False)
    df = _extract_close_frame(raw)
    if df.shape[1] == 1 and len(tickers) == 1: df.columns = [tickers[0]]
    present = [c for c in df.columns if c in tickers]
    if not present: raise SystemExit("No tickers returned from Yahoo.")
    return df[present].ffill().dropna(how="all")

def build_crack_panel(px: pd.DataFrame) -> pd.DataFrame:
    need = {"CL=F","RB=F","HO=F"}
    if not need.issubset(px.columns): raise SystemExit(f"Missing {sorted(need - set(px.columns))}")
    rb_bbl, ho_bbl, cl_bbl = px["RB=F"]*42.0, px["HO=F"]*42.0, px["CL=F"]
    crack = (2*rb_bbl + 1*ho_bbl) - 3*cl_bbl
    out = pd.DataFrame({"CL_$/bbl":cl_bbl,"RBOB_$/bbl":rb_bbl,"HO_$/bbl":ho_bbl,"crack_321":crack})
    out.index.name="Date"
    mu, sd = out["crack_321"].rolling(252, min_periods=100).mean(), out["crack_321"].rolling(252, min_periods=100).std()
    z = (out["crack_321"] - mu)/sd
    out["crack_z_252"] = z
    out["regime"] = np.where(z>1,"rich (high margin)", np.where(z<-1,"cheap (low margin)","neutral"))
    return out

def compute_conditional_forward_returns(panel: pd.DataFrame, px: pd.DataFrame) -> pd.DataFrame:
    df = panel.join(px[[c for c in ["CL=F","CRAK"] if c in px.columns]], how="left").dropna(subset=["crack_z_252"]).ffill()
    tables=[]
    if "CL=F" in df.columns:
        df["ret_CL"]=np.log(df["CL=F"]/df["CL=F"].shift(1)); df["fwd21_CL"]=df["ret_CL"].shift(-21).rolling(21).sum()
        t=df[["regime","fwd21_CL"]].dropna(); tbl=t.groupby("regime")["fwd21_CL"].agg(count="count",mean="mean",std="std")
        tbl["ann_mean"]=tbl["mean"]*(252/21); tbl["ann_sharpe"]=(tbl["mean"]/tbl["std"])*np.sqrt(252/21); tbl["asset"]="CL=F"; tables.append(tbl.reset_index())
    if "CRAK" in df.columns:
        df["ret_CRAK"]=np.log(df["CRAK"]/df["CRAK"].shift(1)); df["fwd21_CRAK"]=df["ret_CRAK"].shift(-21).rolling(21).sum()
        t=df[["regime","fwd21_CRAK"]].dropna(); tbl=t.groupby("regime")["fwd21_CRAK"].agg(count="count",mean="mean",std="std")
        tbl["ann_mean"]=tbl["mean"]*(252/21); tbl["ann_sharpe"]=(tbl["mean"]/tbl["std"])*np.sqrt(252/21); tbl["asset"]="CRAK"; tables.append(tbl.reset_index())
    if not tables: return pd.DataFrame()
    out=pd.concat(tables,ignore_index=True); return out[["asset","regime","count","mean","ann_mean","std","ann_sharpe"]].sort_values(["asset","regime"])

def _add_event_lines(ax, events):  # labels above plot, not vertical
    ax.margins(y=0.05)
    for i,(d,label) in enumerate(events):
        dt = pd.Timestamp(d)
        ax.axvline(dt, linestyle="--", linewidth=1, zorder=1)
        y_axes = 1.01 + 0.04*(i%2)
        ax.annotate(label, xy=(dt,y_axes), xycoords=("data","axes fraction"),
                    xytext=(4,0), textcoords="offset points", ha="left", va="bottom",
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="0.5"),
                    clip_on=False, zorder=3)

def save_plots_with_events(panel: pd.DataFrame):
    """Save crack level & z-score plots; don't auto-show."""
    # Level
    fig, ax = plt.subplots()
    panel["crack_321"].plot(ax=ax)
    ax.set_title("3-2-1 Crack Spread ($/bbl)", pad=28)
    _add_event_lines(ax, EVENTS)
    fig.tight_layout(rect=[0, 0, 1, 0.90])
    fig.savefig(PLOT_LVL, dpi=120, bbox_inches="tight")
    plt.close(fig)

    # Z-score
    fig, ax = plt.subplots()
    panel["crack_z_252"].plot(ax=ax)
    ax.axhline(1.0, ls="--"); ax.axhline(-1.0, ls="--")
    ax.set_title("3-2-1 Crack Spread Z-score (252d)", pad=28)
    _add_event_lines(ax, EVENTS)
    fig.tight_layout(rect=[0, 0, 1, 0.90])
    fig.savefig(PLOT_ZS, dpi=120, bbox_inches="tight")
    plt.close(fig)

    return PLOT_LVL, PLOT_ZS


def write_dashboard(panel: pd.DataFrame):
    s = panel.dropna(subset=["crack_321"]).copy()
    if s.empty: return
    last=s.iloc[-1]; chg21 = (last["crack_321"] - s["crack_321"].iloc[-22]) if len(s)>21 else np.nan
    line = (f"Date: {s.index[-1].date()}\n"
            f"Crack ($/bbl): {last['crack_321']:.2f}\n"
            f"Z-score (252d): {last['crack_z_252']:.2f}\n"
            f"Regime: {last['regime']}\n"
            f"21d change ($/bbl): {('%.2f'%chg21) if pd.notna(chg21) else 'NA'}\n")
    with open(DASH_TXT,"w") as f: f.write(line)
    return line

def plot_seasonality(panel: pd.DataFrame):
    """Save monthly-average chart; don't auto-show."""
    df = panel.dropna(subset=["crack_321"]).copy()
    if df.empty: return None
    monthly = df["crack_321"].groupby(df.index.month).mean()

    fig, ax = plt.subplots()
    monthly.plot(ax=ax, marker="o")
    ax.set_title("Crack Spread Seasonality (Monthly Average)")
    ax.set_xlabel("Month"); ax.set_ylabel("Avg crack ($/bbl)")
    ax.set_xticks(range(1, 13))
    ax.axvspan(4.5, 9.5, alpha=0.15)  # May–Sep
    fig.tight_layout()
    fig.savefig(SEASONAL_PNG, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return SEASONAL_PNG



def max_drawdown(cum: pd.Series)->float:
    eq=np.exp(cum); roll_max=pd.Series(eq).cummax(); dd=(eq-roll_max)/roll_max; return float(dd.min())

def toy_rule(panel: pd.DataFrame, px: pd.DataFrame)->pd.DataFrame:
    df = panel.join(px[[c for c in ["CL=F","CRAK"] if c in px.columns]], how="left").ffill()
    if "CL=F" in df.columns:   df["ret_CL"]=np.log(df["CL=F"]/df["CL=F"].shift(1))
    if "CRAK" in df.columns:   df["ret_CRAK"]=np.log(df["CRAK"]/df["CRAK"].shift(1))
    df["pos_CRAK"]=np.where(df["crack_z_252"]>1,1.0,0.0) if "CRAK" in df.columns else 0.0
    df["pos_CL"]  =np.where(df["crack_z_252"]<-1,-1.0,0.0) if "CL=F" in df.columns else 0.0
    if "ret_CRAK" in df.columns: df["strat_CRAK"]=df["pos_CRAK"]*df["ret_CRAK"]
    if "ret_CL"   in df.columns: df["strat_CL"]  =df["pos_CL"]  *df["ret_CL"]
    for col in ["ret_CRAK","ret_CL","strat_CRAK","strat_CL"]:
        if col in df.columns: df[f"cum_{col}"]=df[col].fillna(0).cumsum()
    return df

def toy_rule_summary_and_plot(tr: pd.DataFrame):
    """Save equity plots and summary; don't auto-show."""
    lines = []

    if {"cum_ret_CRAK","cum_strat_CRAK"}.issubset(tr.columns):
        fig, ax = plt.subplots()
        np.exp(tr["cum_ret_CRAK"]).plot(ax=ax, label="CRAK buy&hold")
        np.exp(tr["cum_strat_CRAK"]).plot(ax=ax, label="CRAK toy rule")
        ax.set_title("CRAK: Toy rule vs Buy&Hold (equity, $1 start)")
        ax.legend()
        fig.tight_layout()
        fig.savefig(TOY_EQUITY_PNG, dpi=120, bbox_inches="tight")
        plt.close(fig)
        daily = tr["strat_CRAK"].dropna()
        ann_ret = daily.mean()*252; ann_vol = daily.std()*np.sqrt(252)
        sharpe = (ann_ret/ann_vol) if ann_vol>0 else np.nan
        mdd = max_drawdown(tr["cum_strat_CRAK"])
        lines += [
            "CRAK toy rule (long when crack_z>+1, else 0):",
            f"  Ann. return:  {ann_ret: .3f}",
            f"  Ann. vol:     {ann_vol: .3f}",
            f"  Sharpe:       {sharpe: .3f}",
            f"  Max drawdown: {mdd: .3f}",
            ""
        ]

    if {"cum_ret_CL","cum_strat_CL"}.issubset(tr.columns):
        fig, ax = plt.subplots()
        np.exp(tr["cum_ret_CL"]).plot(ax=ax, label="CL=F buy&hold")
        np.exp(tr["cum_strat_CL"]).plot(ax=ax, label="CL=F toy rule")
        ax.set_title("CL=F: Toy rule vs Buy&Hold (equity, $1 start)")
        ax.legend()
        fig.tight_layout()
        fig.savefig(TOY_EQUITY_CL_PNG, dpi=120, bbox_inches="tight")
        plt.close(fig)
        daily = tr["strat_CL"].dropna()
        ann_ret = daily.mean()*252; ann_vol = daily.std()*np.sqrt(252)
        sharpe = (ann_ret/ann_vol) if ann_vol>0 else np.nan
        mdd = max_drawdown(tr["cum_strat_CL"])
        lines += [
            "CL=F toy rule (short when crack_z<-1, else 0):",
            f"  Ann. return:  {ann_ret: .3f}",
            f"  Ann. vol:     {ann_vol: .3f}",
            f"  Sharpe:       {sharpe: .3f}",
            f"  Max drawdown: {mdd: .3f}",
            ""
        ]

    if lines:
        with open(TOY_SUMMARY_TXT, "w") as f:
            f.write("Toy rule (educational, no costs/slippage)\n\n")
            f.write("\n".join(lines))
        return "\n".join(lines)


