[README_PricingBuddy.md](https://github.com/user-attachments/files/27426291/README_PricingBuddy.md)
# 💰 Pricing Buddy — Deal Finder Chatbot

A Gradio-powered chatbot that helps you find the lowest price on tech gadgets and used cars. Search by natural language or commands, get smart shopping links across major platforms, and use the built-in **Out-the-Door (OTD) calculator** to compare true total costs side by side.

---

## What It Does

Most price comparisons miss the full picture — shipping, taxes, doc fees, and how far you have to drive all add up. Pricing Buddy fixes that:

1. **Generate smart search links** across eBay, Amazon, Craigslist, Best Buy, Walmart, OfferUp, AutoTrader, CarGurus, and more — pre-filtered by your budget, zip code, and radius
2. **Add candidates** you find with their full cost breakdown
3. **Sort by OTD total** — cash price + shipping + tax + doc fee + registration + travel cost — so the cheapest real-world option rises to the top
4. **Optional AI suggestions** — plug in a Hugging Face token to get LLM-powered buying tips

---

## Features

| Feature | Description |
|---|---|
| 🔗 Smart Links (Tech) | eBay, Amazon, Best Buy, Walmart, Craigslist, OfferUp — filtered by price & location |
| 🚗 Smart Links (Cars) | AutoTrader, CarGurus, Cars.com, Craigslist — filtered by make/model/year/radius |
| 🧮 OTD Calculator | Tracks price, shipping, tax %, doc fee, reg fee, and travel cost per candidate |
| 📊 Comparison Table | Candidates sorted by true OTD total in a markdown table |
| 💬 Natural Language | Understands plain English queries without needing exact command syntax |
| 🤖 AI Tips (Optional) | Hugging Face LLM (Qwen2.5-7B) provides buying strategy suggestions |
| 🖱️ Quick Prompts | One-click suggested searches pre-loaded in the UI |

---

## Getting Started

**1. Clone the repo**
```bash
git clone https://github.com/your-username/pricing-buddy.git
cd pricing-buddy
```

**2. Install dependencies**
```bash
pip install gradio requests
```

**3. Run the app**
```bash
python app.py
```

Open your browser to `http://localhost:7860`.

**Optional — Enable AI suggestions**
```bash
export HF_TOKEN=your_huggingface_token
python app.py
```

Without `HF_TOKEN`, the app works fully — you just won't get the LLM tips.

---

## Usage

### Natural Language (easiest)

Just type what you're looking for:

```
2019–2020 Honda Civic under $17,000 within 25 miles of 93710.
RTX 4060 under $350 near 93710.
laptop under $800 near 93710.
```

The app will detect the item type, parse your budget/location, and return pre-filtered links.

---

### Commands

#### `/links tech` — Find tech items

```
/links tech RTX 4060; zip=93710; radius=25; max=350
```

Returns links to eBay, Amazon, Best Buy, Walmart, Craigslist, and OfferUp filtered to your specs.

#### `/links car` — Find used cars

```
/links car make=Honda; model=Civic; y=2019-2020; zip=93710; radius=25; max=17000
```

Returns links to AutoTrader, CarGurus, Cars.com, and Craigslist pre-filtered by make, model, year range, and max price.

#### `/add` — Add a candidate to compare

```
/add source=AutoTrader listing; price=16500; ship=0; tax=8.35; doc=85; reg=350; miles=20; per_mile=0.6
```

| Parameter | Description |
|---|---|
| `source` | URL or name of the listing |
| `price` | Asking price |
| `ship` | Shipping cost |
| `tax` | Sales tax percentage (e.g., `8.35` for 8.35%) |
| `doc` | Dealer doc fee |
| `reg` | Registration/title fee |
| `miles` | One-way travel miles to pick up |
| `per_mile` | Your cost per mile (IRS rate is ~$0.67) |

#### `/show` — View OTD comparison table

```
/show
```

Displays all added candidates sorted by true out-the-door total:

| Source | Price | Ship | Tax% | Doc | Reg | Travel mi | $/mi | OTD |
|---|---|---|---|---|---|---|---|---|
| eBay listing | $320.00 | $15.00 | 8.35% | $0 | $0 | 0 | $0 | $352.72 |
| Local seller | $340.00 | $0 | 0.00% | $0 | $0 | 12 | $0.67 | $348.04 |

#### `/clear` — Reset all candidates

```
/clear
```

#### `/help` — Show command reference

---

## OTD Formula

```
OTD = price + shipping + (price × tax%) + doc_fee + reg_fee + (travel_miles × $/mile)
```

This gives you the true cost of ownership at the point of acquisition, making comparisons honest regardless of seller location or fees.

---

## Supported Platforms

**Tech searches**
- eBay (sorted by price + shipping, with local pickup radius)
- Amazon
- Best Buy
- Walmart
- Craigslist (items for sale)
- OfferUp

**Car searches**
- AutoTrader
- CarGurus
- Cars.com
- Craigslist (cars & trucks)

---

## Project Structure

```
pricing-buddy/
├── app.py        # Full Gradio application
└── README.md
```

---

## Optional: Hugging Face LLM Integration

When `HF_TOKEN` is set, the app calls `Qwen/Qwen2.5-7B-Instruct` via the Hugging Face Inference API to generate short buying strategy suggestions alongside your links. Without the token, all core features (link generation, OTD calculator, comparison table) work normally.

To get a free token: [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

---

## Deployment

The app binds to `0.0.0.0` and reads the `PORT` environment variable, making it compatible with Hugging Face Spaces, Railway, Render, and similar platforms.

```bash
# Hugging Face Spaces
# Push to a Gradio Space — no config needed.

# Render / Railway
PORT=7860 python app.py
```

---

## License

MIT License. See `LICENSE` for details.
