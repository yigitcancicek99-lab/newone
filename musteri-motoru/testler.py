"""Çalıştırma: python3 -m unittest testler  (musteri-motoru klasöründe)"""

import json
import os
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


if __name__ == "__main__":
    unittest.main()
