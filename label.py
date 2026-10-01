import re
FIBRES = {"cotton": "Cotton", "polyester": "Polyester", "wool": "Wool", "silk": "Silk", "linen": "Linen", "nylon": "Nylon", "polyamide": "Nylon", "viscose": "Viscose", "rayon": "Rayon", "acrylic": "Acrylic", "elastane": "Elastane", "spandex": "Elastane", "lycra": "Elastane"}
def parse_composition(text):
    """'65% Cotton 35% Polyester' -> [{'fiber','percentage'}]. Returns [] unless percentages total 100."""
    t = text.lower().replace("\n", " ")
    for pairs in ([(p, n) for p, n in re.findall(r"(\d{1,3})\s*%\s*([a-z]+)", t)], [(p, n) for n, p in re.findall(r"([a-z]+)\s*(\d{1,3})\s*%", t)]):
        found = {}
        for pct, name in pairs:
            if name in FIBRES: found.setdefault(FIBRES[name], int(pct))
        if found and sum(found.values()) == 100: return [{"fiber": k, "percentage": v} for k, v in found.items()]
    return []
