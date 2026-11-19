#!/usr/bin/env python3
"""
Müşteri Bulma Motoru — yerel web uygulaması.

Çalıştırma:
    python3 sunucu.py              # http://127.0.0.1:8765 adresini tarayıcıda açar
    python3 sunucu.py --port 9000 --tarayici-acma
    python3 sunucu.py --db /yol/motor.db

Yalnızca Python standart kütüphanesi kullanır (Python 3.8+).
"""

import argparse
import html
import json
import mimetypes
import os
import re
import sys
import threading
import webbrowser
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import kaynaklar  # noqa: E402
import motor  # noqa: E402
from sablonlar import BUYUKLUKLER, DURUMLAR, IZINLER, OSM_KATEGORILER, SABLONLAR  # noqa: E402

WEB_KLASORU = os.path.join(motor.KOK, "web")
ORNEK_CSV = os.path.join(os.path.dirname(motor.KOK), "data", "hedef-hesaplar.csv")
KILIT = threading.Lock()  # SQLite bağlantısı iş parçacıkları arasında paylaşılıyor


class Hata(Exception):
    def __init__(self, mesaj, kod=400):
        super().__init__(mesaj)
        self.kod = kod


class Uygulama:
    def __init__(self, db_yolu):
        self.db = motor.baglan(db_yolu)
        self.rotalar = [
            ("GET", r"/api/ayarlar", self.ayarlar),
            ("GET", r"/api/projeler", self.projeler),
            ("POST", r"/api/projeler", self.proje_olustur),
            ("POST", r"/api/ornek-proje", self.ornek_proje),
            ("GET", r"/api/projeler/(\d+)", self.proje),
            ("PUT", r"/api/projeler/(\d+)", self.proje_guncelle),
            ("DELETE", r"/api/projeler/(\d+)", self.proje_sil),
            ("GET", r"/api/projeler/(\d+)/leadler", self.leadler),
            ("POST", r"/api/projeler/(\d+)/leadler", self.lead_ekle),
            ("POST", r"/api/projeler/(\d+)/ice-aktar", self.ice_aktar),
            ("POST", r"/api/projeler/(\d+)/osm-ara", self.osm_ara),
            ("GET", r"/api/projeler/(\d+)/disa-aktar", self.disa_aktar),
            ("GET", r"/api/projeler/(\d+)/rapor", self.rapor),
            ("PUT", r"/api/leadler/(\d+)", self.lead_guncelle),
            ("DELETE", r"/api/leadler/(\d+)", self.lead_sil),
            ("POST", r"/api/leadler/(\d+)/zenginlestir", self.zenginlestir),
        ]

    # --- yardımcılar ---
    def _proje(self, pid):
        p = motor.proje_getir(self.db, int(pid))
        if not p:
            raise Hata("Proje bulunamadı", 404)
        return p

    # --- uç noktalar ---
    def ayarlar(self, istek):
        return {
            "sablonlar": {k: {"ad": v["ad"], "aciklama": v["aciklama"], "satis_tipi": v["satis_tipi"]}
                          for k, v in SABLONLAR.items()},
            "osm_kategoriler": list(OSM_KATEGORILER),
            "buyuklukler": BUYUKLUKLER, "durumlar": DURUMLAR, "izinler": IZINLER,
            "ornek_var": os.path.exists(ORNEK_CSV),
        }

    def projeler(self, istek):
        return motor.projeleri_listele(self.db)

    def proje(self, istek, pid):
        return self._proje(pid)

    def proje_olustur(self, istek):
        try:
            return motor.proje_olustur(self.db, istek["govde"])
        except ValueError as e:
            raise Hata(str(e))

    def proje_guncelle(self, istek, pid):
        self._proje(pid)
        return motor.proje_guncelle(self.db, int(pid), istek["govde"])

    def proje_sil(self, istek, pid):
        motor.proje_sil(self.db, int(pid))
        return {"tamam": True}

    def leadler(self, istek, pid):
        self._proje(pid)
        return motor.leadleri_listele(self.db, int(pid))

    def lead_ekle(self, istek, pid):
        self._proje(pid)
        govde = istek["govde"]
        liste = govde if isinstance(govde, list) else govde.get("leadler") or [govde]
        return motor.toplu_ekle(self.db, int(pid), liste)

    def ice_aktar(self, istek, pid):
        self._proje(pid)
        liste, esleme, eslesmeyen = motor.csv_coz(istek["govde"].get("csv", ""))
        if not liste:
            raise Hata("CSV boş veya okunamadı")
        if "ad" not in esleme.values():
            raise Hata("Firma/kişi adı sütunu bulunamadı. Başlıklardan biri 'Firma', 'Şirket', "
                       "'Ad' veya 'Name' olmalı. Bulunan başlıklar: " + ", ".join(esleme) +
                       (", " if esleme else "") + ", ".join(eslesmeyen))
        varsayilan = istek["govde"].get("varsayilan") or {}
        for l in liste:
            for k, v in varsayilan.items():
                if v and not l.get(k):
                    l[k] = v
        sonuc = motor.toplu_ekle(self.db, int(pid), liste)
        sonuc.update({"esleme": esleme, "eslesmeyen": eslesmeyen})
        return sonuc

    def osm_ara(self, istek, pid):
        self._proje(pid)
        g = istek["govde"]
        try:
            adaylar = kaynaklar.osm_ara(g.get("kategori", ""), g.get("sehir", ""), g.get("ilce", ""),
                                        g.get("ozel_etiket", ""), g.get("ad_icerir", ""),
                                        int(g.get("limit") or 200))
        except kaynaklar.KaynakHatasi as e:
            raise Hata(str(e), 502)
        for a in adaylar:
            a["mukerrer"] = bool(motor.mukerrer_bul(self.db, int(pid), a))
        return adaylar

    def disa_aktar(self, istek, pid):
        p = self._proje(pid)
        leadler = motor.leadleri_listele(self.db, int(pid))
        leadler = _filtrele(leadler, istek["sorgu"])
        dosya = re.sub(r"[^\w-]+", "-", motor.sade(p["ad"])) or "leadler"
        return {"_ham": motor.csv_uret(leadler, p).encode("utf-8"),
                "_tur": "text/csv; charset=utf-8",
                "_dosya": f"{dosya}-{date.today().isoformat()}.csv"}

    def rapor(self, istek, pid):
        p = self._proje(pid)
        leadler = _filtrele(motor.leadleri_listele(self.db, int(pid)), istek["sorgu"])
        return {"_ham": rapor_html(p, leadler).encode("utf-8"), "_tur": "text/html; charset=utf-8"}

    def lead_guncelle(self, istek, lid):
        if not motor.lead_getir(self.db, int(lid)):
            raise Hata("Lead bulunamadı", 404)
        try:
            return motor.lead_guncelle(self.db, int(lid), istek["govde"])
        except ValueError as e:
            raise Hata(str(e))

    def lead_sil(self, istek, lid):
        motor.lead_sil(self.db, int(lid))
        return {"tamam": True}

    def zenginlestir(self, istek, lid):
        lead = motor.lead_getir(self.db, int(lid))
        if not lead:
            raise Hata("Lead bulunamadı", 404)
        if not lead.get("web"):
            raise Hata("Bu kaydın web adresi yok")
        KILIT.release()  # ağ isteği sürerken diğer istekleri bekletme
        try:
            bulunan = kaynaklar.siteden_iletisim(lead["web"])
        except kaynaklar.KaynakHatasi as e:
            raise Hata(str(e), 502)
        finally:
            KILIT.acquire()
        lead = motor.lead_getir(self.db, int(lid))
        guncel = {}
        tel = [t for t in bulunan["telefonlar"] if t not in (lead["telefon"], lead["telefon2"])]
        if not lead["telefon"] and tel:
            guncel["telefon"] = tel.pop(0)
        if not lead["telefon2"] and tel:
            guncel["telefon2"] = tel.pop(0)
        if not lead["eposta"] and bulunan["epostalar"]:
            alan = motor.alan_adi(lead["web"])
            ayni_alan = [e for e in bulunan["epostalar"] if e.endswith("@" + alan)]
            guncel["eposta"] = (ayni_alan or bulunan["epostalar"])[0]
        for k in ("linkedin", "instagram"):
            if not lead[k] and bulunan["sosyal"].get(k):
                guncel[k] = bulunan["sosyal"][k]
        if lead.get("izin") in ("", "bilinmiyor") and guncel:
            guncel["izin"] = "kurumsal"
        if guncel:
            lead = motor.lead_guncelle(self.db, int(lid), guncel)
        return {"lead": lead, "bulunan": bulunan, "guncellenen": list(guncel)}

    def ornek_proje(self, istek):
        """Depodaki Cornerstone hedef hesaplarından örnek proje kurar."""
        if not os.path.exists(ORNEK_CSV):
            raise Hata("Örnek veri dosyası bulunamadı", 404)
        p = motor.proje_olustur(self.db, {
            "ad": "Cornerstone Türkiye – yönetici arama", "musteri": "Cornerstone Executive Search",
            "sablon": "yonetici_arama", "teklif": "Üst düzey yönetici araması, YK araması, halef planlaması",
            "esik_a": 70, "esik_b": 55,
        })
        with open(ORNEK_CSV, encoding="utf-8") as f:
            liste, _, _ = motor.csv_coz(f.read())
        for l in liste:
            if l.get("durum") == "off-limits":
                l["durum"], l["izin"] = "uygun_degil", "yok"
            l["izin"] = l.get("izin") or "kurumsal"
        motor.toplu_ekle(self.db, p["id"], liste)
        return motor.proje_getir(self.db, p["id"])


def _filtrele(leadler, sorgu):
    oncelik = sorgu.get("oncelik", [""])[0]
    durum = sorgu.get("durum", [""])[0]
    if oncelik:
        leadler = [l for l in leadler if l["oncelik"] in oncelik.split(",")]
    if durum:
        leadler = [l for l in leadler if l["durum"] in durum.split(",")]
    if sorgu.get("uygun", [""])[0] == "1":
        leadler = [l for l in leadler if l["iletisime_uygun"]]
    if sorgu.get("telefonlu", [""])[0] == "1":
        leadler = [l for l in leadler if l["telefon"] or l["telefon2"]]
    return leadler


def rapor_html(p, leadler):
    """Müşteriye teslim edilebilecek, yazdırılabilir lead raporu."""
    e = html.escape
    sinyal_adlari = {s["kod"]: s["ad"] for s in p.get("sinyaller", [])}
    say = {k: sum(1 for l in leadler if l["oncelik"] == k) for k in "ABC"}
    telefonlu = sum(1 for l in leadler if l["telefon"] or l["telefon2"])
    epostali = sum(1 for l in leadler if l["eposta"])
    satirlar = []
    for i, l in enumerate(leadler, 1):
        iletisim = "<br>".join(e(x) for x in [l["telefon"], l["telefon2"], l["eposta"]] if x)
        kisi = " – ".join(e(x) for x in [l["yetkili"], l["unvan"]] if x)
        sinyal = e(sinyal_adlari.get(l["sinyal"], l["sinyal"]))
        if l["sinyal_ozet"]:
            sinyal += f"<div class='k'>{e(l['sinyal_ozet'])}</div>"
        web = f"<div class='k'>{e(motor.alan_adi(l['web']))}</div>" if l["web"] else ""
        satirlar.append(
            f"<tr><td>{i}</td><td><span class='r {l['oncelik']}'>{l['oncelik']}</span> {l['puan']:.0f}</td>"
            f"<td><b>{e(l['ad'])}</b>{web}</td><td>{e(l['sektor'])}</td>"
            f"<td>{e(' / '.join(x for x in [l['sehir'], l['ilce']] if x))}</td>"
            f"<td>{kisi}</td><td>{iletisim}</td><td>{sinyal}</td></tr>")
    musteri = f" · {e(p['musteri'])}" if p.get("musteri") else ""
    return f"""<!doctype html><html lang="tr"><head><meta charset="utf-8">
<title>{e(p['ad'])} – Müşteri listesi</title>
<style>
body{{font:13px/1.45 system-ui,-apple-system,Segoe UI,sans-serif;color:#1d2433;margin:32px;}}
h1{{font-size:22px;margin:0}} .alt{{color:#667085;margin:4px 0 20px}}
.kutular{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px}}
.kutu{{border:1px solid #e3e6ec;border-radius:8px;padding:10px 14px;min-width:110px}}
.kutu b{{display:block;font-size:20px}} .kutu span{{color:#667085;font-size:12px}}
table{{border-collapse:collapse;width:100%}} th,td{{text-align:left;padding:7px 8px;border-bottom:1px solid #eceef2;vertical-align:top}}
th{{font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:#667085}}
.k{{color:#667085;font-size:12px}} .r{{display:inline-block;width:20px;text-align:center;border-radius:4px;font-weight:700;color:#fff}}
.r.A{{background:#1a7f4b}} .r.B{{background:#c98a0b}} .r.C{{background:#8a94a6}} .r.-{{background:#ccc}}
.dip{{margin-top:24px;color:#667085;font-size:11px}}
@media print{{body{{margin:12mm}} .yazdir{{display:none}}}}
</style></head><body>
<button class="yazdir" onclick="print()" style="float:right">Yazdır / PDF</button>
<h1>{e(p['ad'])}</h1>
<div class="alt">Hazırlanma: {date.today().strftime('%d.%m.%Y')}{musteri}{(' · ' + e(p['teklif'])) if p.get('teklif') else ''}</div>
<div class="kutular">
<div class="kutu"><b>{len(leadler)}</b><span>Toplam hedef</span></div>
<div class="kutu"><b>{say['A']}</b><span>A – öncelikli</span></div>
<div class="kutu"><b>{say['B']}</b><span>B – yakın takip</span></div>
<div class="kutu"><b>{telefonlu}</b><span>Telefonu olan</span></div>
<div class="kutu"><b>{epostali}</b><span>E-postası olan</span></div>
</div>
<table><thead><tr><th>#</th><th>Öncelik</th><th>Firma / Kişi</th><th>Sektör</th><th>Konum</th>
<th>Yetkili</th><th>İletişim</th><th>Sinyal</th></tr></thead><tbody>{''.join(satirlar)}</tbody></table>
<div class="dip">Puan = sinyal ağırlığı + sinyal tazeliği + sektör uyumu + konum + büyüklük/unvan uyumu + iletişim bilgisi tamlığı (0–100).
İletişim bilgileri kurumların kamuya açık kaynaklarından derlenmiştir. Bireylere ticari ileti göndermeden önce İYS onayı gereklidir.
OpenStreetMap kaynaklı veriler © OpenStreetMap katkıcıları (ODbL).</div>
</body></html>"""


def isleyici_olustur(uygulama):
    class Isleyici(BaseHTTPRequestHandler):
        server_version = "MusteriMotoru/1.0"

        def log_message(self, bicim, *args):
            if os.environ.get("MOTOR_LOG"):
                super().log_message(bicim, *args)

        def _gonder(self, kod, govde, tur="application/json; charset=utf-8", dosya=None):
            if not isinstance(govde, (bytes, bytearray)):
                govde = json.dumps(govde, ensure_ascii=False).encode("utf-8")
            self.send_response(kod)
            self.send_header("Content-Type", tur)
            self.send_header("Content-Length", str(len(govde)))
            self.send_header("Cache-Control", "no-store")
            if dosya:
                self.send_header("Content-Disposition", f"attachment; filename*=UTF-8''{quote(dosya)}")
            self.end_headers()
            self.wfile.write(govde)

        def _statik(self, yol):
            if yol in ("", "/"):
                yol = "/index.html"
            tam = os.path.normpath(os.path.join(WEB_KLASORU, yol.lstrip("/")))
            if not tam.startswith(WEB_KLASORU) or not os.path.isfile(tam):
                return self._gonder(404, {"hata": "Bulunamadı"})
            tur = mimetypes.guess_type(tam)[0] or "application/octet-stream"
            if tur.startswith("text/") or tur.endswith("javascript"):
                tur += "; charset=utf-8"
            with open(tam, "rb") as f:
                self._gonder(200, f.read(), tur)

        def _islem(self, yontem):
            url = urlparse(self.path)
            if not url.path.startswith("/api/"):
                if yontem == "GET":
                    return self._statik(url.path)
                return self._gonder(405, {"hata": "İzin verilmeyen yöntem"})
            # Yalnızca bu bilgisayardan gelen isteklere yanıt ver (DNS rebinding koruması)
            host = (self.headers.get("Host") or "").split(":")[0]
            if host not in ("127.0.0.1", "localhost"):
                return self._gonder(403, {"hata": "Yalnızca yerel erişim"})
            govde = {}
            uzunluk = int(self.headers.get("Content-Length") or 0)
            if uzunluk:
                try:
                    govde = json.loads(self.rfile.read(uzunluk).decode("utf-8"))
                except ValueError:
                    return self._gonder(400, {"hata": "Geçersiz JSON"})
            istek = {"govde": govde, "sorgu": parse_qs(url.query)}
            for r_yontem, desen, fonk in uygulama.rotalar:
                m = re.fullmatch(desen, url.path)
                if r_yontem == yontem and m:
                    try:
                        with KILIT:
                            sonuc = fonk(istek, *m.groups())
                    except Hata as e:
                        return self._gonder(e.kod, {"hata": str(e)})
                    except Exception as e:  # beklenmeyen hata: arayüze ilet
                        return self._gonder(500, {"hata": f"Sunucu hatası: {e}"})
                    if isinstance(sonuc, dict) and "_ham" in sonuc:
                        return self._gonder(200, sonuc["_ham"], sonuc["_tur"], sonuc.get("_dosya"))
                    return self._gonder(200, sonuc)
            return self._gonder(404, {"hata": "Uç nokta bulunamadı"})

        def do_GET(self):
            self._islem("GET")

        def do_POST(self):
            self._islem("POST")

        def do_PUT(self):
            self._islem("PUT")

        def do_DELETE(self):
            self._islem("DELETE")

    return Isleyici


def main():
    ap = argparse.ArgumentParser(description="Müşteri Bulma Motoru")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--db", default=motor.VARSAYILAN_DB)
    ap.add_argument("--tarayici-acma", action="store_true")
    args = ap.parse_args()
    uygulama = Uygulama(args.db)
    sunucu = ThreadingHTTPServer(("127.0.0.1", args.port), isleyici_olustur(uygulama))
    adres = f"http://127.0.0.1:{args.port}"
    print(f"Müşteri Bulma Motoru çalışıyor: {adres}\nVeritabanı: {args.db}\nDurdurmak için Ctrl+C")
    if not args.tarayici_acma:
        threading.Timer(0.8, lambda: webbrowser.open(adres)).start()
    try:
        sunucu.serve_forever()
    except KeyboardInterrupt:
        print("\nKapatıldı.")


if __name__ == "__main__":
    main()
