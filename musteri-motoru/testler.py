"""Çalıştırma: python3 -m unittest testler  (musteri-motoru klasöründe)"""

import json
import os
import re
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import kaynaklar  # noqa: E402
import motor  # noqa: E402


class NormallestirmeTesti(unittest.TestCase):
    def test_telefon(self):
        for girdi in ["0212 555 11 22", "+90 (212) 555-11-22", "902125551122", "2125551122", "0090 212 5551122"]:
            self.assertEqual(motor.telefon_normal(girdi), "+90 212 555 11 22", girdi)
        self.assertEqual(motor.telefon_normal("0532.123.45.67"), "+90 532 123 45 67")
        self.assertEqual(motor.telefon_normal("444 1 234"), "444 1 234")

    def test_sade_ve_ad_anahtari(self):
        self.assertEqual(motor.sade("İSTANBUL"), "istanbul")
        self.assertEqual(motor.sade("Işık Çağrı"), "isik cagri")
        self.assertEqual(motor.ad_anahtari("Örnek Gıda San. ve Tic. A.Ş."), motor.ad_anahtari("ÖRNEK GIDA"))

    def test_alan_adi(self):
        self.assertEqual(motor.alan_adi("https://www.ornek.com.tr/iletisim"), "ornek.com.tr")
        self.assertEqual(motor.alan_adi("ornek.com"), "ornek.com")


class ProjeVeLeadTesti(unittest.TestCase):
    def setUp(self):
        self.db = motor.baglan(":memory:")
        self.p = motor.proje_olustur(self.db, {"ad": "Test", "sablon": "yazilim_saas",
                                               "hedef_sehirler": "İstanbul, Kocaeli"})

    def test_sablon_uygulanir(self):
        self.assertEqual(self.p["satis_tipi"], "b2b")
        self.assertEqual(self.p["hedef_sehirler"], ["İstanbul", "Kocaeli"])
        self.assertTrue(any(s["kod"] == "yatirim_aldi" for s in self.p["sinyaller"]))

    def test_mukerrer(self):
        pid = self.p["id"]
        _, yeni = motor.lead_ekle(self.db, pid, {"ad": "Örnek Ltd. Şti.", "telefon": "0212 555 11 22"})
        self.assertTrue(yeni)
        lid, yeni = motor.lead_ekle(self.db, pid, {"ad": "Başka ad", "telefon": "+902125551122", "eposta": "a@ornek.com"})
        self.assertFalse(yeni)
        self.assertEqual(motor.lead_getir(self.db, lid)["eposta"], "a@ornek.com")  # boş alan dolduruldu
        _, yeni = motor.lead_ekle(self.db, pid, {"ad": "ÖRNEK", "web": "x.com"})
        self.assertFalse(yeni)  # ad anahtarı aynı
        _, yeni = motor.lead_ekle(self.db, pid, {"ad": "Farklı", "web": "https://www.x.com/"})
        self.assertFalse(yeni)  # alan adı aynı

    def test_puan_siralamasi(self):
        pid = self.p["id"]
        bugun = date(2026, 11, 19)
        motor.lead_ekle(self.db, pid, {"ad": "Sıcak", "sektor": "Sağlık", "sehir": "İstanbul",
                                       "sinyal": "yatirim_aldi", "sinyal_tarihi": "2026-11-15",
                                       "telefon": "02125551122", "eposta": "a@b.com", "yetkili": "X",
                                       "buyukluk": "kucuk", "unvan": "BT Müdürü"})
        motor.lead_ekle(self.db, pid, {"ad": "Soğuk", "sektor": "Madencilik", "sehir": "Van"})
        motor.lead_ekle(self.db, pid, {"ad": "Eski sinyal", "sektor": "sağlık", "sehir": "Kocaeli",
                                       "sinyal": "bt_ilani", "sinyal_tarihi": "2026-06-01"})
        liste = motor.leadleri_listele(self.db, pid, bugun)
        self.assertEqual([l["ad"] for l in liste], ["Sıcak", "Eski sinyal", "Soğuk"])
        self.assertEqual(liste[0]["oncelik"], "A")
        self.assertGreater(liste[0]["puan"], 90)
        self.assertEqual(liste[-1]["oncelik"], "C")

    def test_b2c_izin(self):
        p = motor.proje_olustur(self.db, {"ad": "B2C", "sablon": "b2c_tuketici"})
        motor.lead_ekle(self.db, p["id"], {"ad": "Ayşe", "izin": "acik_riza", "telefon": "05321234567"})
        motor.lead_ekle(self.db, p["id"], {"ad": "Mehmet", "telefon": "05321234568"})
        uygun = {l["ad"]: l["iletisime_uygun"] for l in motor.leadleri_listele(self.db, p["id"])}
        self.assertEqual(uygun, {"Ayşe": True, "Mehmet": False})

    def test_csv_ice_ve_disa(self):
        metin = "﻿Firma Adı;Telefon;E-Posta;İl;Çalışan;Vergi No\nA Ltd;0216 111 22 33;info@a.com;İzmir;12;123\n;;;;;\n"
        liste, esleme, eslesmeyen = motor.csv_coz(metin)
        self.assertEqual(len(liste), 1)
        self.assertEqual(liste[0]["ad"], "A Ltd")
        self.assertEqual(liste[0]["sehir"], "İzmir")
        self.assertIn("Vergi No: 123", liste[0]["notlar"])
        self.assertIn("Vergi No", eslesmeyen)
        sonuc = motor.toplu_ekle(self.db, self.p["id"], liste + [{"ad": ""}])
        self.assertEqual((sonuc["eklenen"], sonuc["hatali"]), (1, 1))
        cikti = motor.csv_uret(motor.leadleri_listele(self.db, self.p["id"]), self.p)
        self.assertTrue(cikti.startswith("﻿Öncelik;Puan;Firma / Kişi"))
        self.assertIn("+90 216 111 22 33", cikti)

    def test_ornek_cornerstone_csv(self):
        yol = os.path.join(os.path.dirname(motor.KOK), "data", "hedef-hesaplar.csv")
        if not os.path.exists(yol):
            self.skipTest("örnek CSV yok")
        with open(yol, encoding="utf-8") as f:
            liste, esleme, _ = motor.csv_coz(f.read())
        self.assertIn("ad", esleme.values())
        self.assertIn("sinyal", esleme.values())
        self.assertGreater(len(liste), 30)


class KaynakTesti(unittest.TestCase):
    def test_sayfa_cozumleme(self):
        html = """<html><body><script>var x="gizli@sentry.io 0212 000 00 00";</script>
        <a href="mailto:info@firma.com.tr?subject=x">Yazın</a>
        <a href="tel:+902165551122">Ara</a> Merkez: (0212) 444-55-66 · GSM 0532 111 22 33
        satis@firma.com.tr <img src="logo@2x.png">
        <a href="/iletisim">İletişim</a> <a href="https://baska.com/contact">dış</a>
        <a href="https://www.linkedin.com/company/firma/?x=1">in</a>
        <a href="https://instagram.com/firma">ig</a></body></html>"""
        s = kaynaklar.sayfayi_coz(html, "https://firma.com.tr/")
        self.assertEqual(s["epostalar"], ["info@firma.com.tr", "satis@firma.com.tr"])
        self.assertEqual(s["telefonlar"], ["+90 216 555 11 22", "+90 212 444 55 66", "+90 532 111 22 33"])
        self.assertEqual(s["iletisim_linkleri"], ["https://firma.com.tr/iletisim"])
        self.assertEqual(s["sosyal"]["linkedin"], "https://www.linkedin.com/company/firma/")
        self.assertEqual(s["sosyal"]["instagram"], "https://instagram.com/firma")

    def test_overpass_sorgusu(self):
        q = kaynaklar.overpass_sorgusu([("amenity", "dentist")], "istanbul", "kadıköy", limit=50)
        self.assertIn('area["name"="İstanbul"]["admin_level"="4"]', q)
        self.assertIn('rel(area.il)["name"="Kadıköy"]', q)
        self.assertIn('nwr["amenity"="dentist"]["name"](area.hedef);', q)
        self.assertIn("out center tags 50;", q)

    def test_osm_cevirme(self):
        oge = json.loads("""{"type":"node","id":42,"tags":{"name":"Gülüş Diş","phone":"0216 333 44 55; +90 532 999 88 77",
            "website":"gulus.com","email":"Info@Gulus.com","addr:street":"Bağdat Caddesi","addr:housenumber":"10",
            "addr:district":"Kadıköy"}}""")
        l = kaynaklar.osm_ogesini_leade_cevir(oge, "Diş kliniği", "istanbul", "")
        self.assertEqual(l["telefon"], "+90 216 333 44 55")
        self.assertEqual(l["telefon2"], "+90 532 999 88 77")
        self.assertEqual(l["web"], "https://gulus.com")
        self.assertEqual(l["eposta"], "info@gulus.com")
        self.assertEqual(l["adres"], "Bağdat Caddesi 10, Kadıköy")
        self.assertEqual(l["sehir"], "İstanbul")
        self.assertEqual(l["dis_id"], "osm:node/42")


# --- Yapay zekâ ve sinyal radarı (Claude API sahte istemciyle) -------------------------
import threading  # noqa: E402
from types import SimpleNamespace  # noqa: E402

import tarayici  # noqa: E402
import yz  # noqa: E402
from sablonlar import MULAKAT_BOLUMLERI  # noqa: E402


class SahteAkis:
    def __init__(self, yanit):
        self.yanit = yanit

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def get_final_message(self):
        return self.yanit


class SahteClaude:
    """anthropic.Anthropic yerine geçer; her istekte sıradaki yanıtı döndürür ve parametreleri kaydeder."""

    def __init__(self, yanitlar):
        self.yanitlar = list(yanitlar)
        self.istekler = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(stream=self._stream))

    def _stream(self, **kw):
        self.istekler.append(kw)
        y = self.yanitlar.pop(0)
        if callable(y):
            y = y(kw)
        if isinstance(y, (dict, list)):
            y = json.dumps(y, ensure_ascii=False)
        if isinstance(y, str):
            y = SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=y)])
        return SahteAkis(y)


RSS = """<?xml version="1.0"?><rss><channel><title>Google Haberler</title>
<item><title>Anadolu Gıda Konya'da 500 milyon TL'lik yeni fabrika yatırımı yapıyor - Dünya</title>
<link>https://haber.example/1</link><pubDate>Mon, 16 Nov 2026 08:00:00 GMT</pubDate><source url="x">Dünya</source>
<description>&lt;a href="x"&gt;Anadolu Gıda&lt;/a&gt; yeni tesis</description></item>
<item><title>Merkez Bankası faiz kararını açıkladı - AA</title><link>https://haber.example/2</link>
<pubDate>Tue, 17 Nov 2026 08:00:00 GMT</pubDate><source url="y">AA</source></item>
</channel></rss>"""


class YZTesti(unittest.TestCase):
    def setUp(self):
        self.db = motor.baglan(":memory:")
        self.p = motor.proje_olustur(self.db, {"ad": "Ambalaj", "sablon": "endustriyel_urun",
                                               "hedef_sehirler": "Konya"})

    def test_mulakat_analizi_ve_istek_parametreleri(self):
        analiz = {"ozet": "x", "ideal_musteri": "Gıda üreticileri", "satis_tipi": "b2b", "teklif_turu": "urun",
                  "hedef_sektorler": ["gıda"], "hedef_sehirler": ["Konya"], "hedef_unvanlar": ["Satın Alma Müdürü"],
                  "hedef_buyuklukler": ["orta"], "sinyaller": [{"kod": "yeni_fabrika", "ad": "Yeni fabrika",
                  "agirlik": 99, "yari_omur": 0, "nasil_tespit": "haber"}], "haber_sorgulari": ["gıda fabrikası yatırım"],
                  "osm_kategoriler": [], "veri_kaynaklari": [], "mesaj_acisi": "", "ilk_temas_mesaji": "",
                  "eksik_sorular": ["Minimum sipariş?"], "riskler": []}
        sahte = SahteClaude([analiz])
        ist = yz.Istemci("anahtar", _istemci=sahte)
        motor.proje_guncelle(self.db, self.p["id"], {"mulakat": {"urun_hizmet": "Gıda ambalajı"}})
        p = motor.proje_getir(self.db, self.p["id"])
        sorular = [(b, k, s) for b, q in MULAKAT_BOLUMLERI for k, s, _ in q]
        sonuc = yz.mulakat_analizi(ist, p, sorular)
        self.assertEqual(sonuc["sinyaller"][0]["agirlik"], 30)  # sınırlandı
        self.assertEqual(sonuc["sinyaller"][0]["yari_omur"], 90)  # geçersiz değer -> varsayılan
        istek = sahte.istekler[0]
        self.assertEqual(istek["model"], "claude-opus-5-5")
        self.assertEqual(istek["fallbacks"], "default")
        self.assertEqual(istek["output_config"]["format"]["type"], "json_schema")
        self.assertIn("Gıda ambalajı", istek["messages"][0]["content"])
        with self.assertRaises(yz.YZHatasi):  # boş mülakat
            yz.mulakat_analizi(ist, self.p, sorular)

    def test_haiku_yedek_parametresi_gondermez_ve_red(self):
        red = SimpleNamespace(stop_reason="refusal", content=[])
        sahte = SahteClaude([red])
        ist = yz.Istemci("a", model="claude-haiku-5-5", _istemci=sahte)
        with self.assertRaises(yz.YZHatasi):
            ist.json_iste("x", {"type": "object"})
        self.assertNotIn("fallbacks", sahte.istekler[0])

    def test_web_arastirma_pause_turn_devam_eder(self):
        dur = SimpleNamespace(stop_reason="pause_turn", content=[SimpleNamespace(type="server_tool_use")])
        bitti = SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text="Rapor: ABC A.Ş.")])
        sahte = SahteClaude([dur, bitti, {"adaylar": [{"ad": "ABC A.Ş.", "web": "abc.com", "sektor": "gıda",
            "sehir": "Konya", "sinyal": "yeni_fabrika", "sinyal_ozet": "", "sinyal_tarihi": "", "kaynak": "",
            "neden": "", "yetkili_unvan": "", "telefon": "", "eposta": ""}]}])
        adaylar, rapor = yz.aday_arastir(yz.Istemci("a", _istemci=sahte), self.p, ["Eski Firma"])
        self.assertEqual(adaylar[0]["ad"], "ABC A.Ş.")
        self.assertEqual(rapor, "Rapor: ABC A.Ş.")
        self.assertEqual(len(sahte.istekler[1]["messages"]), 2)  # asistan içeriği eklenerek devam edildi
        self.assertEqual(sahte.istekler[0]["tools"][0]["type"], "web_search_20260209")
        self.assertIn("Eski Firma", sahte.istekler[0]["messages"][0]["content"])

    def test_rss_coz(self):
        o = tarayici.rss_coz(RSS)
        self.assertEqual(o[0]["baslik"], "Anadolu Gıda Konya'da 500 milyon TL'lik yeni fabrika yatırımı yapıyor")
        self.assertEqual(o[0]["kaynak"], "Dünya")
        self.assertEqual(o[0]["tarih"], "2026-11-16")
        self.assertEqual(o[0]["ozet"], "Anadolu Gıda yeni tesis")

    def test_tarama_otomatik_lead(self):
        motor.proje_guncelle(self.db, self.p["id"], {"tarama": {"sorgular": ["gıda fabrikası"], "otomatik_lead_esik": 70}})
        getirilen = []

        def getir(url, zaman_asimi=0):
            getirilen.append(url)
            return RSS, url

        def sinif(kw):
            icerik = kw["messages"][0]["content"]
            ids = dict((b, int(i)) for i, b in re.findall(r'<haber id="(\d+)">\n<baslik>(.*?)</baslik>', icerik))
            ids = [next(v for k, v in ids.items() if k.startswith("Anadolu")),
                   next(v for k, v in ids.items() if k.startswith("Merkez"))]
            return {"sonuclar": [
                {"id": ids[0], "ilgili": True, "uygunluk": 85, "sirket": "Anadolu Gıda", "sinyal": "yeni_fabrika",
                 "sehir": "Konya", "sektor": "gıda", "neden": "Yeni tesis ambalaj ihtiyacı", "yaklasim": "Tebrik"},
                {"id": ids[1], "ilgili": False, "uygunluk": 5, "sirket": "", "sinyal": "yok", "sehir": "",
                 "sektor": "", "neden": "Makro haber", "yaklasim": ""}]}
        ist = yz.Istemci("a", _istemci=SahteClaude([sinif]))
        sonuc = tarayici.tara(self.db, threading.RLock(), self.p["id"], ist, getir=getir)
        self.assertIn("news.google.com/rss/search", getirilen[0])
        self.assertIn("when%3A30d", getirilen[0])  # ilk tarama 30 gün geriye bakar
        self.assertEqual((sonuc["yeni"], sonuc["ilgili"], sonuc["lead_eklenen"]), (2, 1, 1))
        lead = motor.leadleri_listele(self.db, self.p["id"])[0]
        self.assertEqual((lead["ad"], lead["sinyal"], lead["sinyal_tarihi"], lead["kaynak_turu"]),
                         ("Anadolu Gıda", "yeni_fabrika", "2026-11-16", "haber"))
        self.assertEqual(len(tarayici.haberleri_listele(self.db, self.p["id"], "ilgili")), 1)
        # İkinci tarama: aynı haberler tekrar eklenmez
        sonuc2 = tarayici.tara(self.db, threading.RLock(), self.p["id"], None, getir=getir)
        self.assertEqual(sonuc2["yeni"], 0)
        self.assertIn("when%3A7d", getirilen[-1])

    def test_tarama_zamani(self):
        p = motor.proje_getir(self.db, self.p["id"])
        self.assertFalse(tarayici.tarama_zamani_geldi(p))  # kapalı
        p["tarama"]["aktif"] = True
        self.assertTrue(tarayici.tarama_zamani_geldi(p))
        from datetime import datetime, timedelta
        p["son_tarama"] = (datetime.now() - timedelta(hours=2)).isoformat()
        self.assertFalse(tarayici.tarama_zamani_geldi(p))
        p["tarama"]["aralik_saat"] = 1
        self.assertTrue(tarayici.tarama_zamani_geldi(p))

    def test_eski_veritabani_gocu(self):
        import sqlite3
        import tempfile
        yol = os.path.join(tempfile.mkdtemp(), "eski.db")
        eski = sqlite3.connect(yol)
        eski.executescript(motor.SEMA.split("CREATE TABLE IF NOT EXISTS ayarlar")[0])
        eski.execute("INSERT INTO projeler (ad) VALUES ('eski')")
        eski.commit()
        eski.close()
        db = motor.baglan(yol)
        p = motor.projeleri_listele(db)[0]
        self.assertEqual(p["mulakat"], {})
        self.assertFalse(p["tarama"]["aktif"])


if __name__ == "__main__":
    unittest.main()
