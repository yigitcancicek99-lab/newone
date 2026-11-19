"""
Sinyal radarı: projelerin haber sorgularını (Google Haberler RSS) ve eklenen RSS
kaynaklarını düzenli tarar, yeni haberleri kaydeder, yapay zekâ ile
"bu haber bir satın alma sinyali mi, hangi şirket?" diye sınıflandırır ve
yeterince güçlü sinyalleri otomatik olarak müşteri adayı (lead) listesine ekler.
"""

import hashlib
import re
import threading
import time
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from html import unescape

import kaynaklar
import motor
import yz
from sablonlar import GENEL_SINYAL_KELIMELERI

DURUM = {}  # proje_id -> {"calisiyor": bool, "mesaj": str, "sonuc": dict, "zaman": str}
SINIFLANDIRMA_PAKETI = 25
EN_FAZLA_YENI_HABER = 150  # tek taramada sınıflandırılacak en fazla haber


def google_haber_url(sorgu, gun=7):
    q = f"{sorgu} when:{int(gun)}d"
    return ("https://news.google.com/rss/search?" +
            urllib.parse.urlencode({"q": q, "hl": "tr", "gl": "TR", "ceid": "TR:tr"}))


def _etiketsiz(metin):
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", metin or ""))).strip()


def _tarih(metin):
    metin = (metin or "").strip()
    if not metin:
        return ""
    try:
        return parsedate_to_datetime(metin).date().isoformat()
    except (TypeError, ValueError):
        pass
    try:
        return datetime.fromisoformat(metin.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return metin[:10]


def rss_coz(xml_metin):
    """RSS 2.0 ve Atom beslemelerini [{baslik, link, tarih, kaynak, ozet}] listesine çevirir."""
    try:
        kok = ET.fromstring(xml_metin.encode("utf-8") if isinstance(xml_metin, str) else xml_metin)
    except ET.ParseError as e:
        raise kaynaklar.KaynakHatasi(f"Besleme okunamadı: {e}")
    ogeler = []
    for item in kok.iter("item"):
        baslik = _etiketsiz(item.findtext("title"))
        kaynak = _etiketsiz(item.findtext("source"))
        if kaynak and baslik.endswith(" - " + kaynak):
            baslik = baslik[: -len(kaynak) - 3]
        ogeler.append({"baslik": baslik, "link": (item.findtext("link") or "").strip(),
                       "tarih": _tarih(item.findtext("pubDate")), "kaynak": kaynak,
                       "ozet": _etiketsiz(item.findtext("description"))[:800]})
    atom = "{http://www.w3.org/2005/Atom}"
    for entry in kok.iter(atom + "entry"):
        link = entry.find(atom + "link")
        ogeler.append({"baslik": _etiketsiz(entry.findtext(atom + "title")),
                       "link": link.get("href", "") if link is not None else "",
                       "tarih": _tarih(entry.findtext(atom + "updated") or entry.findtext(atom + "published")),
                       "kaynak": _etiketsiz(kok.findtext(atom + "title")),
                       "ozet": _etiketsiz(entry.findtext(atom + "summary") or entry.findtext(atom + "content"))[:800]})
    return [o for o in ogeler if o["baslik"]]


def haber_anahtari(baslik):
    return hashlib.sha1(motor.sade(baslik).encode()).hexdigest()[:20]


def otomatik_sorgular(proje):
    """Mülakat/YZ analizi yapılmamışsa sinyal adları ve sektörlerden basit sorgular üretir."""
    sektorler = proje.get("hedef_sektorler") or [""]
    sorgular = []
    for s in proje.get("sinyaller", [])[:6]:
        for sek in sektorler[:2]:
            sorgular.append(f"{sek} {s['ad']}".strip())
    return sorgular[:12]


def _kelime_puani(haber, proje):
    """YZ yokken kaba ilgililik puanı (0-100) — yalnızca sıralama/inceleme için."""
    metin = motor.sade(haber["baslik"] + " " + haber.get("ozet", ""))
    puan = sum(8 for k in GENEL_SINYAL_KELIMELERI if motor.sade(k) in metin)
    puan += sum(10 for s in proje.get("hedef_sektorler", []) if motor.sade(s) and motor.sade(s) in metin)
    puan += sum(6 for s in proje.get("hedef_sehirler", []) if motor.sade(s) and motor.sade(s) in metin)
    return min(60, puan)


def haberleri_topla(proje, gun=7, getir=kaynaklar._istek):
    """Ağ işlemi: tüm sorgu ve RSS kaynaklarından haberleri çeker (veritabanına dokunmaz)."""
    t = proje["tarama"]
    sorgular = t.get("sorgular") or otomatik_sorgular(proje)
    toplam, hatalar = [], []
    for sorgu in sorgular:
        try:
            metin, _ = getir(google_haber_url(sorgu, gun), zaman_asimi=20)
            for o in rss_coz(metin):
                o["sorgu"] = sorgu
                toplam.append(o)
        except Exception as e:  # tek kaynak hatası taramayı durdurmasın
            hatalar.append(f"{sorgu}: {getattr(e, 'reason', e)}")
    # Ek RSS kaynakları: yalnızca sorgu kelimeleri / sinyal kelimeleri geçenleri al
    anahtar_kelimeler = {motor.sade(k) for s in sorgular for k in s.split() if len(k) > 3}
    anahtar_kelimeler |= {motor.sade(k) for k in GENEL_SINYAL_KELIMELERI}
    for url in t.get("rss") or []:
        try:
            metin, _ = getir(url, zaman_asimi=20)
            for o in rss_coz(metin):
                sade_metin = motor.sade(o["baslik"] + " " + o["ozet"])
                if any(k and k in sade_metin for k in anahtar_kelimeler):
                    o["sorgu"] = "RSS"
                    toplam.append(o)
        except Exception as e:
            hatalar.append(f"{url}: {getattr(e, 'reason', e)}")
    return toplam, hatalar


def tara(db, kilit, proje_id, ist=None, getir=kaynaklar._istek):
    """Tek proje için tam tarama. ist: yz.Istemci (yoksa YZ'siz kaba puanlama)."""
    with kilit:
        proje = motor.proje_getir(db, proje_id)
    if not proje:
        return {}
    DURUM[proje_id] = {"calisiyor": True, "mesaj": "Haberler toplanıyor…", "sonuc": None, "zaman": ""}
    sonuc = {"bulunan": 0, "yeni": 0, "ilgili": 0, "lead_eklenen": 0, "lead_guncellenen": 0,
             "hatalar": [], "yz": bool(ist)}
    try:
        gun = 30 if not proje.get("son_tarama") else 7
        toplanan, sonuc["hatalar"] = haberleri_topla(proje, gun, getir)
        sonuc["bulunan"] = len(toplanan)
        yeniler = []
        with kilit:
            gorulen = set()
            for h in toplanan:
                anahtar = haber_anahtari(h["baslik"])
                if anahtar in gorulen:
                    continue
                gorulen.add(anahtar)
                cur = db.execute(
                    "INSERT OR IGNORE INTO haberler (proje_id, anahtar, baslik, link, kaynak, tarih, ozet, sorgu, "
                    "uygunluk, olusturma) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (proje_id, anahtar, h["baslik"], h["link"], h["kaynak"], h["tarih"], h["ozet"], h["sorgu"],
                     None if ist else _kelime_puani(h, proje), datetime.now().isoformat(timespec="seconds")))
                if cur.rowcount:
                    yeniler.append({**h, "id": cur.lastrowid})
            db.execute("UPDATE projeler SET son_tarama = ? WHERE id = ?",
                       (datetime.now().isoformat(timespec="seconds"), proje_id))
            db.commit()
        sonuc["yeni"] = len(yeniler)
        if ist and yeniler:
            yeniler.sort(key=lambda h: h["tarih"], reverse=True)
            hedef = yeniler[:EN_FAZLA_YENI_HABER]
            for i in range(0, len(hedef), SINIFLANDIRMA_PAKETI):
                DURUM[proje_id]["mesaj"] = f"Yapay zekâ haberleri değerlendiriyor… ({i}/{len(hedef)})"
                paket = hedef[i:i + SINIFLANDIRMA_PAKETI]
                try:
                    degerler = yz.haberleri_siniflandir(ist, proje, paket)
                except yz.YZHatasi as e:
                    sonuc["hatalar"].append(str(e))
                    break
                with kilit:
                    for h in paket:
                        r = degerler.get(h["id"])
                        if r:
                            _siniflandirma_kaydet(db, proje, h, r, sonuc)
                    db.commit()
        DURUM[proje_id].update(calisiyor=False, sonuc=sonuc,
                               mesaj=f"{sonuc['yeni']} yeni haber, {sonuc['ilgili']} ilgili, "
                                     f"{sonuc['lead_eklenen']} yeni aday eklendi.",
                               zaman=datetime.now().isoformat(timespec="seconds"))
    except Exception as e:
        DURUM[proje_id].update(calisiyor=False, mesaj=f"Tarama hatası: {e}", sonuc=sonuc)
        raise
    return sonuc


def _siniflandirma_kaydet(db, proje, haber, r, sonuc):
    sinyal = r.get("sinyal") if r.get("sinyal") != "yok" else ""
    uygunluk = max(0, min(100, int(r.get("uygunluk") or 0)))
    durum = "ilgili" if r.get("ilgili") else "ilgisiz"
    lead_id = None
    esik = int(proje["tarama"].get("otomatik_lead_esik") or 70)
    if r.get("ilgili"):
        sonuc["ilgili"] += 1
    if r.get("ilgili") and uygunluk >= esik and (r.get("sirket") or "").strip():
        lead = {"ad": r["sirket"].strip(), "sektor": r.get("sektor", ""), "sehir": r.get("sehir", ""),
                "sinyal": sinyal, "sinyal_ozet": haber["baslik"][:200], "sinyal_tarihi": haber["tarih"],
                "kaynak": haber["link"], "kaynak_turu": "haber", "izin": "kurumsal",
                "notlar": f"Sinyal radarı: {r.get('neden', '')} Yaklaşım: {r.get('yaklasim', '')}".strip()}
        if (r.get("kisi_ad") or "").strip():
            lead["kisiler"] = [{"ad": r["kisi_ad"], "unvan": r.get("kisi_unvan", ""), "rol": "karar_verici",
                                "kaynak": haber["link"]}]
        mevcut = motor.mukerrer_bul(db, proje["id"], lead)
        if mevcut:
            eski = motor.lead_getir(db, mevcut)
            if sinyal and (haber["tarih"] or "") > (eski.get("sinyal_tarihi") or ""):
                guncel = {k: lead[k] for k in ("sinyal", "sinyal_ozet", "sinyal_tarihi", "kaynak")}
                guncel["notlar"] = ((eski.get("notlar") or "") + "\n" + lead["notlar"]).strip()
                motor.lead_guncelle(db, mevcut, guncel, commit=False)
            if lead.get("kisiler"):
                birlesik = motor.kisileri_birlestir(eski["kisiler"], lead["kisiler"])
                if birlesik != eski["kisiler"]:
                    motor.lead_guncelle(db, mevcut, {"kisiler": birlesik}, commit=False)
                sonuc["lead_guncellenen"] += 1
            lead_id = mevcut
        else:
            lead_id, _ = motor.lead_ekle(db, proje["id"], lead, mukerrer_kontrol=False, commit=False)
            sonuc["lead_eklenen"] += 1
        durum = "lead"
    db.execute("UPDATE haberler SET durum=?, uygunluk=?, sirket=?, sinyal=?, sehir=?, sektor=?, neden=?, "
               "yaklasim=?, lead_id=? WHERE id=?",
               (durum, uygunluk, r.get("sirket", ""), sinyal, r.get("sehir", ""), r.get("sektor", ""),
                r.get("neden", ""), r.get("yaklasim", ""), lead_id, haber["id"]))


def haberleri_listele(db, proje_id, filtre="", limit=300):
    kosul, arg = "proje_id = ?", [proje_id]
    if filtre == "ilgili":
        kosul += " AND durum IN ('ilgili','lead')"
    elif filtre == "incelenmemis":
        kosul += " AND durum = 'yeni'"
    elif filtre == "lead":
        kosul += " AND durum = 'lead'"
    satirlar = db.execute(
        f"SELECT * FROM haberler WHERE {kosul} ORDER BY COALESCE(uygunluk, -1) DESC, tarih DESC LIMIT ?",
        arg + [limit]).fetchall()
    return [dict(s) for s in satirlar]


# --- Zamanlayıcı ---------------------------------------------------------------------
def tarama_zamani_geldi(proje, simdi=None):
    t = proje["tarama"]
    if not t.get("aktif"):
        return False
    if not proje.get("son_tarama"):
        return True
    simdi = simdi or datetime.now()
    try:
        son = datetime.fromisoformat(proje["son_tarama"])
    except ValueError:
        return True
    return simdi - son >= timedelta(hours=float(t.get("aralik_saat") or 12))


def zamanlayici_baslat(db, kilit, istemci_fabrikasi, kontrol_saniye=300):
    """Uygulama açık kaldığı sürece, zamanı gelen projeleri arka planda tarar."""
    def dongu():
        time.sleep(15)
        while True:
            try:
                with kilit:
                    projeler = motor.projeleri_listele(db)
                for p in projeler:
                    if tarama_zamani_geldi(p) and not DURUM.get(p["id"], {}).get("calisiyor"):
                        ist = istemci_fabrikasi() if p["tarama"].get("yz_kullan") else None
                        try:
                            tara(db, kilit, p["id"], ist)
                        except Exception as e:
                            print(f"[sinyal radarı] {p['ad']}: {e}")
            except Exception as e:
                print(f"[sinyal radarı] {e}")
            time.sleep(kontrol_saniye)

    th = threading.Thread(target=dongu, name="sinyal-radari", daemon=True)
    th.start()
    return th

