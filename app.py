
import os
import re
import urllib.parse
import requests
import gradio as gr
from typing import Dict, Any, List

HF_TOKEN = os.getenv("HF_TOKEN", "").strip()  # optional

# ---------------- Utils ----------------
def _q(s: str) -> str:
    return urllib.parse.quote_plus(str(s or "").strip())

def money(x) -> str:
    try:
        return f"${float(x):,.2f}"
    except Exception:
        return ""

def parse_money(text: str, default=None):
    if text is None:
        return default
    m = re.findall(r"\$?\s*([0-9]+(?:\.[0-9]+)?)", str(text))
    return float(m[0]) if m else default

def to_float(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return default

# ---------------- Smart Links (no API keys) ----------------
def tech_links(keywords: str, zip_code: str, radius_miles: int, max_price: float) -> List[str]:
    kw = _q(keywords)
    rz = int(radius_miles or 25)
    mx = int(max_price or 0)
    links = []

    ebay = (
        f"https://www.ebay.com/sch/i.html?_nkw={kw}"
        + (f"&_udhi={mx}" if mx else "")
        + (f"&_stpos={_q(zip_code)}&_sadis={rz}" if zip_code else "")
        + "&_sop=15"  # Price+Shipping lowest
    )
    links.append(f"- eBay: {ebay}")

    cl = (
        f"https://www.craigslist.org/search/sss?query={kw}"
        + (f"&max_price={mx}" if mx else "")
        + (f"&postal={_q(zip_code)}&search_distance={rz}" if zip_code else "")
    )
    links.append(f"- Craigslist: {cl}")

    amazon = f"https://www.amazon.com/s?k={kw}"
    links.append(f"- Amazon: {amazon}")

    bestbuy = f"https://www.bestbuy.com/site/searchpage.jsp?st={kw}"
    links.append(f"- BestBuy: {bestbuy}")

    walmart = f"https://www.walmart.com/search?q={kw}"
    links.append(f"- Walmart: {walmart}")

    offerup = f"https://offerup.com/search/?q={kw}"
    links.append(f"- OfferUp: {offerup}")

    return links

def car_links(make: str, model: str, y1: int, y2: int, zip_code: str, radius_miles: int, max_price: float) -> List[str]:
    mk = _q(make); md = _q(model)
    rz = int(radius_miles or 25); mx = int(max_price or 0)
    y1 = int(y1 or 2005); y2 = int(y2 or y1)
    links = []

    at = (
        f"https://www.autotrader.com/cars-for-sale/{mk}/{md}/{_q(zip_code)}"
        f"?searchRadius={rz}&yearRange={y1}-{y2}"
        + (f"&priceRange=0-{mx}" if mx else "")
    )
    links.append(f"- Autotrader: {at}")

    cg = (
        "https://www.cargurus.com/Cars/inventorylisting/viewDetailsFilterViewInventoryListing.action"
        f"?zip={_q(zip_code)}&distance={rz}&model={md}&make={mk}&minYear={y1}&maxYear={y2}"
    )
    links.append(f"- CarGurus: {cg}")

    cars = (
        "https://www.cars.com/shopping/results/?stock_type=used"
        f"&makes[]={mk}&models[]={mk}-{md}&maximum_distance={rz}&zip={_q(zip_code)}"
        + (f"&list_price_max={mx}" if mx else "")
        + f"&minimum_year={y1}&maximum_year={y2}"
    )
    links.append(f"- Cars.com: {cars}")

    cl = (
        f"https://www.craigslist.org/search/cta?query={mk}+{md}"
        + (f"&max_auto_year={y2}&min_auto_year={y1}" if y1 and y2 else "")
        + (f"&max_price={mx}" if mx else "")
        + (f"&postal={_q(zip_code)}&search_distance={rz}" if zip_code else "")
    )
    links.append(f"- Craigslist (cars+trucks): {cl}")

    return links

# ---------------- OTD helpers ----------------
def compute_otd(entry: Dict[str, Any]) -> float:
    price = to_float(entry.get("price"), 0.0)
    ship = to_float(entry.get("shipping"), 0.0)
    tax_pct = to_float(entry.get("tax_pct"), 0.0)
    doc = to_float(entry.get("doc_fee"), 0.0)
    reg = to_float(entry.get("reg_fee"), 0.0)
    travel_miles = to_float(entry.get("travel_miles"), 0.0)
    travel_per_mile = to_float(entry.get("travel_per_mile"), 0.0)
    tax = price * (tax_pct / 100.0)
    travel = travel_miles * travel_per_mile
    return price + ship + tax + doc + reg + travel

def format_table(candidates: List[Dict[str, Any]]) -> str:
    if not candidates:
        return "No items yet. Add some with `/add`."
    # Sort by OTD
    rows = []
    for c in candidates:
        otd = compute_otd(c)
        rows.append({
            "Source": c.get("source",""),
            "Price": money(c.get("price",0)),
            "Ship": money(c.get("shipping",0)),
            "Tax%": f'{to_float(c.get("tax_pct",0)):.2f}%',
            "Doc": money(c.get("doc_fee",0)),
            "Reg": money(c.get("reg_fee",0)),
            "Travel mi": f'{to_float(c.get("travel_miles",0)):.0f}',
            "$/mi": money(c.get("travel_per_mile",0)),
            "OTD": money(otd),
        })
    # Create a compact markdown table (numbers & keywords only per user preference)
    headers = ["Source","Price","Ship","Tax%","Doc","Reg","Travel mi","$/mi","OTD"]
    md = "|" + "|".join(headers) + "|\n"
    md += "|" + "|".join(["---"]*len(headers)) + "|\n"
    # sort rows by OTD numeric (we have strings now; recompute quickly)
    def _otd_num(r):
        return parse_money(r["OTD"], 0.0)
    for r in sorted(rows, key=_otd_num):
        md += "|" + "|".join(str(r[h]) for h in headers) + "|\n"
    return md

# ---------------- Optional HF Explanation ----------------
def hf_explain(text: str) -> str:
    if not HF_TOKEN:
        return ("(Tip) Set HF_TOKEN to enable a brief LLM suggestion. "
                "For now: use the links, filter by price/distance/condition, then /add items and /show to compare OTD.")
    try:
        model = "Qwen/Qwen2.5-7B-Instruct"  # small default
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        payload = {"inputs": text, "parameters": {"max_new_tokens": 160, "temperature": 0.4}}
        r = requests.post(f"https://api-inference.huggingface.co/models/{model}", headers=headers, json=payload, timeout=30)
        if r.status_code == 200:
            out = r.json()
            if isinstance(out, list) and out and "generated_text" in out[0]:
                return out[0]["generated_text"]
            if isinstance(out, dict) and "generated_text" in out:
                return out["generated_text"]
            return str(out)[:1200]
        return f"LLM call failed ({r.status_code}). Generic advice: filter tightly, then /add and /show for OTD."
    except Exception as e:
        return f"LLM error: {e}. Generic advice: filter tightly, then /add and /show for OTD."

# ---------------- Chat Logic ----------------
HELP = (
    "**Pricing Buddy — Chat (commands)**\n"
    "- `/links tech <keywords>; zip=93710; radius=25; max=500` → smart links for tech\n"
    "- `/links car make=Honda; model=Civic; y=2019-2020; zip=93710; radius=25; max=17000` → smart links for cars\n"
    "- `/add source=<url or name>; price=16500; ship=0; tax=8.35; doc=85; reg=350; miles=20; per_mile=0.6` → add a candidate\n"
    "- `/show` → show OTD table sorted by total\n"
    "- `/clear` → clear candidates\n"
    "- `/help` → show this help\n"
    "You can also talk naturally, e.g., *Find me a 2019–2020 Civic under $17k within 25 miles of 93710.*"
)

def parse_kv_pairs(s: str) -> Dict[str, str]:
    out = {}
    parts = [p.strip() for p in s.split(";") if p.strip()]
    for p in parts:
        if "=" in p:
            k,v = p.split("=",1)
            out[k.strip().lower()] = v.strip()
    return out

def chat_fn(message: str, history: list, state: Dict[str, Any]):
    if state is None:
        state = {"candidates": [], "zip": "93710", "radius": 25, "tax_pct": 8.35}

    msg = message.strip()

    # Commands
    if msg.lower().startswith("/help"):
        return HELP, state

    if msg.lower().startswith("/clear"):
        state["candidates"] = []
        return "Cleared all candidates.", state

    if msg.lower().startswith("/show"):
        return format_table(state["candidates"]), state

    if msg.lower().startswith("/add"):
        # Example: /add source=https://...; price=16500; ship=0; tax=8.35; doc=85; reg=350; miles=20; per_mile=0.6
        args = parse_kv_pairs(msg[len("/add"):])
        entry = {
            "source": args.get("source",""),
            "price": parse_money(args.get("price","0")),
            "shipping": parse_money(args.get("ship","0")),
            "tax_pct": to_float(args.get("tax", state.get("tax_pct", 8.35)), 0.0),
            "doc_fee": parse_money(args.get("doc","0")),
            "reg_fee": parse_money(args.get("reg","0")),
            "travel_miles": to_float(args.get("miles","0"), 0.0),
            "travel_per_mile": parse_money(args.get("per_mile","0")),
        }
        state["candidates"].append(entry)
        return f"Added. Current count: {len(state['candidates'])}\n\nUse `/show` to see OTD table.", state

    if msg.lower().startswith("/links tech"):
        # Format: /links tech <keywords>; zip=...; radius=...; max=...
        body = msg[len("/links tech"):].strip()
        # Split first argument as keywords until first ";"
        if ";" in body:
            kw, rest = body.split(";", 1)
            args = parse_kv_pairs(rest)
        else:
            kw, args = body, {}
        zip_code = args.get("zip", state.get("zip",""))
        radius = int(args.get("radius", state.get("radius", 25)) or 25)
        max_price = parse_money(args.get("max","0")) or 0
        links = tech_links(kw, zip_code, radius, max_price)
        state["zip"] = zip_code; state["radius"] = radius
        resp = f"**Smart links for:** `{kw.strip()}` (zip {zip_code}, radius {radius} mi, max ${int(max_price) if max_price else '—'})\n" + "\n".join(links)
        return resp, state

    if msg.lower().startswith("/links car"):
        # Format: /links car make=Honda; model=Civic; y=2019-2020; zip=...; radius=...; max=...
        body = msg[len("/links car"):].strip()
        args = parse_kv_pairs(body)
        make = args.get("make","")
        model = args.get("model","")
        y = args.get("y","")
        y1, y2 = 0,0
        if "-" in y:
            a,b = y.split("-",1)
            y1 = int(a); y2 = int(b)
        elif y:
            y1 = y2 = int(y)
        else:
            y1, y2 = 2015, 2020
        zip_code = args.get("zip", state.get("zip",""))
        radius = int(args.get("radius", state.get("radius", 25)) or 25)
        max_price = parse_money(args.get("max","0")) or 0
        links = car_links(make, model, y1, y2, zip_code, radius, max_price)
        state["zip"] = zip_code; state["radius"] = radius
        resp = (f"**Smart links for cars:** `{make} {model} {y1}-{y2}` "
                f"(zip {zip_code}, radius {radius} mi, max ${int(max_price) if max_price else '—'})\n" + "\n".join(links))
        return resp, state

    # Natural language fallbacks (very light parsing)
    m_car = re.search(r"\b(car|cars|civic|camry|corolla|accord|tesla|toyota|honda)\b", msg, re.I)
    m_tech = re.search(r"\b(laptop|gpu|gpu|rtx|ps5|xbox|iphone|ipad|tv|camera|headset)\b", msg, re.I)
    if m_car:
        # try to extract make/model/year/radius/max
        mk = re.findall(r"\b(honda|toyota|ford|tesla|bmw|mercedes|hyundai|kia|mazda|chevy|chevrolet)\b", msg, re.I)
        md = re.findall(r"\b(civic|accord|camry|corolla|model 3|model y|elentra|elantra|sonata|optima|mazda3|cx-5|malibu)\b", msg, re.I)
        y = re.findall(r"(20\d{2})", msg)
        budget = parse_money(msg)
        radius = re.findall(r"(\d+)\s*(?:mi|miles)", msg)
        mk = mk[0] if mk else "Honda"
        md = md[0] if md else "Civic"
        if len(y) >= 2:
            y1, y2 = int(y[0]), int(y[1])
        elif len(y) == 1:
            y1 = y2 = int(y[0])
        else:
            y1, y2 = 2019, 2020
        r = int(radius[0]) if radius else 25
        zip_code = re.findall(r"\b9\d{4}\b", msg)
        zip_code = zip_code[0] if zip_code else "93710"
        links = car_links(mk, md, y1, y2, zip_code, r, budget or 0)
        resp = (f"**Smart links for cars:** `{mk} {md} {y1}-{y2}` "
                f"(zip {zip_code}, radius {r} mi, max ${int(budget) if budget else '—'})\n" + "\n".join(links))
        # small LLM suggestion
        extra = hf_explain(f"Suggest how to find best price for a {mk} {md} {y1}-{y2} near {zip_code} within {r} miles under ${int(budget) if budget else 0}.")
        return resp + "\n\n" + extra, state

    if m_tech:
        # extract keywords/budget/radius/zip
        budget = parse_money(msg)
        r = re.findall(r"(\d+)\s*(?:mi|miles)", msg)
        radius = int(r[0]) if r else 25
        zip_code = re.findall(r"\b9\d{4}\b", msg)
        zip_code = zip_code[0] if zip_code else "93710"
        # keywords = the original message (simple)
        links = tech_links(msg, zip_code, radius, budget or 0)
        resp = (f"**Smart links for:** `{msg}` (zip {zip_code}, radius {radius} mi, max ${int(budget) if budget else '—'})\n"
                + "\n".join(links))
        extra = hf_explain(f"Suggest steps to find cheapest '{msg}' near {zip_code} within {radius} miles under ${int(budget) if budget else 0}.")
        return resp + "\n\n" + extra, state

    # default help
    return HELP, state

with gr.Blocks(title="Pricing Buddy — Chat") as demo:
    gr.Markdown("## Pricing Buddy — Chat\nAsk me for deals and I’ll give you smart links and an OTD worksheet. Type `/help` for commands.")

    chatbot = gr.Chatbot(height=420)
    msg = gr.Textbox(placeholder="Ask for deals (e.g., 2019–2020 Civic under $17k near 93710). Press Enter to send.", label=None)
    send = gr.Button("Send")
    clear = gr.Button("Clear")
    # keep session memory here
    state = gr.State({"candidates": [], "zip": "93710", "radius": 25, "tax_pct": 8.35})

    def respond(message, history, st):
        # our existing chat_fn already returns (reply, new_state)
        reply, new_state = chat_fn(message, history or [], st or {"candidates": [], "zip": "93710", "radius": 25, "tax_pct": 8.35})
        history = (history or []) + [(message, reply)]
        return history, new_state, ""

    # Enter to send
    msg.submit(respond, inputs=[msg, chatbot, state], outputs=[chatbot, state, msg])
    # Click to send
    send.click(respond, inputs=[msg, chatbot, state], outputs=[chatbot, state, msg])
    # Clear chat + memory
    clear.click(lambda: ([], {"candidates": [], "zip": "93710", "radius": 25, "tax_pct": 8.35}),
                outputs=[chatbot, state])
        # --- Quick suggested prompts (one click to paste + send) ---
    SUGGESTIONS = [
        "RTX 4060 under $350 near 93710 within 25 miles.",
        "2019–2020 Honda Civic under $17,000 within 25 miles of 93710.",
        "laptop under $800 with 16GB RAM near 93710."
    ]

    with gr.Row():
        s1 = gr.Button(SUGGESTIONS[0], variant="secondary")
        s2 = gr.Button(SUGGESTIONS[1], variant="secondary")
        s3 = gr.Button(SUGGESTIONS[2], variant="secondary")

    # Helper: set the textbox to a prompt, then call respond()
    def _trigger(prompt, history, st):
        return respond(prompt, history, st)

    # Option A: simple one-click send (works on older Gradio)
    s1.click(lambda h, s: _trigger(SUGGESTIONS[0], h, s), inputs=[chatbot, state], outputs=[chatbot, state, msg])
    s2.click(lambda h, s: _trigger(SUGGESTIONS[1], h, s), inputs=[chatbot, state], outputs=[chatbot, state, msg])
    s3.click(lambda h, s: _trigger(SUGGESTIONS[2], h, s), inputs=[chatbot, state], outputs=[chatbot, state, msg])

    # Option B (nicer UX if supported by your Gradio): "paste then auto-send".
    # Uncomment these four lines and comment out the three above if your Gradio supports .then()
    # s1.click(lambda: SUGGESTIONS[0], outputs=msg).then(respond, inputs=[msg, chatbot, state], outputs=[chatbot, state, msg])
    # s2.click(lambda: SUGGESTIONS[1], outputs=msg).then(respond, inputs=[msg, chatbot, state], outputs=[chatbot, state, msg])
    # s3.click(lambda: SUGGESTIONS[2], outputs=msg).then(respond, inputs=[msg, chatbot, state], outputs=[chatbot, state, msg])


if __name__ == "__main__":
    import os
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", 7860)))
