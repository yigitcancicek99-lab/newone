"""
Veri kaynakları:
  1) OpenStreetMap (Overpass API) — şehir/ilçe + kategoriye göre işletme listesi
     (ad, telefon, web, e-posta, adres). Ücretsiz; veri © OpenStreetMap katkıcıları (ODbL).
  2) Firma web sitesi — ana sayfa ve iletişim sayfasından kamuya açık telefon,
     e-posta ve sosyal medya bağlantılarını çıkarır.

Yalnızca kurumların kamuya açık iletişim bilgileri toplanır. Bireylerin kişisel
verileri için KVKK ve İYS (ticari elektronik ileti onayı) kurallarına uyulmalıdır.
"""

import json
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from html import unescape
from html.parser import HTMLParser

from motor import telefon_normal, web_normal
from sablonlar import OSM_KATEGORILER

KULLANICI_AJANI = "MusteriBulmaMotoru/1.0 (+yerel kullanim)"
OVERPASS_SUNUCULARI = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]


class KaynakHatasi(Exception):
    pass


def _istek(url, veri=None, zaman_asimi=30):
    istek = urllib.request.Request(url, data=veri, headers={
        "User-Agent": KULLANICI_AJANI,
        "Accept-Language": "tr,en;q=0.8",
    })
    baglam = ssl.create_default_context()
    with urllib.request.urlopen(istek, timeout=zaman_asimi, context=baglam) as yanit:
        ham = yanit.read(3_000_000)
        tur = yanit.headers.get_content_charset() or "utf-8"
        return ham.decode(tur, errors="replace"), yanit.geturl()


# --- OpenStreetMap -------------------------------------------------------------
def tr_buyuk_ilk(metin):
    """'istanbul' -> 'İstanbul', 'kadıköy' -> 'Kadıköy' (Türkçe i/İ kuralıyla)."""
    def kelime(k):
        if not k:
            return k
        ilk = "İ" if k[0] == "i" else "I" if k[0] == "ı" else k[0].upper()
        return ilk + k[1:]
    return " ".join(kelime(k) for k in metin.strip().split(" "))


def _oq(metin):
    return metin.replace("\\", "\\\\").replace('"', '\\"')


def overpass_sorgusu(etiketler, sehir, ilce="", ad_icerir="", limit=200):
    sehir = tr_buyuk_ilk(sehir)
    alan = f'area["name"="{_oq(sehir)}"]["admin_level"="4"]->.il;\n'
    if ilce:
        alan += (f'rel(area.il)["name"="{_oq(tr_buyuk_ilk(ilce))}"]["boundary"="administrative"];\n'
                 'map_to_area->.hedef;\n')
        hedef = "hedef"
    else:
        hedef = "il"
    ad_filtre = f'["name"~"{_oq(ad_icerir)}",i]' if ad_icerir else '["name"]'
    parcalar = "".join(f'  nwr["{_oq(k)}"="{_oq(v)}"]{ad_filtre}(area.{hedef});\n' for k, v in etiketler)
    return f"[out:json][timeout:90];\n{alan}(\n{parcalar});\nout center tags {int(limit)};"


def _adres(t):
    sokak = " ".join(filter(None, [t.get("addr:street", ""), t.get("addr:housenumber", "")]))
    parca = [sokak, t.get("addr:neighbourhood") or t.get("addr:suburb", ""),
             t.get("addr:district", ""), t.get("addr:city", "")]
    return ", ".join(p for p in parca if p) or t.get("addr:full", "")


def osm_ogesini_leade_cevir(oge, kategori, sehir, ilce):
    t = oge.get("tags", {})
    telefonlar = []
    for k in ("phone", "contact:phone", "contact:mobile", "mobile"):
        for parca in re.split(r"[;,/]", t.get(k, "")):
            n = telefon_normal(parca)
            if n and n not in telefonlar:
                telefonlar.append(n)
    web = t.get("website") or t.get("contact:website") or t.get("url") or ""
    return {
        "ad": t.get("name", "").strip(),
        "tur": "firma",
        "sektor": kategori,
        "sehir": t.get("addr:province") or tr_buyuk_ilk(sehir),
        "ilce": t.get("addr:district") or (tr_buyuk_ilk(ilce) if ilce else ""),
        "adres": _adres(t),
        "web": web_normal(web),
        "telefon": telefonlar[0] if telefonlar else "",
        "telefon2": telefonlar[1] if len(telefonlar) > 1 else "",
        "eposta": (t.get("email") or t.get("contact:email") or "").lower(),
        "instagram": t.get("contact:instagram", ""),
        "kaynak": f"https://www.openstreetmap.org/{oge.get('type', 'node')}/{oge.get('id')}",
        "kaynak_turu": "osm",
        "izin": "kurumsal",
        "dis_id": f"osm:{oge.get('type', 'node')}/{oge.get('id')}",
    }


def osm_ara(kategori, sehir, ilce="", ozel_etiket="", ad_icerir="", limit=200):
    if not sehir:
        raise KaynakHatasi("Şehir (il) gerekli")
    if ozel_etiket:
        if "=" not in ozel_etiket:
            raise KaynakHatasi("Özel etiket 'anahtar=değer' biçiminde olmalı (ör. shop=bakery)")
        k, v = ozel_etiket.split("=", 1)
        etiketler = [(k.strip(), v.strip())]
        kategori = kategori or v.strip()
    else:
        etiketler = OSM_KATEGORILER.get(kategori)
        if not etiketler:
            raise KaynakHatasi(f"Bilinmeyen kategori: {kategori}")
    sorgu = overpass_sorgusu(etiketler, sehir, ilce, ad_icerir, limit)
    veri = urllib.parse.urlencode({"data": sorgu}).encode()
    son_hata = None
    for sunucu in OVERPASS_SUNUCULARI:
        try:
            metin, _ = _istek(sunucu, veri, zaman_asimi=100)
            json_veri = json.loads(metin)
            break
        except (urllib.error.URLError, OSError, ValueError) as e:
            son_hata = e
    else:
        raise KaynakHatasi(f"OpenStreetMap'e ulaşılamadı: {son_hata}")
    sonuc = []
    gorulen = set()
    for oge in json_veri.get("elements", []):
        lead = osm_ogesini_leade_cevir(oge, kategori, sehir, ilce)
        if lead["ad"] and lead["dis_id"] not in gorulen:
            gorulen.add(lead["dis_id"])
            sonuc.append(lead)
    if not sonuc and not json_veri.get("elements"):
        uyari = json_veri.get("remark", "")
        if uyari:
            raise KaynakHatasi(f"OpenStreetMap yanıtı: {uyari}")
    return sonuc


# --- Web sitesinden iletişim bilgisi --------------------------------------------
class _BaglantiToplayici(HTMLParser):
    def __init__(self):
        super().__init__()
        self.baglantilar = []  # (href, metin)
        self._href = None
        self._metin = []
        self.metin = []
        self._atla = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self._atla += 1
        if tag == "a":
            self._href = dict(attrs).get("href") or ""
            self._metin = []

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self._atla:
            self._atla -= 1
        if tag == "a" and self._href is not None:
            self.baglantilar.append((self._href, " ".join(self._metin).strip()))
            self._href = None

    def handle_data(self, data):
        if self._atla:
            return
        self.metin.append(data)
        if self._href is not None:
            self._metin.append(data.strip())


EPOSTA_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# +90 / 0 ile başlayan veya 3-3-2-2 gruplu Türk numaraları, 444 numaraları
TELEFON_RE = re.compile(
    r"(?:(?:\+|00)90[\s.\-]?|0[\s.\-]?)?\(?[2-5]\d{2}\)?[\s.\-]?\d{3}[\s.\-]?\d{2}[\s.\-]?\d{2}(?!\d)"
    r"|444[\s.\-]?\d[\s.\-]?\d{3}(?!\d)")
ILETISIM_KELIMELERI = ("iletisim", "iletişim", "contact", "bize-ulas", "bize ulaş", "ulasim", "hakkimizda", "about")
GECERSIZ_EPOSTA = ("example.", "domain.", "sentry", "wixpress", ".png", ".jpg", ".gif", ".webp", ".svg",
                   "@2x", "ornek@", "email@", "name@", "user@")


def _eposta_gecerli(e):
    e = e.lower()
    return not any(g in e for g in GECERSIZ_EPOSTA) and len(e) < 80


def sayfayi_coz(html_metin, taban_url):
    p = _BaglantiToplayici()
    try:
        p.feed(html_metin)
    except Exception:  # bozuk HTML'de elimizdekiyle devam
        pass
    metin = unescape(" ".join(p.metin))
    epostalar, telefonlar, sosyal, iletisim_linkleri = [], [], {}, []

    for href, yazi in p.baglantilar:
        h = unescape(href).strip()
        hl = h.lower()
        if hl.startswith("mailto:"):
            e = urllib.parse.unquote(h[7:].split("?")[0]).strip().lower()
            if EPOSTA_RE.fullmatch(e) and _eposta_gecerli(e) and e not in epostalar:
                epostalar.append(e)
        elif hl.startswith("tel:"):
            n = telefon_normal(urllib.parse.unquote(h[4:]))
            if n.startswith(("+90", "444")) and n not in telefonlar:
                telefonlar.append(n)
        elif "linkedin.com/company" in hl or "linkedin.com/in/" in hl:
            sosyal.setdefault("linkedin", h.split("?")[0])
        elif "instagram.com/" in hl and "/p/" not in hl:
            sosyal.setdefault("instagram", h.split("?")[0])
        elif any(k in hl or k in yazi.lower() for k in ILETISIM_KELIMELERI):
            tam = urllib.parse.urljoin(taban_url, h)
            if urllib.parse.urlparse(tam).netloc == urllib.parse.urlparse(taban_url).netloc \
                    and tam not in iletisim_linkleri:
                iletisim_linkleri.append(tam)

    for e in EPOSTA_RE.findall(metin):
        e = e.lower().strip(".")
        if _eposta_gecerli(e) and e not in epostalar:
            epostalar.append(e)
    for t in TELEFON_RE.findall(metin):
        n = telefon_normal(t)
        if n.startswith(("+90", "444")) and n not in telefonlar:
            telefonlar.append(n)
    return {"epostalar": epostalar, "telefonlar": telefonlar, "sosyal": sosyal,
            "iletisim_linkleri": iletisim_linkleri}


def siteden_iletisim(web, en_fazla_sayfa=3):
    """Ana sayfa + en fazla 2 iletişim/hakkımızda sayfasını tarar."""
    url = web_normal(web)
    if not url:
        raise KaynakHatasi("Web adresi yok")
    toplam = {"epostalar": [], "telefonlar": [], "sosyal": {}, "taranan": []}
    kuyruk = [url]
    hatalar = []
    while kuyruk and len(toplam["taranan"]) < en_fazla_sayfa:
        sayfa = kuyruk.pop(0)
        try:
            metin, gercek_url = _istek(sayfa, zaman_asimi=15)
        except (urllib.error.URLError, OSError, ValueError) as e:
            if sayfa == url and url.startswith("https://"):
                kuyruk.insert(0, "http://" + url[8:])  # bazı eski siteler yalnızca http
                url = "http://" + url[8:]
            hatalar.append(f"{sayfa}: {getattr(e, 'reason', e)}")
            continue
        toplam["taranan"].append(gercek_url)
        sonuc = sayfayi_coz(metin, gercek_url)
        for e in sonuc["epostalar"]:
            if e not in toplam["epostalar"]:
                toplam["epostalar"].append(e)
        for t in sonuc["telefonlar"]:
            if t not in toplam["telefonlar"]:
                toplam["telefonlar"].append(t)
        for k, v in sonuc["sosyal"].items():
            toplam["sosyal"].setdefault(k, v)
        for link in sonuc["iletisim_linkleri"]:
            if link not in toplam["taranan"] and link not in kuyruk:
                kuyruk.append(link)
    if not toplam["taranan"]:
        raise KaynakHatasi("Siteye ulaşılamadı: " + "; ".join(hatalar[:2]))
    return toplam
