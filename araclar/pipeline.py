#!/usr/bin/env python3
"""
Cornerstone Türkiye — Sinyal odaklı müşteri bulma aracı.

Hedef hesapları (data/hedef-hesaplar.csv) sinyal türü, sinyalin tazeliği,
sektör uyumu ve pozisyon kademesine göre puanlar; haftalık arama listesi ve
yöneticiye gösterilebilecek bir HTML pano üretir.

Yalnızca Python standart kütüphanesi kullanır (Python 3.8+).

Kullanım:
    python araclar/pipeline.py liste                 # puanlı tüm hesaplar
    python araclar/pipeline.py hafta                 # bu haftanın arama listesi -> raporlar/
    python araclar/pipeline.py panel                 # HTML pano -> panel/index.html
    python araclar/pipeline.py ekle --sirket "X A.Ş." --sektor enerji \
        --sinyal yeni_yatirim --ozet "Yeni fabrika" --tarih 2026-11-07 \
        --kaynak https://... --kademe direktor --hizmet "İlk 5 yönetici paketi" \
        --unvan "Genel Müdür"
    python araclar/pipeline.py guncelle --id 12 --durum temas \
        --sonraki "Telefon" --sonraki-tarih 2026-11-12

Ortak seçenek: --bugun YYYY-MM-DD  (tarih hesaplarını sabitlemek için)
"""

import argparse
import csv
import html
import os
import sys
from collections import Counter
from datetime import date, datetime, timedelta

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_YOLU = os.path.join(KOK, "data", "hedef-hesaplar.csv")
RAPOR_KLASORU = os.path.join(KOK, "raporlar")
PANEL_YOLU = os.path.join(KOK, "panel", "index.html")

ALANLAR = [
    "id", "sirket", "sektor", "sinyal_turu", "sinyal_ozeti", "sinyal_tarihi",
    "kaynak", "pozisyon_kademesi", "onerilen_hizmet", "hedef_unvan",
    "hedef_kisi", "durum", "sonraki_adim", "sonraki_adim_tarihi", "notlar",
]

# --- Puanlama modeli -------------------------------------------------------
# sinyal_turu: (ağırlık, tazelik yarı ömrü gün)
# Yarı ömür: sinyalin değeri kaç günde yarıya iner. İlanlar hızlı soğur,
# yatırım ve halka arz gibi yapısal olaylar aylarca sıcak kalır.
SINYALLER = {
    "ceo_ayrilik":    (30, 120),
    "ust_duzey_ilan": (25, 21),
    "satin_alma":     (22, 120),
    "halka_arz":      (20, 150),
    "yeni_yatirim":   (20, 180),
    "yeni_ceo":       (15, 180),
    "hizli_buyume":   (12, 180),
    "kuculme":        (12, 90),
    "izleme":         (5, 365),
}
TAZELIK_MAKS = 25
TARIHSIZ_TAZELIK = 3

# Cornerstone Türkiye'nin odak sektörleri + stratejik büyüme sektörleri
ODAK_SEKTORLER = {"otomotiv", "endustriyel", "uretim", "enerji", "teknoloji", "savunma", "finans"}
SEKTOR_ODAK_PUANI = 20
SEKTOR_DIGER_PUANI = 8

KADEME_PUANI = {"c_level": 20, "direktor": 15, "mudur": 8}

ESIK_A = 75
ESIK_B = 60

AKTIF_DURUMLAR = {"yeni", "temas", "gorusme", "teklif"}
KAPALI_DURUMLAR = {"kazanildi", "kaybedildi", "off-limits"}
HUNI_SIRASI = ["yeni", "temas", "gorusme", "teklif", "kazanildi"]
HUNI_ETIKET = {"gorusme": "görüşme", "kazanildi": "kazanıldı"}

SABLON = {
    "ust_duzey_ilan": "Şablon 1 – Üst düzey ilan",
    "ceo_ayrilik": "Şablon 2 – Vekaleten CEO/GM",
    "yeni_yatirim": "Şablon 3 – Yeni yatırım",
    "halka_arz": "Şablon 4 – Halka arz",
    "satin_alma": "Şablon 2/3 uyarlaması – Satın alma",
    "yeni_ceo": "Şablon 2 uyarlaması – Yeni CEO",
    "hizli_buyume": "Şablon 3 uyarlaması – Büyüme",
    "kuculme": "Outplacement mesajı",
    "izleme": "LinkedIn bağlantı notu",
}

GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe"]


# --- Yardımcılar -------------------------------------------------------------
def tarih_oku(metin):
    metin = (metin or "").strip()
    if not metin:
        return None
    try:
        return datetime.strptime(metin, "%Y-%m-%d").date()
    except ValueError:
        return None


def csv_oku():
    with open(CSV_YOLU, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def csv_yaz(satirlar):
    with open(CSV_YOLU, "w", newline="", encoding="utf-8") as f:
        yazici = csv.DictWriter(f, fieldnames=ALANLAR)
        yazici.writeheader()
        for s in satirlar:
            yazici.writerow({k: s.get(k, "") for k in ALANLAR})


def puanla(satir, bugun):
    """Hesap için 0–95 arası puan ve A/B/C önceliği döndürür."""
    durum = (satir.get("durum") or "").strip()
    if durum == "off-limits":
        return 0.0, "-", {}
    agirlik, yari_omur = SINYALLER.get(satir.get("sinyal_turu", "").strip(), (5, 365))
    t = tarih_oku(satir.get("sinyal_tarihi"))
    if t is None:
        tazelik = TARIHSIZ_TAZELIK
    else:
        gun = max((bugun - t).days, 0)
        tazelik = TAZELIK_MAKS * (0.5 ** (gun / yari_omur))
    sektor = SEKTOR_ODAK_PUANI if satir.get("sektor", "").strip() in ODAK_SEKTORLER else SEKTOR_DIGER_PUANI
    kademe = KADEME_PUANI.get(satir.get("pozisyon_kademesi", "").strip(), 8)
    toplam = round(agirlik + tazelik + sektor + kademe, 1)
    oncelik = "A" if toplam >= ESIK_A else "B" if toplam >= ESIK_B else "C"
    detay = {"sinyal": agirlik, "tazelik": round(tazelik, 1), "sektor": sektor, "kademe": kademe}
    return toplam, oncelik, detay


def puanli_liste(bugun):
    satirlar = csv_oku()
    for s in satirlar:
        s["_puan"], s["_oncelik"], s["_detay"] = puanla(s, bugun)
    satirlar.sort(key=lambda s: s["_puan"], reverse=True)
    return satirlar


def hafta_baslangici(gun):
    return gun - timedelta(days=gun.weekday())


# --- Komutlar ----------------------------------------------------------------
def komut_liste(args):
    bugun = args.bugun
    satirlar = puanli_liste(bugun)
    print(f"{'#':>3} {'Öncelik':7} {'Puan':>5}  {'Şirket':32} {'Sinyal':15} {'Durum':10}")
    print("-" * 80)
    for s in satirlar:
        print(f"{s['id']:>3} {s['_oncelik']:7} {s['_puan']:>5}  {s['sirket'][:32]:32} "
              f"{s['sinyal_turu'][:15]:15} {s['durum'][:10]:10}")
    sayac = Counter(s["_oncelik"] for s in satirlar)
    print(f"\nToplam {len(satirlar)} hesap — A: {sayac['A']}  B: {sayac['B']}  C: {sayac['C']}")


def komut_hafta(args):
    bugun = args.bugun
    pzt = hafta_baslangici(bugun)
    cuma = pzt + timedelta(days=4)
    yil, hafta_no, _ = pzt.isocalendar()
    satirlar = puanli_liste(bugun)

    takipler = [
        s for s in satirlar
        if s["durum"] in AKTIF_DURUMLAR - {"yeni"}
        and tarih_oku(s["sonraki_adim_tarihi"]) is not None
        and tarih_oku(s["sonraki_adim_tarihi"]) <= cuma
    ]
    takipler.sort(key=lambda s: tarih_oku(s["sonraki_adim_tarihi"]))

    yeniler = [s for s in satirlar if s["durum"] == "yeni" and s["_oncelik"] in ("A", "B")]
    yeniler = yeniler[: args.adet]

    satir = []
    satir.append(f"# Haftalık Arama Listesi — {yil}, {hafta_no}. hafta")
    satir.append("")
    satir.append(f"Dönem: {pzt.strftime('%d.%m.%Y')} – {cuma.strftime('%d.%m.%Y')}  ·  "
                 f"Oluşturulma: {bugun.strftime('%d.%m.%Y')}")
    satir.append("")
    satir.append("Hedef: 60 temas · 15 karar vericiyle konuşma · 3 keşif toplantısı")
    satir.append("")

    satir.append(f"## 1. Vadesi gelen takipler ({len(takipler)})")
    satir.append("")
    if takipler:
        satir.append("| Tarih | Şirket | Durum | Sonraki adım | Kişi |")
        satir.append("|---|---|---|---|---|")
        for s in takipler:
            satir.append(f"| {s['sonraki_adim_tarihi']} | {s['sirket']} | {s['durum']} | "
                         f"{s['sonraki_adim']} | {s['hedef_kisi'] or s['hedef_unvan']} |")
    else:
        satir.append("_Bu hafta vadesi gelen takip yok._")
    satir.append("")

    satir.append(f"## 2. Yeni temas listesi — puana göre ({len(yeniler)} hesap)")
    satir.append("")
    for i, gun in enumerate(GUNLER):
        dilim = yeniler[i::len(GUNLER)]
        if not dilim:
            continue
        satir.append(f"### {gun}")
        satir.append("")
        satir.append("| Öncelik | Puan | Şirket | Sinyal | Önerilen hizmet | Kime | Şablon |")
        satir.append("|---|---|---|---|---|---|---|")
        for s in dilim:
            satir.append(
                f"| {s['_oncelik']} | {s['_puan']} | {s['sirket']} | {s['sinyal_ozeti']} | "
                f"{s['onerilen_hizmet']} | {s['hedef_kisi'] or s['hedef_unvan']} | "
                f"{SABLON.get(s['sinyal_turu'], '-')} |")
        satir.append("")

    satir.append("## 3. Cuma değerlendirmesi")
    satir.append("")
    satir.append("- [ ] Tüm temaslar CSV'ye işlendi (`durum`, `sonraki_adim`, `sonraki_adim_tarihi`)")
    satir.append("- [ ] Bu hafta en çok yanıt getiren sinyal türü: ______")
    satir.append("- [ ] Gelecek haftanın odak sektörü: ______")
    satir.append("- [ ] `python araclar/pipeline.py panel` ile pano güncellendi")
    satir.append("")

    os.makedirs(RAPOR_KLASORU, exist_ok=True)
    yol = os.path.join(RAPOR_KLASORU, f"haftalik-liste-{yil}-H{hafta_no:02d}.md")
    with open(yol, "w", encoding="utf-8") as f:
        f.write("\n".join(satir))
    print(f"Haftalık liste yazıldı: {os.path.relpath(yol, KOK)}  "
          f"({len(takipler)} takip, {len(yeniler)} yeni hesap)")


def komut_ekle(args):
    satirlar = csv_oku()
    if args.sinyal not in SINYALLER:
        sys.exit(f"Geçersiz sinyal türü: {args.sinyal}. Seçenekler: {', '.join(SINYALLER)}")
    if args.kademe not in KADEME_PUANI:
        sys.exit(f"Geçersiz kademe: {args.kademe}. Seçenekler: {', '.join(KADEME_PUANI)}")
    if args.tarih and tarih_oku(args.tarih) is None:
        sys.exit("Tarih biçimi YYYY-MM-DD olmalı.")
    mevcut = {s["sirket"].strip().lower() for s in satirlar}
    if args.sirket.strip().lower() in mevcut:
        print(f"Uyarı: '{args.sirket}' zaten listede; yeni sinyal olarak yine de eklendi.")
    yeni_id = max((int(s["id"]) for s in satirlar if s["id"].isdigit()), default=0) + 1
    satirlar.append({
        "id": str(yeni_id), "sirket": args.sirket, "sektor": args.sektor,
        "sinyal_turu": args.sinyal, "sinyal_ozeti": args.ozet, "sinyal_tarihi": args.tarih or "",
        "kaynak": args.kaynak or "", "pozisyon_kademesi": args.kademe,
        "onerilen_hizmet": args.hizmet or "", "hedef_unvan": args.unvan or "",
        "hedef_kisi": "", "durum": "yeni", "sonraki_adim": "", "sonraki_adim_tarihi": "", "notlar": "",
    })
    csv_yaz(satirlar)
    puan, oncelik, _ = puanla(satirlar[-1], args.bugun)
    print(f"Eklendi: #{yeni_id} {args.sirket} — puan {puan} ({oncelik})")


def komut_guncelle(args):
    satirlar = csv_oku()
    for s in satirlar:
        if s["id"] == str(args.id):
            if args.durum:
                s["durum"] = args.durum
            if args.sonraki is not None:
                s["sonraki_adim"] = args.sonraki
            if args.sonraki_tarih is not None:
                s["sonraki_adim_tarihi"] = args.sonraki_tarih
            if args.kisi is not None:
                s["hedef_kisi"] = args.kisi
            if args.not_ is not None:
                s["notlar"] = (s["notlar"] + " | " if s["notlar"] else "") + args.not_
            csv_yaz(satirlar)
            print(f"Güncellendi: #{s['id']} {s['sirket']} → durum={s['durum']}")
            return
    sys.exit(f"#{args.id} bulunamadı.")


def komut_panel(args):
    bugun = args.bugun
    satirlar = puanli_liste(bugun)
    aktif = [s for s in satirlar if s["durum"] not in KAPALI_DURUMLAR]
    oncelik = Counter(s["_oncelik"] for s in aktif)
    sinyal = Counter(s["sinyal_turu"] for s in aktif)
    sektor = Counter(s["sektor"] for s in aktif)
    durum = Counter(s["durum"] for s in satirlar)
    e = html.escape

    def cubuklar(sayac, renk):
        if not sayac:
            return "<p class='bos'>Veri yok</p>"
        maks = max(sayac.values())
        parcalar = []
        for ad, n in sayac.most_common():
            yuzde = 100 * n / maks
            parcalar.append(
                f"<div class='cubuk-satir'><span class='etiket'>{e(ad)}</span>"
                f"<span class='cubuk'><span style='width:{yuzde:.0f}%;background:{renk}'></span></span>"
                f"<span class='deger'>{n}</span></div>")
        return "".join(parcalar)

    huni = []
    for d in HUNI_SIRASI:
        n = durum.get(d, 0)
        huni.append(f"<div class='huni-adim'><div class='huni-sayi'>{n}</div>"
                    f"<div class='huni-ad'>{e(HUNI_ETIKET.get(d, d))}</div></div>")

    tablo = []
    for s in [s for s in aktif if s["_oncelik"] in ("A", "B")][:20]:
        kaynak = s["kaynak"]
        kaynak_html = (f"<a href='{e(kaynak)}' target='_blank' rel='noopener'>kaynak</a>"
                       if kaynak.startswith("http") else e(kaynak))
        tablo.append(
            f"<tr><td><span class='rozet {s['_oncelik']}'>{s['_oncelik']}</span></td>"
            f"<td class='sayi'>{s['_puan']}</td><td><strong>{e(s['sirket'])}</strong><br>"
            f"<span class='ince'>{e(s['sektor'])}</span></td>"
            f"<td>{e(s['sinyal_ozeti'])}<br><span class='ince'>{e(s['sinyal_turu'])} · "
            f"{e(s['sinyal_tarihi'] or 'tarih yok')} · {kaynak_html}</span></td>"
            f"<td>{e(s['onerilen_hizmet'])}</td><td>{e(s['hedef_kisi'] or s['hedef_unvan'])}</td>"
            f"<td>{e(s['durum'])}</td></tr>")

    sayfa = f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cornerstone Türkiye — İş Geliştirme Panosu</title>
<style>
  :root {{ --lacivert:#14213d; --gri:#5c6370; --acik:#f4f5f7; --vurgu:#c8963e; --cizgi:#e3e5e8; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif; color:#1d2330; background:#fff; }}
  header {{ background:var(--lacivert); color:#fff; padding:28px 40px; }}
  header h1 {{ margin:0; font-size:26px; letter-spacing:.2px; }}
  header p {{ margin:6px 0 0; color:#c9cede; font-size:14px; }}
  main {{ padding:28px 40px 48px; max-width:1280px; margin:0 auto; }}
  .kartlar {{ display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin-bottom:28px; }}
  .kart {{ background:var(--acik); border-radius:10px; padding:18px 20px; }}
  .kart .ust {{ font-size:13px; color:var(--gri); }}
  .kart .alt {{ font-size:32px; font-weight:700; margin-top:4px; color:var(--lacivert); }}
  .izgara {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:24px; margin-bottom:32px; }}
  h2 {{ font-size:16px; color:var(--lacivert); margin:0 0 12px; }}
  .kutu {{ border:1px solid var(--cizgi); border-radius:10px; padding:18px 20px; }}
  .cubuk-satir {{ display:flex; align-items:center; gap:10px; margin:7px 0; font-size:13px; }}
  .etiket {{ width:110px; color:var(--gri); }}
  .cubuk {{ flex:1; background:var(--acik); height:12px; border-radius:6px; overflow:hidden; }}
  .cubuk span {{ display:block; height:100%; border-radius:6px; }}
  .deger {{ width:24px; text-align:right; font-variant-numeric:tabular-nums; }}
  .huni {{ display:flex; gap:8px; }}
  .huni-adim {{ flex:1; background:var(--acik); border-radius:8px; padding:12px 6px; text-align:center; }}
  .huni-sayi {{ font-size:24px; font-weight:700; color:var(--lacivert); }}
  .huni-ad {{ font-size:12px; color:var(--gri); margin-top:2px; }}
  table {{ width:100%; border-collapse:collapse; font-size:13.5px; }}
  th {{ text-align:left; background:var(--acik); padding:10px; font-weight:600; color:var(--lacivert); }}
  td {{ padding:10px; border-bottom:1px solid var(--cizgi); vertical-align:top; }}
  td.sayi {{ text-align:right; font-variant-numeric:tabular-nums; }}
  .ince {{ color:var(--gri); font-size:12px; }}
  .rozet {{ display:inline-block; width:26px; height:26px; line-height:26px; text-align:center; border-radius:6px; font-weight:700; color:#fff; }}
  .rozet.A {{ background:var(--vurgu); }} .rozet.B {{ background:#7d8aa3; }} .rozet.C {{ background:#b9bfca; }}
  a {{ color:var(--lacivert); }}
  footer {{ margin-top:28px; font-size:12px; color:var(--gri); }}
  .bos {{ color:var(--gri); font-size:13px; }}
  @media (max-width:900px) {{ .kartlar, .izgara {{ grid-template-columns:1fr 1fr; }} main, header {{ padding:20px; }} }}
</style>
</head>
<body>
<header>
  <h1>Cornerstone Türkiye — İş Geliştirme Panosu</h1>
  <p>Sinyal odaklı hedef hesap takibi · Güncelleme: {bugun.strftime('%d.%m.%Y')}</p>
</header>
<main>
  <section class="kartlar">
    <div class="kart"><div class="ust">Aktif hedef hesap</div><div class="alt">{len(aktif)}</div></div>
    <div class="kart"><div class="ust">A öncelik (hemen aranacak)</div><div class="alt">{oncelik.get('A', 0)}</div></div>
    <div class="kart"><div class="ust">B öncelik</div><div class="alt">{oncelik.get('B', 0)}</div></div>
    <div class="kart"><div class="ust">C öncelik (izleme)</div><div class="alt">{oncelik.get('C', 0)}</div></div>
  </section>
  <section class="izgara">
    <div class="kutu"><h2>Sinyal türüne göre</h2>{cubuklar(sinyal, '#14213d')}</div>
    <div class="kutu"><h2>Sektöre göre</h2>{cubuklar(sektor, '#c8963e')}</div>
    <div class="kutu"><h2>Satış hunisi</h2><div class="huni">{''.join(huni)}</div>
      <p class="ince" style="margin-top:14px">yeni → temas → görüşme → teklif → kazanıldı</p></div>
  </section>
  <section>
    <h2>En öncelikli 20 hesap</h2>
    <table>
      <thead><tr><th>Öncelik</th><th style="text-align:right">Puan</th><th>Şirket</th><th>Sinyal</th>
      <th>Önerilen hizmet</th><th>Kime</th><th>Durum</th></tr></thead>
      <tbody>{''.join(tablo)}</tbody>
    </table>
  </section>
  <footer>Puan = sinyal ağırlığı + sinyal tazeliği + sektör uyumu + pozisyon kademesi (en fazla 95).
  A ≥ {ESIK_A}, B ≥ {ESIK_B}. Kaynak: data/hedef-hesaplar.csv</footer>
</main>
</body>
</html>
"""
    os.makedirs(os.path.dirname(PANEL_YOLU), exist_ok=True)
    with open(PANEL_YOLU, "w", encoding="utf-8") as f:
        f.write(sayfa)
    print(f"Pano yazıldı: {os.path.relpath(PANEL_YOLU, KOK)}")


def main():
    p = argparse.ArgumentParser(description="Cornerstone Türkiye sinyal odaklı müşteri bulma aracı")
    p.add_argument("--bugun", type=lambda x: datetime.strptime(x, "%Y-%m-%d").date(),
                   default=date.today(), help="Hesaplamalar için tarih (YYYY-MM-DD)")
    alt = p.add_subparsers(dest="komut", required=True)

    alt.add_parser("liste", help="Puanlı hesap listesi")

    h = alt.add_parser("hafta", help="Haftalık arama listesi üret")
    h.add_argument("--adet", type=int, default=20, help="Yeni temas sayısı (varsayılan 20)")

    alt.add_parser("panel", help="HTML pano üret")

    e = alt.add_parser("ekle", help="Yeni hesap / sinyal ekle")
    e.add_argument("--sirket", required=True)
    e.add_argument("--sektor", required=True)
    e.add_argument("--sinyal", required=True, help=", ".join(SINYALLER))
    e.add_argument("--ozet", required=True)
    e.add_argument("--tarih")
    e.add_argument("--kaynak")
    e.add_argument("--kademe", default="direktor", help=", ".join(KADEME_PUANI))
    e.add_argument("--hizmet")
    e.add_argument("--unvan")

    g = alt.add_parser("guncelle", help="Hesap durumunu güncelle")
    g.add_argument("--id", required=True)
    g.add_argument("--durum", choices=sorted(AKTIF_DURUMLAR | KAPALI_DURUMLAR | {"beklemede"}))
    g.add_argument("--sonraki")
    g.add_argument("--sonraki-tarih", dest="sonraki_tarih")
    g.add_argument("--kisi")
    g.add_argument("--not", dest="not_")

    args = p.parse_args()
    # Alt komuttan sonra verilen --bugun'u da kabul etmek için
    komutlar = {"liste": komut_liste, "hafta": komut_hafta, "panel": komut_panel,
                "ekle": komut_ekle, "guncelle": komut_guncelle}
    komutlar[args.komut](args)


if __name__ == "__main__":
    main()
