import streamlit as st
import json
import os

st.set_page_config(
    page_title="Multiplier Engine",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed",
)

SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "rfq": {
        "rr_min_euribor_estr": 60.0,
        "rr_min_other": 40.0,
        "euribor_outright": {"pts_per_wn": 0.01, "wn_per_pt": 100, "wn_cap": 10000, "max_pts": 1.0},
        "euribor_package": {"pts_per_wn": 0.01, "wn_per_pt": 600, "wn_cap": 60000, "max_pts": 1.0},
        "estr_outright": {"pts_per_wn": 0.01, "wn_per_pt": 100, "wn_cap": 10000, "max_pts": 1.0},
        "estr_package": {"pts_per_wn": 0.01, "wn_per_pt": 600, "wn_cap": 60000, "max_pts": 1.0},
        "euribor_estr_combined_max": 2.0,
        "outright": {
            "inflation": {"pts_per_wn": 0.01, "wn_per_pt": 5, "wn_cap": 200, "max_pts": 0.4},
            "majors": {"pts_per_wn": 0.01, "wn_per_pt": 25, "wn_cap": 1000, "max_pts": 0.4},
            "minors": {"pts_per_wn": 0.01, "wn_per_pt": 5, "wn_cap": 200, "max_pts": 0.4},
            "pln": {"pts_per_wn": 0.01, "wn_per_pt": 10, "wn_cap": 400, "max_pts": 0.4},
        },
        "package": {
            "inflation": {"pts_per_wn": 0.01, "wn_per_pt": 20, "wn_cap": 800, "max_pts": 0.4},
            "majors": {"pts_per_wn": 0.01, "wn_per_pt": 100, "wn_cap": 4000, "max_pts": 0.4},
            "minors": {"pts_per_wn": 0.01, "wn_per_pt": 20, "wn_cap": 800, "max_pts": 0.4},
            "pln": {"pts_per_wn": 0.01, "wn_per_pt": 40, "wn_cap": 1600, "max_pts": 0.4},
        },
    },
    "efs": {
        "non_stir_outright": {"pts_per_wn": 0.01, "wn_per_pt": 30, "wn_cap": 4500, "max_pts": 1.0},
        "non_stir_ccp": {"pts_per_wn": 0.01, "wn_per_pt": 1250, "wn_cap": 187500, "max_pts": 1.0},
        "stir_outright": {"pts_per_wn": 0.01, "wn_per_pt": 30, "wn_cap": 3000, "max_pts": 1.0},
        "stir_ccp": {"pts_per_wn": 0.01, "wn_per_pt": 1250, "wn_cap": 125000, "max_pts": 1.0},
        "combined_max_pts": 1.5,
    },
    "product": {
        "inflation": {"pts_per_wn": 0.01, "wn_per_pt": 5, "wn_cap": 250, "max_pts": 0.5},
        "majors": {"pts_per_wn": 0.01, "wn_per_pt": 25, "wn_cap": 1250, "max_pts": 0.5},
        "minors": {"pts_per_wn": 0.01, "wn_per_pt": 5, "wn_cap": 250, "max_pts": 0.5},
        "pln": {"pts_per_wn": 0.01, "wn_per_pt": 10, "wn_cap": 500, "max_pts": 0.5},
    },
    "matching": {
        "eurex_outright": {"pts_per_wn": 0.01, "wn_per_pt": 30, "wn_cap": 4500, "max_pts": 1.0},
        "ccp_outright": {"pts_per_wn": 0.01, "wn_per_pt": 1250, "wn_cap": 187500, "max_pts": 1.0},
        "strategy": {"pts_per_wn": 0.01, "wn_per_pt": 2500, "wn_cap": 375000, "max_pts": 1.0},
        "pln_multiplier": 5.0,
        "combined_max_pts": 1.5,
    },
    "voice": {
        "eurex_outright": {"pts_per_wn": 0.01, "wn_per_pt": 30, "wn_cap": 4500, "max_pts": 1.0},
        "ccp_outright": {"pts_per_wn": 0.01, "wn_per_pt": 1250, "wn_cap": 187500, "max_pts": 1.0},
        "strategy": {"pts_per_wn": 0.01, "wn_per_pt": 2500, "wn_cap": 375000, "max_pts": 1.0},
        "pln_multiplier": 5.0,
        "combined_max_pts": 1.5,
    },
    "im": {
        "pts_per_wn": 0.01,
        "wn_per_pt": 60,
        "wn_floor": 0,
        "wn_cap": 3000,
        "max_pts": 0.5,
    },
}


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            try:
                data = json.load(f)
                for k, v in DEFAULT_SETTINGS.items():
                    if k not in data:
                        data[k] = v
                return data
            except Exception:
                pass
    return DEFAULT_SETTINGS


def save_settings(s):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(s, f, indent=2)


# -- INPUT HELPERS -------------------------------------------------------------

def parse_num(raw, fallback=0.0):
    cleaned = str(raw).replace(",", "").replace(" ", "").strip()
    if cleaned == "":
        return fallback
    try:
        return float(cleaned)
    except ValueError:
        return fallback


def ti(label, key, value):
    """Text input accepting commas, returns float."""
    display = "{:g}".format(value) if value != 0 else ""
    raw = st.text_input(label, value=display, key=key, placeholder="e.g. 10,000")
    return parse_num(raw, fallback=0.0)


# -- SCORING -------------------------------------------------------------------

def calc_pts(wn, cfg):
    effective_wn = min(wn, cfg["wn_cap"])
    pts = (effective_wn / cfg["wn_per_pt"]) * cfg["pts_per_wn"]
    return min(pts, cfg["max_pts"])


def calc_rfq_score(cfg, package, exec_type, response_rate, notional):
    if package in ("-- select --", "") or notional <= 0:
        return 0.0, ""
    rr_min = cfg["rr_min_euribor_estr"] if package in ("Euribor", "ESTR") else cfg["rr_min_other"]
    if response_rate < rr_min:
        return 0.0, "RR {:.1f}% below minimum {:.0f}% - 0 pts".format(response_rate, rr_min)
    if package == "Euribor":
        key = "euribor_outright" if exec_type == "Outright" else "euribor_package"
        tc = cfg[key]
    elif package == "ESTR":
        key = "estr_outright" if exec_type == "Outright" else "estr_package"
        tc = cfg[key]
    else:
        prod_key = {"Inflation": "inflation", "Majors": "majors", "Minors": "minors", "PLN": "pln"}.get(package)
        if not prod_key:
            return 0.0, ""
        ec = "outright" if exec_type == "Outright" else "package"
        tc = cfg[ec][prod_key]
    pts = calc_pts(notional, tc)
    return pts, "{} {} - cap {:,}Mn - max {}pts".format(package, exec_type, int(tc["wn_cap"]), tc["max_pts"])


EFS_NON_STIR_CONTRACTS = ["BUXL", "BUND", "BOBL", "SCHATZ", "EURIBORS", "ESTRS"]


def calc_efs_score(cfg, product, contract, exec_type, notional):
    if notional <= 0:
        return 0.0, ""
    is_stir = product == "EFS STIR"
    key = (
        "stir_outright" if exec_type == "Outright" else "stir_ccp"
    ) if is_stir else (
        "non_stir_outright" if exec_type == "Outright" else "non_stir_ccp"
    )
    tc = cfg[key]
    pts = calc_pts(notional, tc)
    label = "{} ({})".format(product, contract) if not is_stir and contract else product
    return pts, "{} {} - {:,}Mn - {:.2f}pts".format(label, exec_type, int(notional), pts)


def calc_product_score(cfg, product, notional):
    if notional <= 0:
        return 0.0, ""
    key = {"Inflation": "inflation", "Majors": "majors", "Minors": "minors", "PLN": "pln"}.get(product)
    if not key:
        return 0.0, ""
    tc = cfg[key]
    pts = calc_pts(notional, tc)
    return pts, "{} - {:,}Mn - cap {:,}Mn - max {}pts - {:.2f}pts".format(
        product, int(notional), int(tc["wn_cap"]), tc["max_pts"], pts
    )


def calc_service_score(cfg, venue, exec_type, currency, notional):
    if notional <= 0:
        return 0.0, ""
    pln_mult = cfg["pln_multiplier"] if currency == "PLN" else 1.0
    if exec_type == "Strategy":
        base_cfg = dict(cfg["strategy"])
    elif venue == "Eurex":
        base_cfg = dict(cfg["eurex_outright"])
    else:
        base_cfg = dict(cfg["ccp_outright"])
    eff = dict(base_cfg)
    eff["pts_per_wn"] = base_cfg["pts_per_wn"] * pln_mult
    pts = min(calc_pts(notional, eff), base_cfg["max_pts"])
    note = " - PLN x500%" if currency == "PLN" else ""
    return pts, "{} {} - {}{} - {:,}Mn - {:.2f}pts".format(venue, exec_type, currency, note, int(notional), pts)


def calc_im_score(cfg, notional):
    if notional <= cfg["wn_floor"]:
        return 0.0, ""
    pts = min((min(notional, cfg["wn_cap"]) / cfg["wn_per_pt"]) * cfg["pts_per_wn"], cfg["max_pts"])
    return pts, "{:,}Mn - {:.2f}pts".format(int(notional), pts)


# -- SESSION STATE -------------------------------------------------------------

def new_rfq_row():
    return {"package": "-- select --", "ccy": "", "exec_type": "Outright", "rr": 0.0, "notional": 0.0}


def new_efs_row():
    return {"product": "-- select --", "contract": "", "ccy": "", "exec_type": "Outright", "notional": 0.0}


def new_svc_row():
    return {"service": "-- select --", "venue": "Eurex", "exec_type": "Outright", "ccy": "EUR", "notional": 0.0}


def init_state():
    if "settings" not in st.session_state:
        st.session_state.settings = load_settings()
    if "rfq_rows" not in st.session_state:
        st.session_state.rfq_rows = [new_rfq_row()]
    if "efs_rows" not in st.session_state:
        st.session_state.efs_rows = [new_efs_row()]
    if "svc_rows" not in st.session_state:
        st.session_state.svc_rows = [new_svc_row()]


init_state()
cfg = st.session_state.settings

# -- CSS -----------------------------------------------------------------------

st.markdown(
    """
    <style>
    [data-testid="stSelectbox"] label,
    [data-testid="stNumberInput"] label,
    [data-testid="stTextInput"] label {
        font-size: 0.7rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .sec-title {
        font-weight: 700;
        font-size: 0.9rem;
        border-left: 3px solid #1a73e8;
        padding-left: 0.6rem;
        margin: 1.2rem 0 0.6rem 0;
    }
    .row-box {
        border: 1px solid #d0e2ff;
        border-radius: 8px;
        padding: 0.8rem 1rem 0.6rem 1rem;
        margin-bottom: 0.5rem;
        background: #f8faff;
    }
    .row-num {
        font-size: 0.6rem;
        font-weight: 700;
        color: #1a73e8;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.3rem;
    }
    .score-pill {
        display: inline-block;
        background: #e8f0fe;
        color: #1a73e8;
        font-weight: 700;
        font-size: 0.88rem;
        padding: 0.2rem 0.75rem;
        border-radius: 20px;
        border: 1px solid #1a73e8;
    }
    .section-total {
        font-size: 0.75rem;
        font-weight: 600;
        color: #333;
        margin-top: 0.4rem;
    }
    .total-box {
        background: #f0f7ff;
        border: 2px solid #1a73e8;
        border-radius: 12px;
        padding: 1.2rem 2rem;
        margin: 1rem 0 1.5rem 0;
    }
    .total-label {
        font-size: 0.65rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        color: #555;
    }
    .total-value {
        font-weight: 700;
        font-size: 2.8rem;
        color: #1a73e8;
        line-height: 1.1;
    }
    .warn { color: #c62828; font-size: 0.75rem; font-weight: 600; }
    .ok { color: #2e7d32; font-size: 0.73rem; }
    .sg-label {
        font-size: 0.65rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #1a73e8;
        margin: 0.8rem 0 0.3rem 0;
        border-bottom: 1px dashed #c5d8f5;
        padding-bottom: 2px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

tab_dash, tab_settings = st.tabs(["Dashboard", "Settings"])

# ==============================================================================
# DASHBOARD
# ==============================================================================

with tab_dash:
    rfq_total = 0.0
    efs_total = 0.0
    product_total = 0.0
    match_total = 0.0
    voice_total = 0.0
    im_total = 0.0

    # -- RFQ -------------------------------------------------------------------

    st.markdown('<div class="sec-title">RFQ</div>', unsafe_allow_html=True)

    pkg_opts = ["-- select --", "Euribor", "ESTR", "Inflation", "Majors", "Minors", "PLN"]
    rows_to_delete = []

    for i, row in enumerate(st.session_state.rfq_rows):
        st.markdown(
            '<div class="row-box"><div class="row-num">Entry {}</div>'.format(i + 1),
            unsafe_allow_html=True,
        )
        c1, c2, c3, c4, c5 = st.columns([1.4, 1, 1, 1, 0.2])

        with c1:
            row["package"] = st.selectbox(
                "Package",
                pkg_opts,
                index=pkg_opts.index(row["package"]) if row["package"] in pkg_opts else 0,
                key="rfq_pkg_{}".format(i),
            )
            if row["package"] == "Majors":
                maj = ["CHF", "GBP", "JPY", "USD"]
                row["ccy"] = st.selectbox(
                    "Currency",
                    maj,
                    index=maj.index(row["ccy"]) if row["ccy"] in maj else 0,
                    key="rfq_maj_{}".format(i),
                )
            elif row["package"] == "Minors":
                mn = ["DKK", "NOK", "SEK", "CZK", "HUF", "PLN"]
                row["ccy"] = st.selectbox(
                    "Currency",
                    mn,
                    index=mn.index(row["ccy"]) if row["ccy"] in mn else 0,
                    key="rfq_min_{}".format(i),
                )
            else:
                row["ccy"] = ""

        with c2:
            exec_opts = ["Outright", "Package"]
            if row["exec_type"] not in exec_opts:
                row["exec_type"] = exec_opts[0]
            row["exec_type"] = st.selectbox(
                "Execution Type",
                exec_opts,
                index=exec_opts.index(row["exec_type"]),
                key="rfq_exec_{}".format(i),
            )

        with c3:
            row["rr"] = st.number_input(
                "Response Rate (%)",
                min_value=0.0,
                max_value=100.0,
                value=float(row["rr"]),
                step=0.5,
                format="%g",
                key="rfq_rr_{}".format(i),
            )

        with c4:
            row["notional"] = ti("Weighted Notional (Mn)", "rfq_not_{}".format(i), row["notional"])

        with c5:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("X", key="rfq_del_{}".format(i), help="Remove"):
                rows_to_delete.append(i)

        pts, msg = calc_rfq_score(cfg["rfq"], row["package"], row["exec_type"], row["rr"], row["notional"])
        rfq_total += pts
        if msg:
            css = "warn" if pts == 0 and row["notional"] > 0 else "ok"
            st.markdown('<div class="{}">{}</div>'.format(css, msg), unsafe_allow_html=True)
            st.markdown('<span class="score-pill">{:.2f} pts</span>'.format(pts), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    for idx in sorted(rows_to_delete, reverse=True):
        st.session_state.rfq_rows.pop(idx)
        st.rerun()

    if st.button("+ Add RFQ Entry", key="rfq_add"):
        st.session_state.rfq_rows.append(new_rfq_row())
        st.rerun()

    ee_max = cfg["rfq"].get("euribor_estr_combined_max", 2.0)
    ee_raw = sum(
        calc_rfq_score(cfg["rfq"], r["package"], r["exec_type"], r["rr"], r["notional"])[0]
        for r in st.session_state.rfq_rows
        if r["package"] in ("Euribor", "ESTR")
    )
    other_rfq = sum(
        calc_rfq_score(cfg["rfq"], r["package"], r["exec_type"], r["rr"], r["notional"])[0]
        for r in st.session_state.rfq_rows
        if r["package"] not in ("Euribor", "ESTR", "-- select --", "")
    )
    ee_capped = min(ee_raw, ee_max)
    rfq_total = ee_capped + other_rfq
    cap_note = " (Euribor/ESTR cap applied)" if ee_raw > ee_max else ""
    st.markdown(
        '<div class="section-total">RFQ Total: <b>{:.2f} pts</b> &nbsp; Euribor+ESTR: <b>{:.2f}</b> &nbsp; Other: <b>{:.2f}</b>{}</div>'.format(
            rfq_total, ee_capped, other_rfq, cap_note
        ),
        unsafe_allow_html=True,
    )

    st.divider()

    # -- HOUSE: PRODUCT --------------------------------------------------------

    st.markdown('<div class="sec-title">HOUSE - Product</div>', unsafe_allow_html=True)

    prod_opts = ["-- select --", "EFS Non STIR", "EFS STIR", "Inflation", "Majors", "Minors", "PLN"]
    efs_to_delete = []

    for i, row in enumerate(st.session_state.efs_rows):
        st.markdown(
            '<div class="row-box"><div class="row-num">Entry {}</div>'.format(i + 1),
            unsafe_allow_html=True,
        )
        c1, c2, c3, c4, c5 = st.columns([1.2, 1.1, 1, 1, 0.2])

        with c1:
            row["product"] = st.selectbox(
                "Product",
                prod_opts,
                index=prod_opts.index(row["product"]) if row["product"] in prod_opts else 0,
                key="efs_prod_{}".format(i),
            )
            if row["product"] == "Majors":
                maj = ["CHF", "GBP", "JPY", "USD"]
                row["ccy"] = st.selectbox(
                    "Currency",
                    maj,
                    index=maj.index(row["ccy"]) if row["ccy"] in maj else 0,
                    key="efs_maj_{}".format(i),
                )
            elif row["product"] == "Minors":
                mn = ["DKK", "NOK", "SEK", "CZK", "HUF", "PLN"]
                row["ccy"] = st.selectbox(
                    "Currency",
                    mn,
                    index=mn.index(row["ccy"]) if row["ccy"] in mn else 0,
                    key="efs_min_{}".format(i),
                )
            else:
                row["ccy"] = ""

        with c2:
            if row["product"] == "EFS Non STIR":
                cur = row.get("contract", "BUXL")
                row["contract"] = st.selectbox(
                    "Contract",
                    EFS_NON_STIR_CONTRACTS,
                    index=EFS_NON_STIR_CONTRACTS.index(cur) if cur in EFS_NON_STIR_CONTRACTS else 0,
                    key="efs_contract_{}".format(i),
                )
            else:
                row["contract"] = ""

        with c3:
            if row["product"] in ("EFS Non STIR", "EFS STIR"):
                exec_opts = ["Outright", "CCP Basis"]
                if row["exec_type"] not in exec_opts:
                    row["exec_type"] = exec_opts[0]
                row["exec_type"] = st.selectbox(
                    "Exec Type",
                    exec_opts,
                    index=exec_opts.index(row["exec_type"]),
                    key="efs_exec_{}".format(i),
                )

        with c4:
            if row["product"] != "-- select --":
                row["notional"] = ti("Weighted Notional (Mn)", "efs_not_{}".format(i), row["notional"])

        with c5:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("X", key="efs_del_{}".format(i), help="Remove"):
                efs_to_delete.append(i)

        if row["product"] in ("EFS Non STIR", "EFS STIR"):
            pts, msg = calc_efs_score(
                cfg["efs"], row["product"], row.get("contract", ""), row["exec_type"], row["notional"]
            )
            efs_total += pts
        else:
            pts, msg = calc_product_score(cfg["product"], row["product"], row["notional"])
            product_total += pts

        if msg:
            st.markdown('<div class="ok">{}</div>'.format(msg), unsafe_allow_html=True)
            st.markdown('<span class="score-pill">{:.2f} pts</span>'.format(pts), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    for idx in sorted(efs_to_delete, reverse=True):
        st.session_state.efs_rows.pop(idx)
        st.rerun()

    if st.button("+ Add Product Entry", key="efs_add"):
        st.session_state.efs_rows.append(new_efs_row())
        st.rerun()

    efs_capped = min(efs_total, cfg["efs"]["combined_max_pts"])
    efs_cap_note = " (combined cap applied)" if efs_total > cfg["efs"]["combined_max_pts"] else ""
    st.markdown(
        '<div class="section-total">EFS: <b>{:.2f} pts</b>{} &nbsp; Product: <b>{:.2f} pts</b></div>'.format(
            efs_capped, efs_cap_note, product_total
        ),
        unsafe_allow_html=True,
    )
    efs_total = efs_capped

    st.divider()

    # -- HOUSE: SERVICES -------------------------------------------------------

    st.markdown('<div class="sec-title">HOUSE - Services</div>', unsafe_allow_html=True)

    svc_to_delete = []

    for i, row in enumerate(st.session_state.svc_rows):
        st.markdown(
            '<div class="row-box"><div class="row-num">Entry {}</div>'.format(i + 1),
            unsafe_allow_html=True,
        )
        svc_opts = ["-- select --", "Matching", "Voice", "Initial Margin"]
        c1, c2, c3, c4, c5 = st.columns([1.1, 1, 1, 1, 0.2])

        with c1:
            row["service"] = st.selectbox(
                "Service",
                svc_opts,
                index=svc_opts.index(row["service"]) if row["service"] in svc_opts else 0,
                key="svc_type_{}".format(i),
            )

        pts = 0.0
        msg = ""

        if row["service"] in ("Matching", "Voice"):
            with c2:
                venue_opts = ["Eurex", "CCP Basis"]
                row["venue"] = st.selectbox(
                    "Venue",
                    venue_opts,
                    index=venue_opts.index(row["venue"]) if row["venue"] in venue_opts else 0,
                    key="svc_venue_{}".format(i),
                )
            with c3:
                exec_opts = ["Outright", "Strategy"]
                if row["exec_type"] not in exec_opts:
                    row["exec_type"] = exec_opts[0]
                row["exec_type"] = st.selectbox(
                    "Execution Type",
                    exec_opts,
                    index=exec_opts.index(row["exec_type"]),
                    key="svc_exec_{}".format(i),
                )
            with c4:
                ccy_opts = ["EUR", "USD", "GBP", "CHF", "JPY", "DKK", "NOK", "SEK", "CZK", "HUF", "PLN"]
                row["ccy"] = st.selectbox(
                    "Currency",
                    ccy_opts,
                    index=ccy_opts.index(row["ccy"]) if row["ccy"] in ccy_opts else 0,
                    key="svc_ccy_{}".format(i),
                )

            row["notional"] = ti("Weighted Notional (Mn)", "svc_not_{}".format(i), row["notional"])

            svc_cfg = cfg["matching"] if row["service"] == "Matching" else cfg["voice"]
            pts, msg = calc_service_score(
                svc_cfg, row["venue"], row["exec_type"], row["ccy"], row["notional"]
            )
            pts = min(pts, svc_cfg["combined_max_pts"])

            if row["service"] == "Matching":
                match_total += pts
            else:
                voice_total += pts

        elif row["service"] == "Initial Margin":
            with c2:
                row["notional"] = ti("IM Notional (Mn)", "svc_not_{}".format(i), row["notional"])
            pts, msg = calc_im_score(cfg["im"], row["notional"])
            im_total += pts

        with c5:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("X", key="svc_del_{}".format(i), help="Remove"):
                svc_to_delete.append(i)

        if msg:
            st.markdown('<div class="ok">{}</div>'.format(msg), unsafe_allow_html=True)
            st.markdown('<span class="score-pill">{:.2f} pts</span>'.format(pts), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    for idx in sorted(svc_to_delete, reverse=True):
        st.session_state.svc_rows.pop(idx)
        st.rerun()

    if st.button("+ Add Service Entry", key="svc_add"):
        st.session_state.svc_rows.append(new_svc_row())
        st.rerun()

    match_capped = min(match_total, cfg["matching"]["combined_max_pts"])
    voice_capped = min(voice_total, cfg["voice"]["combined_max_pts"])
    im_capped = min(im_total, cfg["im"]["max_pts"])

    cap_notes = []
    if match_total > cfg["matching"]["combined_max_pts"]:
        cap_notes.append("Matching cap applied")
    if voice_total > cfg["voice"]["combined_max_pts"]:
        cap_notes.append("Voice cap applied")
    cap_str = " (" + ", ".join(cap_notes) + ")" if cap_notes else ""

    st.markdown(
        '<div class="section-total">Matching: <b>{:.2f}pts</b> &nbsp; Voice: <b>{:.2f}pts</b> &nbsp; Initial Margin: <b>{:.2f}pts</b>{}</div>'.format(
            match_capped, voice_capped, im_capped, cap_str
        ),
        unsafe_allow_html=True,
    )

    st.divider()

    # -- GRAND TOTAL -----------------------------------------------------------

    grand_total = rfq_total + efs_total + product_total + match_capped + voice_capped + im_capped

    st.markdown(
        """
        <div class="total-box">
            <div class="total-label">Total Multiplier Score</div>
            <div class="total-value">{:.2f} <span style="font-size:1.1rem; color:#555; font-weight:400;">pts</span></div>
        </div>
        """.format(grand_total),
        unsafe_allow_html=True,
    )

    b1, b2, b3, b4, b5, b6, b7 = st.columns(7)
    b1.metric("RFQ", "{:.2f}".format(rfq_total))
    b2.metric("EFS", "{:.2f}".format(efs_total))
    b3.metric("Product", "{:.2f}".format(product_total))
    b4.metric("Matching", "{:.2f}".format(match_capped))
    b5.metric("Voice", "{:.2f}".format(voice_capped))
    b6.metric("Init. Margin", "{:.2f}".format(im_capped))
    b7.metric("TOTAL", "{:.2f}".format(grand_total))

    st.markdown("")
    if st.button("Reset All Entries"):
        st.session_state.rfq_rows = [new_rfq_row()]
        st.session_state.efs_rows = [new_efs_row()]
        st.session_state.svc_rows = [new_svc_row()]
        # Clear all text input state so fields show blank
        keys_to_clear = [
            k for k in st.session_state
            if any(
                k.startswith(p)
                for p in [
                    "rfq_not_", "efs_not_", "svc_not_", "rfq_rr_",
                    "rfq_pkg_", "rfq_exec_", "rfq_maj_", "rfq_min_",
                    "efs_prod_", "efs_contract_", "efs_exec_",
                    "efs_maj_", "efs_min_", "svc_type_", "svc_venue_",
                    "svc_exec_", "svc_ccy_",
                ]
            )
        ]
        for k in keys_to_clear:
            del st.session_state[k]
        st.rerun()

# ==============================================================================
# SETTINGS
# ==============================================================================

with tab_settings:
    st.markdown("### Framework Settings")
    st.caption("Edit values below. Click Save to persist across sessions.")

    s = st.session_state.settings

    with st.expander("RFQ - Response Rate Floors", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            s["rfq"]["rr_min_euribor_estr"] = ti(
                "Min RR - Euribor / ESTR (%)",
                "s_rr_ee",
                s["rfq"]["rr_min_euribor_estr"],
            )
        with c2:
            s["rfq"]["rr_min_other"] = ti(
                "Min RR - Inflation / Majors / Minors / PLN (%)",
                "s_rr_other",
                s["rfq"]["rr_min_other"],
            )

    with st.expander("RFQ - Euribor / ESTR Scoring", expanded=False):
        st.caption("Each execution type scores individually (max 1pt each). Combined Euribor+ESTR cap: 2pts.")
        for key, label in [
            ("euribor_outright", "Euribor - Outright"),
            ("euribor_package", "Euribor - Package"),
            ("estr_outright", "ESTR - Outright"),
            ("estr_package", "ESTR - Package"),
        ]:
            if key not in s["rfq"]:
                s["rfq"][key] = {"pts_per_wn": 0.01, "wn_per_pt": 100, "wn_cap": 10000, "max_pts": 1.0}
            st.markdown('<div class="sg-label">{}</div>'.format(label), unsafe_allow_html=True)
            d = s["rfq"][key]
            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                d["wn_per_pt"] = ti("WN per 0.01pt", "s_rfq_{}_wn".format(key), d["wn_per_pt"])
            with sc2:
                d["wn_cap"] = ti("WN Cap (Mn)", "s_rfq_{}_cap".format(key), d["wn_cap"])
            with sc3:
                d["max_pts"] = ti("Max Points", "s_rfq_{}_max".format(key), d["max_pts"])

        st.markdown('<div class="sg-label">Combined Euribor + ESTR Cap</div>', unsafe_allow_html=True)
        s["rfq"]["euribor_estr_combined_max"] = ti(
            "Max Points - Euribor + ESTR combined",
            "s_rfq_ee_combined",
            s["rfq"].get("euribor_estr_combined_max", 2.0),
        )

    with st.expander("RFQ - Outright Scoring (Inflation / Majors / Minors / PLN)", expanded=False):
        for key, label in [("inflation", "Inflation"), ("majors", "Majors"), ("minors", "Minors"), ("pln", "PLN")]:
            st.markdown('<div class="sg-label">{}</div>'.format(label), unsafe_allow_html=True)
            d = s["rfq"]["outright"][key]
            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                d["wn_per_pt"] = ti("WN per 0.01pt", "s_rfq_out_{}_wn".format(key), d["wn_per_pt"])
            with sc2:
                d["wn_cap"] = ti("WN Cap (Mn)", "s_rfq_out_{}_cap".format(key), d["wn_cap"])
            with sc3:
                d["max_pts"] = ti("Max Points", "s_rfq_out_{}_max".format(key), d["max_pts"])

    with st.expander("RFQ - Package Scoring (Inflation / Majors / Minors / PLN)", expanded=False):
        for key, label in [("inflation", "Inflation"), ("majors", "Majors"), ("minors", "Minors"), ("pln", "PLN")]:
            st.markdown('<div class="sg-label">{}</div>'.format(label), unsafe_allow_html=True)
            d = s["rfq"]["package"][key]
            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                d["wn_per_pt"] = ti("WN per 0.01pt", "s_rfq_pkg_{}_wn".format(key), d["wn_per_pt"])
            with sc2:
                d["wn_cap"] = ti("WN Cap (Mn)", "s_rfq_pkg_{}_cap".format(key), d["wn_cap"])
            with sc3:
                d["max_pts"] = ti("Max Points", "s_rfq_pkg_{}_max".format(key), d["max_pts"])

    with st.expander("EFS - Scoring", expanded=False):
        for key, label in [
            ("non_stir_outright", "EFS Non STIR - Outright"),
            ("non_stir_ccp", "EFS Non STIR - CCP Basis"),
            ("stir_outright", "EFS STIR - Outright"),
            ("stir_ccp", "EFS STIR - CCP Basis"),
        ]:
            st.markdown('<div class="sg-label">{}</div>'.format(label), unsafe_allow_html=True)
            d = s["efs"][key]
            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                d["wn_per_pt"] = ti("WN per 0.01pt", "s_efs_{}_wn".format(key), d["wn_per_pt"])
            with sc2:
                d["wn_cap"] = ti("WN Cap (Mn)", "s_efs_{}_cap".format(key), d["wn_cap"])
            with sc3:
                d["max_pts"] = ti("Max Points (per contract)", "s_efs_{}_max".format(key), d["max_pts"])

        st.markdown('<div class="sg-label">Combined EFS Cap</div>', unsafe_allow_html=True)
        s["efs"]["combined_max_pts"] = ti(
            "Max Points - all EFS combined",
            "s_efs_combined_max",
            s["efs"]["combined_max_pts"],
        )

    with st.expander("Product - Scoring (Inflation / Majors / Minors / PLN)", expanded=False):
        if "product" not in s:
            s["product"] = DEFAULT_SETTINGS["product"]
        for key, label in [("inflation", "Inflation"), ("majors", "Majors"), ("minors", "Minors"), ("pln", "PLN")]:
            st.markdown('<div class="sg-label">{}</div>'.format(label), unsafe_allow_html=True)
            d = s["product"][key]
            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                d["wn_per_pt"] = ti("WN per 0.01pt", "s_prod_{}_wn".format(key), d["wn_per_pt"])
            with sc2:
                d["wn_cap"] = ti("WN Cap (Mn)", "s_prod_{}_cap".format(key), d["wn_cap"])
            with sc3:
                d["max_pts"] = ti("Max Points", "s_prod_{}_max".format(key), d["max_pts"])

    for svc_key, svc_label in [("matching", "Matching"), ("voice", "Voice")]:
        with st.expander("{} - Scoring".format(svc_label), expanded=False):
            for key, label in [
                ("eurex_outright", "Eurex Outright"),
                ("ccp_outright", "CCP Basis Outright"),
                ("strategy", "Strategy"),
            ]:
                st.markdown('<div class="sg-label">{}</div>'.format(label), unsafe_allow_html=True)
                d = s[svc_key][key]
                sc1, sc2, sc3 = st.columns(3)
                with sc1:
                    d["wn_per_pt"] = ti("WN per 0.01pt", "s_{}_{}_wn".format(svc_key, key), d["wn_per_pt"])
                with sc2:
                    d["wn_cap"] = ti("WN Cap (Mn)", "s_{}_{}_cap".format(svc_key, key), d["wn_cap"])
                with sc3:
                    d["max_pts"] = ti("Max Points (per currency)", "s_{}_{}_max".format(svc_key, key), d["max_pts"])

            st.markdown('<div class="sg-label">PLN and Combined Cap</div>', unsafe_allow_html=True)
            pc1, pc2 = st.columns(2)
            with pc1:
                s[svc_key]["pln_multiplier"] = ti(
                    "PLN Weight Multiplier x",
                    "s_{}_pln".format(svc_key),
                    s[svc_key]["pln_multiplier"],
                )
            with pc2:
                s[svc_key]["combined_max_pts"] = ti(
                    "Max Points - all combined",
                    "s_{}_cmax".format(svc_key),
                    s[svc_key]["combined_max_pts"],
                )

    with st.expander("Initial Margin - Scoring", expanded=False):
        ic1, ic2, ic3, ic4 = st.columns(4)
        with ic1:
            s["im"]["wn_per_pt"] = ti("WN per 0.01pt", "s_im_wn", s["im"]["wn_per_pt"])
        with ic2:
            s["im"]["wn_floor"] = ti("Floor WN (Mn)", "s_im_floor", s["im"]["wn_floor"])
        with ic3:
            s["im"]["wn_cap"] = ti("Cap WN (Mn)", "s_im_cap", s["im"]["wn_cap"])
        with ic4:
            s["im"]["max_pts"] = ti("Max Points", "s_im_max", s["im"]["max_pts"])

    st.divider()
    col_save, col_reset, _ = st.columns([1, 1, 4])
    with col_save:
        if st.button("Save Settings", type="primary", use_container_width=True):
            save_settings(s)
            st.success("Saved to settings.json")
    with col_reset:
        if st.button("Reset to Defaults", use_container_width=True):
            st.session_state.settings = DEFAULT_SETTINGS
            save_settings(DEFAULT_SETTINGS)
            st.rerun()

    st.caption("Settings stored in settings.json alongside app.py")
