"""
Müşteri Bulma Motoru — çekirdek: veritabanı, puanlama, mükerrer kontrolü,
CSV içe / dışa aktarma. Yalnızca Python standart kütüphanesi.
"""

import csv
import hashlib
import io
import json
import os
import re
import sqlite3
import unicodedata
from datetime import date, datetime
from urllib.parse import urlparse

from sablonlar import SABLONLAR

KOK = os.path.dirname(os.path.abspath(__file__))
VARSAYILAN_DB = os.path.join(KOK, "veri", "motor.db")

LEAD_ALANLARI = [
    "ad", "tur", "sektor", "sehir", "ilce", "adres", "buyukluk",
    "web", "telefon", "telefon2", "eposta", "linkedin", "instagram",
    "whatsapp", "facebook", "x", "iletisim_formu", "kisiler",
    "yetkili", "unvan", "sinyal", "sinyal_ozet", "sinyal_tarihi",
    "kaynak", "kaynak_turu", "izin", "durum", "sonraki_adim", "sonraki_tarih",
    "notlar", "dis_id",
]

PROJE_ALANLARI = [
    "ad", "musteri", "satis_tipi", "teklif_turu", "teklif", "hedef_sektorler",
    "hedef_sehirler", "hedef_unvanlar", "hedef_buyuklukler", "sinyaller",
    "esik_a", "esik_b", "notlar", "mulakat", "yz_analiz", "tarama",
]
PROJE_LISTE_ALANLARI = {"hedef_sektorler", "hedef_sehirler", "hedef_unvanlar", "hedef_buyuklukler", "sinyaller"}
PROJE_SOZLUK_ALANLARI = {"mulakat", "yz_analiz", "tarama"}
VARSAYILAN_TARAMA = {"aktif": False, "aralik_saat": 12, "sorgular": [], "rss": [], "otomatik_lead_esik": 70,
                     "yz_kullan": True}

SEMA = """
CREATE TABLE IF NOT EXISTS projeler (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad TEXT NOT NULL,
    musteri TEXT DEFAULT '',
    satis_tipi TEXT DEFAULT 'b2b',
    teklif_turu TEXT DEFAULT 'hizmet',
    teklif TEXT DEFAULT '',
    hedef_sektorler TEXT DEFAULT '[]',
    hedef_sehirler TEXT DEFAULT '[]',
    hedef_unvanlar TEXT DEFAULT '[]',
    hedef_buyuklukler TEXT DEFAULT '[]',
    sinyaller TEXT DEFAULT '[]',
    esik_a INTEGER DEFAULT 70,
    esik_b INTEGER DEFAULT 50,
    notlar TEXT DEFAULT '',
    olusturma TEXT
);
CREATE TABLE IF NOT EXISTS leadler (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proje_id INTEGER NOT NULL REFERENCES projeler(id) ON DELETE CASCADE,
    ad TEXT NOT NULL,
    tur TEXT DEFAULT 'firma',
    sektor TEXT DEFAULT '', sehir TEXT DEFAULT '', ilce TEXT DEFAULT '',
    adres TEXT DEFAULT '', buyukluk TEXT DEFAULT '',
    web TEXT DEFAULT '', telefon TEXT DEFAULT '', telefon2 TEXT DEFAULT '',
    eposta TEXT DEFAULT '', linkedin TEXT DEFAULT '', instagram TEXT DEFAULT '',
    yetkili TEXT DEFAULT '', unvan TEXT DEFAULT '',
    sinyal TEXT DEFAULT '', sinyal_ozet TEXT DEFAULT '', sinyal_tarihi TEXT DEFAULT '',
    kaynak TEXT DEFAULT '', kaynak_turu TEXT DEFAULT 'manuel',
    izin TEXT DEFAULT 'bilinmiyor',
    durum TEXT DEFAULT 'yeni',
    sonraki_adim TEXT DEFAULT '', sonraki_tarih TEXT DEFAULT '',
    notlar TEXT DEFAULT '', dis_id TEXT DEFAULT '',
    olusturma TEXT, guncelleme TEXT
);
CREATE INDEX IF NOT EXISTS ix_lead_proje ON leadler(proje_id);
CREATE TABLE IF NOT EXISTS ayarlar (anahtar TEXT PRIMARY KEY, deger TEXT);
CREATE TABLE IF NOT EXISTS haberler (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proje_id INTEGER NOT NULL REFERENCES projeler(id) ON DELETE CASCADE,
    anahtar TEXT NOT NULL,
    baslik TEXT, link TEXT, kaynak TEXT, tarih TEXT, ozet TEXT, sorgu TEXT,
    durum TEXT DEFAULT 'yeni',
    uygunluk INTEGER, sirket TEXT DEFAULT '', sinyal TEXT DEFAULT '', sehir TEXT DEFAULT '',
    sektor TEXT DEFAULT '', neden TEXT DEFAULT '', yaklasim TEXT DEFAULT '',
    lead_id INTEGER, olusturma TEXT,
    UNIQUE(proje_id, anahtar)
);
CREATE INDEX IF NOT EXISTS ix_haber_proje ON haberler(proje_id);
"""

# Eski sürüm veritabanlarına eklenecek sütunlar
GOC_SUTUNLARI = {
    "projeler": {"mulakat": "TEXT DEFAULT '{}'", "yz_analiz": "TEXT DEFAULT '{}'",
                 "tarama": "TEXT DEFAULT '{}'", "son_tarama": "TEXT DEFAULT ''"},
    "leadler": {"whatsapp": "TEXT DEFAULT ''", "facebook": "TEXT DEFAULT ''", "x": "TEXT DEFAULT ''",
                "iletisim_formu": "TEXT DEFAULT ''", "kisiler": "TEXT DEFAULT '[]'"},
}

# Bir firmadaki ulaşılabilecek kişiler (karar verici, etkileyen, kullanıcı…)
KISI_ALANLARI = ["ad", "unvan", "rol", "linkedin", "eposta", "telefon", "kaynak", "not"]
KISI_ROLLERI = {"karar_verici": "Karar verici", "etkileyen": "Etkileyen / öneren", "kullanici": "Kullanıcı",
                "kapi": "Kapı açıcı (asistan, santral)", "diger": "Diğer"}


# --- Veritabanı --------------------------------------------------------------
def baglan(yol=VARSAYILAN_DB):
    if yol != ":memory:":
        os.makedirs(os.path.dirname(yol), exist_ok=True)
    db = sqlite3.connect(yol, check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(SEMA)
    for tablo, sutunlar in GOC_SUTUNLARI.items():
        mevcut = {r["name"] for r in db.execute(f"PRAGMA table_info({tablo})")}
        for ad, tanim in sutunlar.items():
            if ad not in mevcut:
                db.execute(f"ALTER TABLE {tablo} ADD COLUMN {ad} {tanim}")
    db.commit()
    return db


def ayar_oku(db, anahtar, varsayilan=""):
    s = db.execute("SELECT deger FROM ayarlar WHERE anahtar = ?", (anahtar,)).fetchone()
    return s["deger"] if s else varsayilan


def ayar_yaz(db, anahtar, deger):
    db.execute("INSERT INTO ayarlar (anahtar, deger) VALUES (?, ?) "
               "ON CONFLICT(anahtar) DO UPDATE SET deger = excluded.deger", (anahtar, deger))
    db.commit()


def _simdi():
    return datetime.now().isoformat(timespec="seconds")


def proje_sozluk(satir):
    p = dict(satir)
    for k in PROJE_LISTE_ALANLARI:
        try:
            p[k] = json.loads(p.get(k) or "[]")
        except ValueError:
            p[k] = []
    for k in PROJE_SOZLUK_ALANLARI:
        try:
            p[k] = json.loads(p.get(k) or "{}") or {}
        except ValueError:
            p[k] = {}
    p["tarama"] = {**VARSAYILAN_TARAMA, **p["tarama"]}
    return p


def projeleri_listele(db):
    satirlar = db.execute(
        "SELECT p.*, (SELECT COUNT(*) FROM leadler l WHERE l.proje_id = p.id) AS lead_sayisi "
        "FROM projeler p ORDER BY p.id DESC").fetchall()
    return [proje_sozluk(s) for s in satirlar]


def proje_getir(db, proje_id):
    s = db.execute("SELECT * FROM projeler WHERE id = ?", (proje_id,)).fetchone()
    return proje_sozluk(s) if s else None


def _proje_degerleri(veri):
    degerler = {}
    for k in PROJE_ALANLARI:
        if k not in veri:
            continue
        v = veri[k]
        if k in PROJE_LISTE_ALANLARI:
            if isinstance(v, str):
                v = [x.strip() for x in v.split(",") if x.strip()]
            v = json.dumps(v, ensure_ascii=False)
        elif k in PROJE_SOZLUK_ALANLARI:
            v = json.dumps(v or {}, ensure_ascii=False)
        elif k in ("esik_a", "esik_b"):
            v = int(v)
        degerler[k] = v
    return degerler


def proje_olustur(db, veri):
    sablon = SABLONLAR.get(veri.get("sablon") or "bos", SABLONLAR["bos"])
    taban = {k: sablon[k] for k in ("satis_tipi", "teklif_turu", "hedef_sektorler",
                                    "hedef_unvanlar", "hedef_buyuklukler", "sinyaller")}
    taban.update({k: v for k, v in veri.items() if v not in (None, "", [])})
    if not (taban.get("ad") or "").strip():
        raise ValueError("Proje adı gerekli")
    degerler = _proje_degerleri(taban)
    degerler["olusturma"] = _simdi()
    alanlar = ", ".join(degerler)
    soru = ", ".join("?" for _ in degerler)
    cur = db.execute(f"INSERT INTO projeler ({alanlar}) VALUES ({soru})", list(degerler.values()))
    db.commit()
    return proje_getir(db, cur.lastrowid)


def proje_guncelle(db, proje_id, veri):
    degerler = _proje_degerleri(veri)
    if degerler:
        atama = ", ".join(f"{k} = ?" for k in degerler)
        db.execute(f"UPDATE projeler SET {atama} WHERE id = ?", [*degerler.values(), proje_id])
        db.commit()
    return proje_getir(db, proje_id)


def proje_sil(db, proje_id):
    db.execute("DELETE FROM haberler WHERE proje_id = ?", (proje_id,))
    db.execute("DELETE FROM leadler WHERE proje_id = ?", (proje_id,))
    db.execute("DELETE FROM projeler WHERE id = ?", (proje_id,))
    db.commit()


# --- Normalleştirme ----------------------------------------------------------
_TR = str.maketrans("çğıöşüÇĞİÖŞÜâîû", "cgiosuCGIOSUaiu")


def sade(metin):
    """Karşılaştırma için: küçük harf, Türkçe karakter ve noktalama yok."""
    metin = (metin or "").replace("İ", "i").replace("I", "ı").lower().translate(_TR)
    metin = unicodedata.normalize("NFKD", metin)
    metin = "".join(c for c in metin if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", metin).strip()


_SIRKET_EKLERI = re.compile(
    r"\b(a s|as|ltd|sti|ltd sti|limited|sirketi|sanayi|san|ticaret|tic|ve|inc|llc|gmbh|co)\b")


def ad_anahtari(ad):
    return re.sub(r"\s+", " ", _SIRKET_EKLERI.sub(" ", sade(ad))).strip()


def telefon_normal(tel):
    """Türk numaralarını +90 5XX XXX XX XX biçimine çevirir; diğerlerini sade bırakır."""
    if not tel:
        return ""
    rakam = re.sub(r"\D", "", tel)
    if rakam.startswith("0090"):
        rakam = rakam[4:]
    elif rakam.startswith("90") and len(rakam) == 12:
        rakam = rakam[2:]
    elif rakam.startswith("0") and len(rakam) == 11:
        rakam = rakam[1:]
    if len(rakam) == 10 and rakam[0] in "2345":
        return f"+90 {rakam[:3]} {rakam[3:6]} {rakam[6:8]} {rakam[8:]}"
    if rakam.startswith("444") and len(rakam) == 7:
        return f"444 {rakam[3]} {rakam[4:]}"
    return tel.strip()


def alan_adi(web):
    if not web:
        return ""
    w = web.strip().lower()
    if "://" not in w:
        w = "http://" + w
    host = urlparse(w).netloc.split(":")[0]
    return host[4:] if host.startswith("www.") else host


def web_normal(web):
    web = (web or "").strip()
    if web and "://" not in web:
        web = "https://" + web
    return web


def linkedin_normal(url):
    url = (url or "").strip()
    if not url:
        return ""
    if "linkedin.com" not in url.lower():
        return url
    if "://" not in url:
        url = "https://" + url
    parca = urlparse(url)
    yol = parca.path.rstrip("/")
    return f"https://www.linkedin.com{yol}" if yol else "https://www.linkedin.com"


def whatsapp_normal(deger):
    """wa.me linki veya numarayı +90 5XX… biçimine çevirir."""
    deger = (deger or "").strip()
    m = re.search(r"(?:wa\.me/|phone=)\+?(\d{10,15})", deger)
    return telefon_normal(m.group(1) if m else deger)


def kisi_temizle(k):
    if not isinstance(k, dict):
        return None
    kisi = {a: str(k.get(a) or "").strip()[:500] for a in KISI_ALANLARI}
    if not (kisi["ad"] or kisi["linkedin"] or kisi["eposta"]):
        return None
    kisi["linkedin"] = linkedin_normal(kisi["linkedin"])
    kisi["telefon"] = telefon_normal(kisi["telefon"])
    kisi["eposta"] = kisi["eposta"].lower()
    if kisi["rol"] not in KISI_ROLLERI:
        kisi["rol"] = "karar_verici" if not kisi["rol"] else "diger"
    kisi["id"] = str(k.get("id") or "") or hashlib.sha1(
        (kisi["linkedin"] or kisi["eposta"] or sade(kisi["ad"])).encode()).hexdigest()[:10]
    return kisi


def kisiler_oku(deger):
    if isinstance(deger, list):
        liste = deger
    else:
        try:
            liste = json.loads(deger or "[]")
        except ValueError:
            liste = []
    return [k for k in (kisi_temizle(x) for x in liste if isinstance(x, dict)) if k]


def kisi_anahtari(k):
    return k.get("linkedin") or k.get("eposta") or sade(k.get("ad"))


def kisileri_birlestir(eski, yeni):
    """Aynı kişiyi (LinkedIn, e-posta veya ad) tekrar eklemez; eksik alanlarını doldurur."""
    sonuc = [dict(k) for k in kisiler_oku(eski)]
    for k in kisiler_oku(yeni):
        mevcut = next((m for m in sonuc if kisi_anahtari(m) == kisi_anahtari(k)
                       or (k["ad"] and sade(m["ad"]) == sade(k["ad"]))), None)
        if mevcut:
            for a in KISI_ALANLARI:
                if k.get(a) and not mevcut.get(a):
                    mevcut[a] = k[a]
        else:
            sonuc.append(k)
    return sonuc


def lead_temizle(veri):
    lead = {k: ("" if veri.get(k) is None else str(veri.get(k)).strip())
            for k in LEAD_ALANLARI if k in veri and k != "kisiler"}
    if "kisiler" in veri:
        lead["kisiler"] = json.dumps(kisiler_oku(veri["kisiler"]), ensure_ascii=False)
    if lead.get("linkedin"):
        lead["linkedin"] = linkedin_normal(lead["linkedin"])
    if lead.get("whatsapp"):
        lead["whatsapp"] = whatsapp_normal(lead["whatsapp"])
    if "telefon" in lead:
        lead["telefon"] = telefon_normal(lead["telefon"])
    if "telefon2" in lead:
        lead["telefon2"] = telefon_normal(lead["telefon2"])
    if "web" in lead:
        lead["web"] = web_normal(lead["web"])
    if "eposta" in lead:
        lead["eposta"] = lead["eposta"].lower()
    if "sinyal_tarihi" in lead and lead["sinyal_tarihi"]:
        lead["sinyal_tarihi"] = tarih_normal(lead["sinyal_tarihi"])
    if "sonraki_tarih" in lead and lead["sonraki_tarih"]:
        lead["sonraki_tarih"] = tarih_normal(lead["sonraki_tarih"])
    return lead


def tarih_normal(metin):
    metin = (metin or "").strip()
    for bicim in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(metin, bicim).date().isoformat()
        except ValueError:
            pass
    return metin


def tarih_oku(metin):
    try:
        return datetime.strptime((metin or "").strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


# --- Puanlama ----------------------------------------------------------------
# Toplam 100: sinyal 30 + tazelik 20 + sektör 20 + konum 10 + büyüklük/unvan 10 + iletişim 10
TAZELIK_MAKS = 20
TARIHSIZ_TAZELIK = 4


def _eslesir(deger, hedefler):
    d = sade(deger)
    if not d:
        return False
    for h in hedefler:
        h = sade(h)
        if h and (h in d or d in h):
            return True
    return False


def puanla(lead, proje, bugun=None):
    bugun = bugun or date.today()
    if lead.get("durum") in ("uygun_degil", "kaybedildi"):
        return 0, "-", {}
    sinyaller = {s["kod"]: s for s in proje.get("sinyaller", [])}

    sinyal = sinyaller.get(lead.get("sinyal") or "")
    if sinyal:
        s_puan = max(0, min(30, float(sinyal.get("agirlik", 0))))
        t = tarih_oku(lead.get("sinyal_tarihi"))
        if t is None:
            tazelik = TARIHSIZ_TAZELIK
        else:
            gun = max((bugun - t).days, 0)
            yari = max(1, float(sinyal.get("yari_omur") or 90))
            tazelik = TAZELIK_MAKS * (0.5 ** (gun / yari))
    else:
        s_puan, tazelik = 0, 0

    hs = proje.get("hedef_sektorler") or []
    sektor = 10 if not hs else (20 if _eslesir(lead.get("sektor"), hs) else 4)

    hc = proje.get("hedef_sehirler") or []
    konum_metin = f"{lead.get('sehir', '')} {lead.get('ilce', '')}"
    konum = 5 if not hc else (10 if _eslesir(konum_metin, hc) else 2)

    # Büyüklük ve unvan uyumu (her biri 5)
    hb = proje.get("hedef_buyuklukler") or []
    buyukluk = 2.5 if not hb or not lead.get("buyukluk") else (5 if lead.get("buyukluk") in hb else 0)
    hu = proje.get("hedef_unvanlar") or []
    unvan = 2.5 if not hu or not lead.get("unvan") else (5 if _eslesir(lead.get("unvan"), hu) else 1)

    kisiler = lead.get("kisiler") or []
    if isinstance(kisiler, str):
        kisiler = kisiler_oku(kisiler)
    iletisim = (5 if lead.get("telefon") or lead.get("telefon2") or lead.get("whatsapp") else 0) \
        + (3 if lead.get("eposta") or any(k.get("eposta") for k in kisiler) else 0) \
        + (2 if lead.get("yetkili") or kisiler else 0)

    toplam = round(s_puan + tazelik + sektor + konum + buyukluk + unvan + iletisim, 1)
    esik_a = proje.get("esik_a", 70)
    esik_b = proje.get("esik_b", 50)
    oncelik = "A" if toplam >= esik_a else "B" if toplam >= esik_b else "C"
    detay = {"sinyal": s_puan, "tazelik": round(tazelik, 1), "sektor": sektor, "konum": konum,
             "buyukluk_unvan": buyukluk + unvan, "iletisim": iletisim}
    return toplam, oncelik, detay


def iletisime_uygun(lead, proje):
    """B2C'de yalnızca açık rızalı kişiler, B2B'de 'izin yok' olmayanlar."""
    izin = lead.get("izin") or "bilinmiyor"
    if proje.get("satis_tipi") == "b2c":
        return izin == "acik_riza"
    return izin != "yok"


# --- Lead işlemleri ----------------------------------------------------------
def leadleri_listele(db, proje_id, bugun=None):
    proje = proje_getir(db, proje_id)
    if not proje:
        return []
    satirlar = [_lead_sozluk(s) for s in db.execute(
        "SELECT * FROM leadler WHERE proje_id = ?", (proje_id,)).fetchall()]
    for s in satirlar:
        s["puan"], s["oncelik"], s["puan_detay"] = puanla(s, proje, bugun)
        s["iletisime_uygun"] = iletisime_uygun(s, proje)
    satirlar.sort(key=lambda s: s["puan"], reverse=True)
    return satirlar


def _lead_sozluk(satir):
    l = dict(satir)
    l["kisiler"] = kisiler_oku(l.get("kisiler"))
    return l


def lead_getir(db, lead_id):
    s = db.execute("SELECT * FROM leadler WHERE id = ?", (lead_id,)).fetchone()
    return _lead_sozluk(s) if s else None


def mukerrer_bul(db, proje_id, lead):
    """Aynı projede aynı telefon, alan adı, e-posta, dış kaynak id'si veya ad+şehir varsa id döndürür."""
    mevcutlar = db.execute(
        "SELECT id, ad, sehir, telefon, telefon2, web, eposta, dis_id FROM leadler WHERE proje_id = ?",
        (proje_id,)).fetchall()
    tel = re.sub(r"\D", "", lead.get("telefon") or "")[-10:]
    alan = alan_adi(lead.get("web"))
    posta = (lead.get("eposta") or "").lower()
    anahtar = ad_anahtari(lead.get("ad"))
    sehir = sade(lead.get("sehir"))
    dis_id = lead.get("dis_id") or ""
    for m in mevcutlar:
        if dis_id and m["dis_id"] == dis_id:
            return m["id"]
        if len(tel) == 10 and tel in (re.sub(r"\D", "", m["telefon"] or "")[-10:],
                                      re.sub(r"\D", "", m["telefon2"] or "")[-10:]):
            return m["id"]
        if alan and alan == alan_adi(m["web"]):
            return m["id"]
        if posta and posta == (m["eposta"] or "").lower():
            return m["id"]
        if anahtar and anahtar == ad_anahtari(m["ad"]) and (not sehir or not m["sehir"] or sehir == sade(m["sehir"])):
            return m["id"]
    return None


def lead_ekle(db, proje_id, veri, mukerrer_kontrol=True, commit=True):
    """(id, yeni_mi) döndürür. Mükerrer varsa boş alanlarını doldurur."""
    lead = lead_temizle(veri)
    if not lead.get("ad"):
        raise ValueError("Lead adı (firma veya kişi) gerekli")
    if mukerrer_kontrol:
        mevcut = mukerrer_bul(db, proje_id, lead)
        if mevcut:
            eski = lead_getir(db, mevcut)
            eksik = {k: v for k, v in lead.items() if v and not eski.get(k) and k != "kisiler"}
            if lead.get("kisiler") and lead["kisiler"] != "[]":
                birlesik = kisileri_birlestir(eski["kisiler"], lead["kisiler"])
                if birlesik != eski["kisiler"]:
                    eksik["kisiler"] = birlesik
            if eksik:
                lead_guncelle(db, mevcut, eksik, commit=commit)
            return mevcut, False
    lead.setdefault("durum", "yeni")
    if not lead.get("durum"):
        lead["durum"] = "yeni"
    lead["proje_id"] = proje_id
    lead["olusturma"] = lead["guncelleme"] = _simdi()
    alanlar = ", ".join(lead)
    soru = ", ".join("?" for _ in lead)
    cur = db.execute(f"INSERT INTO leadler ({alanlar}) VALUES ({soru})", list(lead.values()))
    if commit:
        db.commit()
    return cur.lastrowid, True


def lead_guncelle(db, lead_id, veri, commit=True):
    lead = lead_temizle(veri)
    if "ad" in lead and not lead["ad"]:
        raise ValueError("Lead adı boş olamaz")
    if lead:
        lead["guncelleme"] = _simdi()
        atama = ", ".join(f"{k} = ?" for k in lead)
        db.execute(f"UPDATE leadler SET {atama} WHERE id = ?", [*lead.values(), lead_id])
        if commit:
            db.commit()
    return lead_getir(db, lead_id)


def lead_sil(db, lead_id):
    db.execute("DELETE FROM leadler WHERE id = ?", (lead_id,))
    db.commit()


def toplu_ekle(db, proje_id, liste):
    sonuc = {"eklenen": 0, "mukerrer": 0, "hatali": 0, "hatalar": []}
    for i, veri in enumerate(liste, 1):
        try:
            _, yeni = lead_ekle(db, proje_id, veri, commit=False)
            sonuc["eklenen" if yeni else "mukerrer"] += 1
        except ValueError as e:
            sonuc["hatali"] += 1
            if len(sonuc["hatalar"]) < 10:
                sonuc["hatalar"].append(f"Satır {i}: {e}")
    db.commit()
    return sonuc


# --- CSV ---------------------------------------------------------------------
# Başlık eş anlamlıları (sade() uygulanmış hâlleriyle karşılaştırılır)
BASLIK_ESLEME = {
    "ad": ["ad", "firma", "firma adi", "sirket", "sirket adi", "unvan firma", "isletme", "company",
           "company name", "name", "ad soyad", "musteri", "kurum", "title firma"],
    "sektor": ["sektor", "sector", "industry", "kategori", "category", "faaliyet", "segment"],
    "sehir": ["sehir", "il", "city", "province", "konum"],
    "ilce": ["ilce", "district", "semt"],
    "adres": ["adres", "address", "acik adres"],
    "buyukluk": ["buyukluk", "calisan sayisi", "employees", "size", "personel"],
    "web": ["web", "website", "web sitesi", "site", "url", "internet sitesi", "domain"],
    "telefon": ["telefon", "tel", "phone", "telefon no", "telefon numarasi", "gsm", "cep", "mobile",
                "phone number", "sabit telefon"],
    "telefon2": ["telefon 2", "telefon2", "tel 2", "cep telefonu", "phone 2"],
    "eposta": ["eposta", "e posta", "email", "e mail", "mail", "mail adresi", "e posta adresi"],
    "linkedin": ["linkedin", "linkedin url"],
    "instagram": ["instagram"],
    "whatsapp": ["whatsapp", "whatsapp hatti", "wp"],
    "facebook": ["facebook"],
    "x": ["x", "twitter"],
    "iletisim_formu": ["iletisim formu", "contact form"],
    "yetkili": ["yetkili", "yetkili kisi", "ilgili kisi", "contact", "contact name", "hedef kisi", "kisi"],
    "unvan": ["unvan", "pozisyon", "gorev", "job title", "position", "hedef unvan"],
    "sinyal": ["sinyal", "sinyal turu", "signal"],
    "sinyal_ozet": ["sinyal ozeti", "sinyal ozet", "olay", "aciklama", "description"],
    "sinyal_tarihi": ["sinyal tarihi", "olay tarihi", "tarih", "date"],
    "kaynak": ["kaynak", "source", "kaynak link"],
    "izin": ["izin", "riza", "acik riza", "consent", "iys"],
    "durum": ["durum", "status", "asama"],
    "sonraki_adim": ["sonraki adim", "next step"],
    "sonraki_tarih": ["sonraki adim tarihi", "sonraki tarih", "takip tarihi"],
    "notlar": ["notlar", "not", "notes", "aciklamalar"],
}


def basliklari_esle(basliklar):
    esleme = {}
    kullanilan = set()
    for i, b in enumerate(basliklar):
        bs = sade(b)
        for alan, esler in BASLIK_ESLEME.items():
            if alan in kullanilan:
                continue
            if bs in esler or bs == alan:
                esleme[i] = alan
                kullanilan.add(alan)
                break
    return esleme


def csv_coz(metin):
    """CSV metnini (virgül/noktalı virgül/sekme) lead sözlükleri listesine çevirir."""
    metin = metin.lstrip("﻿")
    ilk = metin.split("\n", 1)[0]
    ayirici = max([",", ";", "\t"], key=ilk.count)
    okuyucu = csv.reader(io.StringIO(metin), delimiter=ayirici)
    satirlar = [s for s in okuyucu if any(h.strip() for h in s)]
    if not satirlar:
        return [], {}, []
    basliklar = satirlar[0]
    esleme = basliklari_esle(basliklar)
    eslesmeyen = [b for i, b in enumerate(basliklar) if i not in esleme and b.strip()]
    liste = []
    for s in satirlar[1:]:
        lead = {}
        ekstra = []
        for i, deger in enumerate(s):
            if i in esleme:
                lead[esleme[i]] = deger
            elif i < len(basliklar) and deger.strip() and basliklar[i].strip():
                ekstra.append(f"{basliklar[i].strip()}: {deger.strip()}")
        if ekstra:
            lead["notlar"] = "; ".join(filter(None, [lead.get("notlar", "")] + ekstra))
        lead.setdefault("kaynak_turu", "csv")
        liste.append(lead)
    return liste, {basliklar[i]: a for i, a in esleme.items()}, eslesmeyen


DISA_ALANLAR = [
    ("oncelik", "Öncelik"), ("puan", "Puan"), ("ad", "Firma / Kişi"), ("sektor", "Sektör"),
    ("sehir", "Şehir"), ("ilce", "İlçe"), ("adres", "Adres"), ("buyukluk", "Büyüklük"),
    ("yetkili", "Yetkili"), ("unvan", "Unvan"), ("telefon", "Telefon"), ("telefon2", "Telefon 2"),
    ("eposta", "E-posta"), ("whatsapp", "WhatsApp"), ("web", "Web"), ("iletisim_formu", "İletişim formu"),
    ("linkedin", "LinkedIn (şirket)"), ("instagram", "Instagram"), ("facebook", "Facebook"), ("x", "X / Twitter"),
    ("kisi1_ad", "Kişi 1"), ("kisi1_unvan", "Kişi 1 unvan"), ("kisi1_linkedin", "Kişi 1 LinkedIn"), ("kisi1_eposta", "Kişi 1 e-posta"),
    ("kisi2_ad", "Kişi 2"), ("kisi2_unvan", "Kişi 2 unvan"), ("kisi2_linkedin", "Kişi 2 LinkedIn"), ("kisi2_eposta", "Kişi 2 e-posta"),
    ("kisi3_ad", "Kişi 3"), ("kisi3_unvan", "Kişi 3 unvan"), ("kisi3_linkedin", "Kişi 3 LinkedIn"), ("kisi3_eposta", "Kişi 3 e-posta"),
    ("diger_kisiler", "Diğer kişiler"),
    ("sinyal_ad", "Sinyal"), ("sinyal_ozet", "Sinyal özeti"), ("sinyal_tarihi", "Sinyal tarihi"),
    ("kaynak", "Kaynak"), ("izin", "İzin"), ("durum", "Durum"), ("sonraki_adim", "Sonraki adım"),
    ("sonraki_tarih", "Sonraki tarih"), ("notlar", "Notlar"),
]


def csv_uret(leadler, proje):
    """Excel (Türkçe) ile doğrudan açılan, ; ayrılmış UTF-8 BOM'lu CSV."""
    sinyal_adlari = {s["kod"]: s["ad"] for s in proje.get("sinyaller", [])}
    cikti = io.StringIO()
    cikti.write("﻿")
    yazici = csv.writer(cikti, delimiter=";")
    yazici.writerow([b for _, b in DISA_ALANLAR])
    for l in leadler:
        l = dict(l, sinyal_ad=sinyal_adlari.get(l.get("sinyal"), l.get("sinyal", "")))
        kisiler = sorted(kisiler_oku(l.get("kisiler")), key=lambda k: list(KISI_ROLLERI).index(k["rol"]))
        for i, k in enumerate(kisiler[:3], 1):
            for a in ("ad", "unvan", "linkedin", "eposta"):
                l[f"kisi{i}_{a}"] = k.get(a, "")
        l["diger_kisiler"] = "; ".join(
            " – ".join(x for x in (k["ad"], k["unvan"], k["linkedin"] or k["eposta"]) if x) for k in kisiler[3:])
        yazici.writerow([l.get(k, "") for k, _ in DISA_ALANLAR])
    return cikti.getvalue()
