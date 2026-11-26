"""Generate the "large" synthetic dataset in data/large/ (deterministic, seed 42).

The toy dataset in data/ is hand-written and tiny. This script builds a bigger one with the same
CSV schemas, so each agent has a realistic amount of data to search:

- dishes.csv         ~200 dishes = cuisine-specific bases x proteins
- wines.csv          ~120 wines  = grapes x levels/regions
- restaurants.csv    ~430 restaurants across 8 cities
- user_profiles.csv  1500 users drawn from taste archetypes
- dish_likes.csv     likes sampled from each user's affinity to each dish  (LightFM)
- wine_orders.csv    dish x wine order counts from pairing rules + noise    (implicit)
- ratings.csv        1-5 ratings from cuisine affinity, restaurant quality and rater bias (Surprise)

Run:  uv run python scripts/generate_large_data.py
"""

from __future__ import annotations

import csv
import random
import unicodedata
from pathlib import Path

SEED = 42
OUT = Path(__file__).resolve().parents[1] / "data" / "large"
N_USERS = 1500

# ---------------------------------------------------------------------------------------------
# Dishes: (base name, sauce, intensity, tags, has_gluten, has_dairy, proteins)
# Protein entries are "key:word" — key is the protein vocabulary value, word goes in the name.
# ---------------------------------------------------------------------------------------------
P = {
    "carne": "carne_vermelha:carne", "file": "carne_vermelha:filé", "cordeiro": "carne_vermelha:cordeiro",
    "frango": "ave:frango", "pato": "ave:pato", "porco": "porco:porco", "linguica": "porco:linguiça",
    "salmao": "peixe:salmão", "bacalhau": "peixe:bacalhau", "peixe": "peixe:peixe branco",
    "atum": "peixe:atum", "camarao": "frutos_do_mar:camarão", "lula": "frutos_do_mar:lula",
    "polvo": "frutos_do_mar:polvo", "cogumelos": "vegetal:cogumelos", "legumes": "vegetal:legumes",
    "abobora": "vegetal:abóbora", "berinjela": "vegetal:berinjela", "tofu": "vegetal:tofu",
    "grao": "vegetal:grão-de-bico", "queijo": "queijo:queijo",
}

BASES = {
    "italiana": [
        ("Risoto de", "cremoso", "media", ["arroz", "parmesão", "manteiga"], False, True,
         ["cogumelos", "abobora", "camarao", "frango", "salmao", "linguica"]),
        ("Spaghetti ao sugo com", "tomate", "leve", ["massa", "tomate", "manjericão", "azeite"], True, False,
         ["legumes", "berinjela", "camarao", "carne", "atum"]),
        ("Lasanha de", "tomate", "intensa", ["massa", "queijo", "forno", "tomate"], True, True,
         ["carne", "frango", "berinjela", "abobora", "queijo"]),
        ("Fettuccine cremoso de", "cremoso", "media", ["massa", "creme", "parmesão"], True, True,
         ["cogumelos", "salmao", "camarao", "frango"]),
        ("Pizza de", "tomate", "media", ["massa", "queijo", "forno", "tomate"], True, True,
         ["queijo", "linguica", "cogumelos", "legumes", "atum"]),
    ],
    "japonesa": [
        ("Sushi de", "leve", "leve", ["arroz", "cru", "wasabi", "shoyu"], True, False,
         ["salmao", "atum", "camarao", "legumes", "polvo"]),
        ("Lámen de", "intenso", "intensa", ["caldo", "macarrão", "umami", "ovo"], True, False,
         ["porco", "frango", "cogumelos", "tofu"]),
        ("Tempurá de", "leve", "leve", ["frito", "crocante", "shoyu"], True, False,
         ["legumes", "camarao", "peixe", "abobora"]),
        ("Teriyaki de", "doce", "media", ["shoyu", "gengibre", "arroz", "gergelim"], True, False,
         ["frango", "salmao", "tofu", "carne"]),
    ],
    "brasileira": [
        ("Moqueca de", "picante", "media", ["dendê", "coco", "pimenta", "coentro"], False, False,
         ["peixe", "camarao", "legumes", "polvo", "bacalhau"]),
        ("Bobó de", "cremoso", "media", ["mandioca", "coco", "dendê"], False, False,
         ["camarao", "frango", "legumes"]),
        ("Churrasco de", "leve", "intensa", ["churrasco", "brasa", "sal_grosso", "defumado"], False, False,
         ["carne", "file", "porco", "linguica", "frango", "legumes"]),
        ("Escondidinho de", "cremoso", "media", ["mandioca", "queijo", "forno"], False, True,
         ["carne", "frango", "bacalhau", "legumes"]),
        ("Feijoada de", "intenso", "intensa", ["feijão", "defumado", "laranja", "couve"], False, False,
         ["porco", "linguica", "legumes"]),
    ],
    "argentina": [
        ("Parrilla de", "leve", "intensa", ["grelhado", "chimichurri", "brasa"], False, False,
         ["carne", "file", "cordeiro", "linguica", "legumes"]),
        ("Empanada de", "leve", "media", ["massa", "forno", "azeitona"], True, False,
         ["carne", "frango", "queijo", "legumes"]),
        ("Milanesa de", "leve", "media", ["empanado", "frito", "limão"], True, False,
         ["carne", "frango", "berinjela"]),
    ],
    "francesa": [
        ("Ensopado ao vinho de", "intenso", "media", ["vinho", "ensopado", "ervas", "bacon"], False, False,
         ["carne", "frango", "pato", "cogumelos"]),
        ("na manteiga de limão:", "cremoso", "media", ["manteiga", "limão", "ervas"], False, True,
         ["salmao", "peixe", "camarao", "frango"]),
        ("Quiche de", "cremoso", "media", ["massa", "ovo", "queijo", "forno"], True, True,
         ["legumes", "cogumelos", "salmao", "queijo"]),
        ("Gratinado de", "cremoso", "intensa", ["queijo", "creme", "forno"], False, True,
         ["legumes", "abobora", "bacalhau", "frango"]),
    ],
    "mexicana": [
        ("Tacos de", "picante", "media", ["tortilla", "pimenta", "coentro", "limão"], False, False,
         ["carne", "porco", "frango", "peixe", "legumes", "camarao"]),
        ("Burrito de", "picante", "intensa", ["tortilla", "feijão", "arroz", "queijo"], True, True,
         ["carne", "frango", "legumes", "porco"]),
        ("Enchiladas de", "picante", "media", ["tortilla", "queijo", "forno", "tomate"], False, True,
         ["frango", "queijo", "legumes"]),
    ],
    "árabe": [
        ("Espetinho de", "leve", "media", ["grelhado", "especiarias", "hortelã"], False, False,
         ["cordeiro", "carne", "frango", "legumes"]),
        ("Esfiha de", "leve", "media", ["massa", "forno", "limão"], True, False,
         ["carne", "queijo", "legumes", "frango"]),
        ("Falafel com homus e", "leve", "leve", ["tahine", "ervas", "frito", "limão"], False, False,
         ["grao", "legumes", "berinjela"]),
    ],
    "indiana": [
        ("Curry de", "picante", "intensa", ["curry", "especiarias", "coco", "arroz"], False, False,
         ["frango", "cordeiro", "camarao", "grao", "legumes"]),
        ("Tikka masala de", "cremoso", "intensa", ["especiarias", "creme", "tomate"], False, True,
         ["frango", "queijo", "camarao", "legumes"]),
        ("Biryani de", "picante", "media", ["arroz", "especiarias", "açafrão"], False, False,
         ["frango", "cordeiro", "legumes", "camarao"]),
    ],
    "tailandesa": [
        ("Pad thai de", "doce", "media", ["macarrão", "amendoim", "limão", "tamarindo"], False, False,
         ["camarao", "frango", "tofu", "legumes"]),
        ("Curry verde de", "picante", "intensa", ["coco", "pimenta", "manjericão"], False, False,
         ["frango", "camarao", "tofu", "legumes", "peixe"]),
        ("Salada thai de", "leve", "leve", ["limão", "coentro", "pimenta", "crocante"], False, False,
         ["carne", "camarao", "tofu", "legumes"]),
    ],
    "chinesa": [
        ("Xadrez de", "intenso", "media", ["shoyu", "pimentão", "amendoim"], True, False,
         ["frango", "carne", "tofu", "camarao"]),
        ("Agridoce de", "doce", "media", ["agridoce", "abacaxi", "frito"], True, False,
         ["porco", "frango", "peixe", "legumes"]),
        ("Chop suey de", "leve", "leve", ["legumes", "shoyu", "broto"], True, False,
         ["frango", "carne", "camarao", "tofu", "legumes"]),
    ],
    "peruana": [
        ("Ceviche de", "leve", "leve", ["limão", "cru", "cebola_roxa", "coentro"], False, False,
         ["peixe", "camarao", "polvo", "lula", "cogumelos"]),
        ("Lomo saltado de", "intenso", "intensa", ["shoyu", "batata", "cebola"], True, False,
         ["carne", "frango", "cogumelos"]),
        ("Arroz chaufa de", "intenso", "media", ["arroz", "shoyu", "ovo"], True, False,
         ["frango", "porco", "camarao", "legumes"]),
    ],
    "espanhola": [
        ("Paella de", "intenso", "media", ["arroz", "açafrão", "páprica"], False, False,
         ["camarao", "frango", "legumes", "lula", "polvo"]),
        ("Tapas de", "leve", "leve", ["azeite", "alho", "páprica"], False, False,
         ["camarao", "polvo", "cogumelos", "linguica", "queijo"]),
    ],
}

# ---------------------------------------------------------------------------------------------
# Wines: grape -> (type, body, notes, [(level, region, price)])
# ---------------------------------------------------------------------------------------------
LEVELS = [("", "baixa"), ("Reserva", "media"), ("Gran Reserva", "alta")]
GRAPES = {
    "Pinot Noir": ("tinto", "leve", "cereja e terroso", ["Chile", "Borgonha", "Oregon", "Serra Gaúcha"]),
    "Gamay": ("tinto", "leve", "frutas vermelhas frescas", ["Beaujolais"]),
    "Merlot": ("tinto", "medio", "ameixa macia", ["Serra Gaúcha", "Chile", "Bordeaux"]),
    "Sangiovese": ("tinto", "medio", "cereja e ervas secas", ["Toscana", "Chianti"]),
    "Tempranillo": ("tinto", "medio", "couro e frutas negras", ["Rioja", "Ribera del Duero"]),
    "Carménère": ("tinto", "medio", "pimentão e especiarias", ["Chile"]),
    "Grenache": ("tinto", "medio", "morango e especiarias", ["Rhône", "Priorat"]),
    "Malbec": ("tinto", "encorpado", "amora e taninos firmes", ["Mendoza", "Cahors", "Salta"]),
    "Cabernet Sauvignon": ("tinto", "encorpado", "cassis e carvalho", ["Napa", "Chile", "Bordeaux", "Mendoza"]),
    "Syrah": ("tinto", "encorpado", "pimenta-do-reino e frutas negras", ["Rhône", "Barossa", "Vale do São Francisco"]),
    "Tannat": ("tinto", "encorpado", "taninos potentes", ["Uruguai", "Madiran"]),
    "Nebbiolo": ("tinto", "encorpado", "rosas e alcatrão", ["Barolo", "Piemonte"]),
    "Touriga Nacional": ("tinto", "encorpado", "violeta e frutas negras", ["Douro", "Dão"]),
    "Sauvignon Blanc": ("branco", "leve", "cítrico e herbáceo", ["Chile", "Nova Zelândia", "Loire"]),
    "Albariño": ("branco", "leve", "salino e floral", ["Rías Baixas"]),
    "Riesling": ("branco", "leve", "lima e leve dulçor", ["Alsácia", "Mosel"]),
    "Pinot Grigio": ("branco", "leve", "pera e amêndoa", ["Vêneto"]),
    "Alvarinho": ("branco", "leve", "cítrico e mineral", ["Vinho Verde"]),
    "Chardonnay": ("branco", "medio", "maçã verde e mineral", ["Chablis", "Chile", "Serra Gaúcha"]),
    "Chardonnay barricado": ("branco", "encorpado", "manteiga e baunilha", ["Borgonha", "Napa"]),
    "Viognier": ("branco", "medio", "damasco e flores", ["Rhône"]),
    "Gewürztraminer": ("branco", "medio", "lichia e especiarias", ["Alsácia"]),
    "Chenin Blanc": ("branco", "medio", "mel e maçã", ["Loire", "África do Sul"]),
    "Rosé": ("rose", "leve", "morango e seco", ["Provence", "Navarra", "Serra Gaúcha"]),
    "Espumante Brut": ("espumante", "leve", "borbulhas finas e cítrico", ["Serra Gaúcha", "Cava"]),
    "Prosecco": ("espumante", "leve", "pera e floral", ["Vêneto"]),
    "Champagne Brut": ("espumante", "leve", "brioche e acidez elegante", ["Champagne"]),
}

# Pairing knowledge (the rules of feature 001) used to *simulate* order history for implicit.
RULES = [
    ({"protein": "carne_vermelha", "intensity": "intensa"}, ["tinto"], ["encorpado"]),
    ({"protein": "carne_vermelha"}, ["tinto"], ["medio", "encorpado"]),
    ({"protein": "peixe", "intensity": "leve"}, ["branco", "espumante"], ["leve"]),
    ({"protein": "peixe"}, ["branco", "rose"], ["leve", "medio"]),
    ({"protein": "frutos_do_mar"}, ["branco", "espumante"], ["leve", "medio"]),
    ({"sauce": "cremoso"}, ["branco"], ["medio", "encorpado"]),
    ({"sauce": "tomate"}, ["tinto"], ["leve", "medio"]),
    ({"sauce": "picante"}, ["branco", "rose"], ["leve", "medio"]),
    ({"sauce": "doce"}, ["branco", "espumante"], ["leve", "medio"]),
    ({"protein": "porco", "sauce": "intenso"}, ["tinto"], ["medio"]),
    ({"protein": "porco"}, ["tinto", "rose"], ["leve", "medio"]),
    ({"protein": "ave"}, ["tinto", "branco"], ["leve", "medio"]),
    ({"protein": "vegetal", "intensity": "leve"}, ["branco", "espumante", "rose"], ["leve"]),
    ({"protein": "vegetal"}, ["branco", "rose", "tinto"], ["leve", "medio"]),
    ({"intensity": "intensa"}, ["tinto"], ["encorpado"]),
    ({"protein": "queijo"}, ["tinto", "branco"], ["medio"]),
]

# ---------------------------------------------------------------------------------------------
# Restaurants
# ---------------------------------------------------------------------------------------------
CITIES = {
    "São Paulo": ["Pinheiros", "Jardins", "Vila Madalena", "Bixiga", "Liberdade", "Itaim Bibi", "Moema"],
    "Rio de Janeiro": ["Leblon", "Botafogo", "Santa Teresa", "Copacabana", "Barra da Tijuca", "Lapa"],
    "Belo Horizonte": ["Savassi", "Lourdes", "Santa Tereza", "Funcionários"],
    "Curitiba": ["Batel", "Centro", "Santa Felicidade", "Água Verde"],
    "Porto Alegre": ["Moinhos de Vento", "Cidade Baixa", "Bom Fim", "Menino Deus"],
    "Salvador": ["Rio Vermelho", "Barra", "Pelourinho", "Pituba"],
    "Recife": ["Boa Viagem", "Casa Forte", "Recife Antigo", "Espinheiro"],
    "Brasília": ["Asa Sul", "Asa Norte", "Lago Sul", "Sudoeste"],
}
CITY_WEIGHT = {"São Paulo": 3.0, "Rio de Janeiro": 2.0}  # bigger cities get more restaurants
NAMES = {
    "italiana": (["Trattoria", "Osteria", "Cantina", "Forneria", "Ristorante"],
                 ["Bella", "da Nonna", "Toscana", "del Porto", "Il Giardino", "Vecchia Roma", "Sapori"]),
    "japonesa": (["Sushi", "Izakaya", "Restaurante", "Temaki"], ["Sakura", "Kaze", "Hana", "Kyoto", "Yuzu", "Koi"]),
    "brasileira": (["Boteco", "Casa", "Cozinha", "Empório"], ["Mineira", "da Vó", "do Sertão", "Baiana", "Raiz", "Caipira"]),
    "argentina": (["Parrilla", "Asador", "Bodegón"], ["Buenos Aires", "Patagonia", "La Boca", "El Gaucho", "Mendoza"]),
    "francesa": (["Bistrô", "Brasserie", "Maison"], ["Le Petit", "Lumière", "Provence", "Saint-Germain", "Montmartre"]),
    "mexicana": (["Taquería", "Cantina", "Cocina"], ["El Sol", "La Catrina", "Oaxaca", "Frida", "Azteca"]),
    "árabe": (["Empório", "Casa", "Restaurante"], ["Beirute", "Damasco", "Cedro", "Aladin", "Al Manara"]),
    "indiana": (["Restaurante", "Casa", "Curry House"], ["Taj", "Masala", "Jaipur", "Ganesha", "Bombay"]),
    "tailandesa": (["Thai", "Restaurante", "Cozinha"], ["Bangkok", "Lotus", "Siam", "Chiang Mai", "Orchid"]),
    "chinesa": (["Restaurante", "Casa", "Dragão"], ["Dourado", "Imperial", "Xangai", "Pequim", "Jade"]),
    "peruana": (["Cevichería", "Cocina", "Restaurante"], ["Lima", "Cusco", "Inca", "Pacífico", "Andino"]),
    "espanhola": (["Tasca", "Bodega", "Taberna"], ["Sevilla", "Madrid", "Barcelona", "Andaluz", "Galicia"]),
}

# ---------------------------------------------------------------------------------------------
# Users: taste archetypes (weights are relative)
# ---------------------------------------------------------------------------------------------
ARCHETYPES = {
    "carnivoro": dict(w=3, cuisines=["brasileira", "argentina", "árabe"], proteins=["carne_vermelha", "porco"],
                      terms=["carne", "grelhado", "churrasco", "defumado", "brasa", "chimichurri", "linguiça"]),
    "vegetariano": dict(w=2, cuisines=["italiana", "indiana", "árabe", "tailandesa"], proteins=["vegetal", "queijo"],
                        terms=["legumes", "cogumelos", "ervas", "grão-de-bico", "tofu", "berinjela", "abóbora"],
                        restriction="vegetariano"),
    "vegano": dict(w=1, cuisines=["árabe", "tailandesa", "indiana", "japonesa"], proteins=["vegetal"],
                   terms=["legumes", "tofu", "grão-de-bico", "coco", "ervas", "azeite"], restriction="vegano"),
    "mar": dict(w=2, cuisines=["japonesa", "peruana", "brasileira", "espanhola"],
                proteins=["peixe", "frutos_do_mar"], terms=["peixe", "camarão", "salmão", "polvo", "limão", "cru", "lula"]),
    "apimentado": dict(w=2, cuisines=["mexicana", "indiana", "tailandesa"], proteins=["ave", "porco", "carne_vermelha"],
                       terms=["pimenta", "curry", "especiarias", "coentro", "tortilla", "picante"]),
    "massas": dict(w=2, cuisines=["italiana", "francesa"], proteins=["queijo", "ave", "carne_vermelha"],
                   terms=["massa", "queijo", "tomate", "parmesão", "forno", "manjericão", "cremoso"]),
    "oriental": dict(w=2, cuisines=["japonesa", "chinesa", "tailandesa"], proteins=["ave", "peixe", "porco"],
                     terms=["shoyu", "arroz", "gengibre", "umami", "macarrão", "gergelim"]),
    "conforto": dict(w=2, cuisines=["francesa", "brasileira", "italiana"], proteins=["ave", "carne_vermelha", "queijo"],
                     terms=["cremoso", "manteiga", "queijo", "creme", "forno", "mandioca"]),
    "leve": dict(w=1, cuisines=["japonesa", "peruana", "árabe"], proteins=["peixe", "vegetal", "ave"],
                 terms=["leve", "limão", "ervas", "azeite", "legumes", "cru"]),
}


def norm(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


# Tags that describe how a dish is cooked, not what goes in it: kept as LightFM features,
# left out of the human-readable ingredient list.
COOKING_TERMS = {"grelhado", "brasa", "frito", "forno", "cru", "crocante", "churrasco", "ensopado",
                 "empanado", "defumado", "umami", "agridoce", "curry"}
CUISINE_PRICE = {"italiana": 52, "japonesa": 58, "brasileira": 48, "argentina": 62, "francesa": 72,
                 "mexicana": 42, "árabe": 38, "indiana": 50, "tailandesa": 50, "chinesa": 40,
                 "peruana": 60, "espanhola": 64}
PROTEIN_PRICE = {"carne_vermelha": 22, "frutos_do_mar": 26, "peixe": 16, "ave": 4, "porco": 6,
                 "vegetal": -6, "queijo": 0}


def build_dishes(rng: random.Random) -> list[dict]:
    dishes, seen = [], set()
    for cuisine, bases in BASES.items():
        for base, sauce, intensity, tags, gluten, dairy, proteins in bases:
            for pkey in proteins:
                protein, word = P[pkey].split(":")
                if base.endswith(":"):  # "na manteiga de limão:" -> "Salmão na manteiga de limão"
                    name = f"{word.capitalize()} {base[:-1]}"
                else:
                    name = f"{base} {word}"
                if name in seen:
                    continue
                seen.add(name)
                has_dairy = dairy or protein == "queijo"
                suitable = []
                if protein in ("vegetal", "queijo"):
                    suitable.append("vegetariano")
                    if protein == "vegetal" and not has_dairy and "ovo" not in tags:
                        suitable.append("vegano")
                if not gluten:
                    suitable.append("sem_gluten")
                if not has_dairy:
                    suitable.append("sem_lactose")
                word_tags = [w for w in word.split() if w not in ("de", "branco")]
                ingredients = list(dict.fromkeys(
                    [word] + [t.replace("_", " ") for t in tags if t not in COOKING_TERMS]
                ))
                price = CUISINE_PRICE[cuisine] + PROTEIN_PRICE[protein] + rng.randint(-6, 6)
                dishes.append(dict(
                    name=name, cuisine=cuisine, protein=protein, sauce=sauce, intensity=intensity,
                    tags=";".join(dict.fromkeys(tags + word_tags)), suitable_for=";".join(suitable),
                    ingredients=";".join(ingredients), price_brl=price,
                ))
    return dishes


GRAPE_OF = {"Rosé": "Grenache e Syrah", "Espumante Brut": "Chardonnay e Pinot Noir",
            "Champagne Brut": "Chardonnay e Pinot Noir", "Prosecco": "Glera"}
WINE_PRICE = {"baixa": (45, 85), "media": (90, 180), "alta": (200, 480)}
TICKET = {"baixa": (40, 80), "media": (90, 160), "alta": (180, 350)}


def build_wines(rng: random.Random) -> list[dict]:
    wines = []
    for grape, (wtype, body, notes, regions) in GRAPES.items():
        for i, region in enumerate(regions):
            for level, price in LEVELS:
                # Not every grape/region has all three levels: keep the catalog varied.
                if (i + len(level)) % 3 == 2 and price != "media":
                    continue
                name = " ".join(p for p in (grape, level, region) if p)
                grape_name = GRAPE_OF.get(grape, grape.replace(" barricado", ""))
                wines.append(dict(name=name, type=wtype, body=body, price=price, notes=notes,
                                  grape=grape_name, price_brl=rng.randint(*WINE_PRICE[price])))
    return wines


def affinity(dish: dict, wine: dict) -> float:
    score = 0.0
    for when, types, bodies in RULES:
        if all(dish[k] == v for k, v in when.items()) and wine["type"] in types and wine["body"] in bodies:
            score += len(when)
    return score


def build_orders(rng: random.Random, dishes: list[dict], wines: list[dict]) -> list[dict]:
    popularity = {w["name"]: rng.lognormvariate(0, 0.2) for w in wines}
    rows = []
    for d in dishes:
        scored = [(affinity(d, w) * popularity[w["name"]], w) for w in wines]
        good = [(s, w) for s, w in scored if s > 0]
        # Weighted sampling without replacement (score^2): strong pairings dominate, but each
        # dish gets its own mix instead of the same few popular bottles everywhere.
        chosen = []
        for _ in range(min(len(good), rng.randint(5, 9))):
            pick = rng.choices(range(len(good)), weights=[s * s for s, _ in good])[0]
            chosen.append(good.pop(pick))
        noise = rng.sample([w for s, w in scored if s == 0], k=min(2, sum(1 for s, _ in scored if s == 0)))
        for s, w in chosen:
            rows.append(dict(dish=d["name"], wine=w["name"], count=max(1, round(s * rng.uniform(1.5, 3.5)))))
        for w in noise:  # occasional odd pairing: real order logs are messy
            if rng.random() < 0.5:
                rows.append(dict(dish=d["name"], wine=w["name"], count=1))
    return rows


def build_restaurants(rng: random.Random) -> list[dict]:
    rows, names = [], set()
    for city, hoods in CITIES.items():
        for cuisine, (prefixes, suffixes) in NAMES.items():
            n = round(rng.uniform(2, 4) * CITY_WEIGHT.get(city, 1.0))
            for _ in range(n):
                hood = rng.choice(hoods)
                base = f"{rng.choice(prefixes)} {rng.choice(suffixes)}"
                name = base if base not in names else f"{base} {hood}"
                k = 2
                while name in names:
                    name, k = f"{base} {hood} {k}", k + 1
                names.add(name)
                price = rng.choices(["baixa", "media", "alta"], weights=[3, 4, 2])[0]
                rows.append(dict(name=name, cuisine=cuisine, city=city, neighborhood=hood, price=price,
                                 avg_ticket_brl=rng.randint(*TICKET[price])))
    return rows


def dish_affinity(user: dict, dish: dict) -> float:
    arch = ARCHETYPES[user["archetype"]]
    terms = {norm(t) for t in dish["tags"].split(";")} | {dish["sauce"], dish["intensity"]}
    score = 1.2 * (dish["cuisine"] in arch["cuisines"]) + 1.5 * (dish["protein"] in arch["proteins"])
    score += 0.6 * len(terms & {norm(t) for t in user["prefs"]})
    return score


def build_users(rng: random.Random, dishes, restaurants):
    names, weights = zip(*((k, v["w"]) for k, v in ARCHETYPES.items()))
    city_names = list(CITIES)
    city_w = [CITY_WEIGHT.get(c, 1.0) for c in city_names]
    quality = {r["name"]: rng.gauss(0, 0.6) for r in restaurants}
    by_city: dict[str, list[dict]] = {}
    for r in restaurants:
        by_city.setdefault(r["city"], []).append(r)

    profiles, likes, ratings = [], [], []
    for i in range(1, N_USERS + 1):
        uid = f"u{i:04d}"
        archetype = rng.choices(names, weights=weights)[0]
        arch = ARCHETYPES[archetype]
        prefs = rng.sample(arch["terms"], k=min(len(arch["terms"]), rng.randint(3, 5)))
        if rng.random() < 0.3:  # a secondary taste
            other = ARCHETYPES[rng.choice(names)]
            prefs.append(rng.choice(other["terms"]))
        prefs = list(dict.fromkeys(prefs))
        user = dict(archetype=archetype, prefs=prefs)
        profiles.append(dict(user_id=uid, preferences=";".join(prefs)))

        restriction = arch.get("restriction")
        eligible = [d for d in dishes if not restriction or restriction in d["suitable_for"].split(";")]
        scored = sorted(((dish_affinity(user, d) + rng.gauss(0, 0.8), d["name"]) for d in eligible), reverse=True)
        for _, name in scored[: rng.randint(6, 14)]:
            likes.append(dict(user_id=uid, dish=name))

        home = rng.choices(city_names, weights=city_w)[0]
        bias = rng.gauss(0, 0.5)
        # ~90% of visits in the home city: dense enough local overlap for user-based KNN.
        n_visits = rng.randint(15, 35)
        local = rng.sample(by_city[home], k=min(len(by_city[home]), round(n_visits * 0.9)))
        visited = local + rng.sample(restaurants, n_visits - len(local))
        for r in {r["name"]: r for r in visited}.values():
            liked = 1.0 if r["cuisine"] in arch["cuisines"] else -0.6
            value = 3.2 + liked + quality[r["name"]] + bias + rng.gauss(0, 0.6)
            ratings.append(dict(user_id=uid, restaurant=r["name"], rating=int(min(5, max(1, round(value))))))
    return profiles, likes, ratings


def write(name: str, rows: list[dict]) -> None:
    with open(OUT / name, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"{name:20s} {len(rows):>6} rows")


def main() -> None:
    rng = random.Random(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    dishes = build_dishes(rng)
    wines = build_wines(rng)
    restaurants = build_restaurants(rng)
    orders = build_orders(rng, dishes, wines)
    profiles, likes, ratings = build_users(rng, dishes, restaurants)
    for name, rows in [("dishes.csv", dishes), ("wines.csv", wines), ("restaurants.csv", restaurants),
                       ("wine_orders.csv", orders), ("user_profiles.csv", profiles),
                       ("dish_likes.csv", likes), ("ratings.csv", ratings)]:
        write(name, rows)
    assert not any("," in r["name"] for r in restaurants), "Surprise reads ratings.csv with sep=','"


if __name__ == "__main__":
    main()
