# Müşteri Bulma Motoru

Her sektöre ve işe uyarlanabilen, **ürün veya hizmet satan** firmalar için **B2B ve B2C** müşteri bulma sistemi.
Hedef kitleyi tanımlarsınız; sistem işletme listesi çıkarır, iletişim bilgilerini (telefon, e-posta, web, sosyal medya)
toplar, her kaydı **satın alma sinyaline** göre puanlar ve müşterinize teslim edebileceğiniz öncelikli bir liste üretir.

Freelance müşteri bulma hizmeti için tasarlandı: **her müşteriniz = bir proje**.

## Kurulum ve çalıştırma

Yalnızca Python 3.8+ gerekir (ek paket yok). [python.org](https://www.python.org/downloads/) → kurarken *"Add Python to PATH"* işaretleyin.

| Sistem | Nasıl açılır |
|---|---|
| Windows | `baslat.bat` dosyasına çift tıklayın |
| macOS | `baslat.command` dosyasına çift tıklayın (ilk seferde: sağ tık → Aç) |
| Terminal | `python3 sunucu.py` |

Tarayıcıda `http://127.0.0.1:8765` açılır. Veriler `veri/motor.db` dosyasında, **yalnızca sizin bilgisayarınızda** tutulur
(yedeklemek için bu dosyayı kopyalayın).

## İş akışı

1. **Yeni proje** → şablon seçin:
   - Yönetici arama / İK danışmanlığı (Cornerstone modeli)
   - Yazılım / SaaS / dijital hizmet
   - Endüstriyel ürün / ekipman / hammadde
   - Yerel işletmelere satış (KOBİ: restoran, klinik, kuaför…)
   - Tüketiciye satış (B2C)
   - Boş proje
2. **Proje ayarları** → ideal müşteri profili: hedef sektörler, şehirler, unvanlar, firma büyüklüğü ve
   **satın alma sinyalleri** (ağırlık + yarı ömür). Her şey değiştirilebilir.
3. **Liste oluşturun:**
   - **Müşteri bul** → OpenStreetMap'ten şehir/ilçe + kategoriye göre işletmeler (40 hazır kategori veya özel etiket).
   - **İçe aktar** → Excel/CSV listesi (oda/OSB/dernek üye listeleri, fuar katılımcıları, kendi müşteri listeniz).
     Başlıklar otomatik eşlenir, Türkçe Excel kodlaması desteklenir.
   - **Kayıt ekle** → KAP, ticaret sicili, teşvik belgeleri, ilanlar gibi sinyal kaynaklarından elle.
4. **İletişim bilgisi toplayın** → *Liste → Sitelerden iletişim topla*: web sitesi olan kayıtların ana sayfası ve
   iletişim sayfası taranır; telefon, e-posta, LinkedIn, Instagram yalnızca **boş alanlara** yazılır.
5. **Mükerrer kontrolü** otomatiktir: aynı telefon, web alanı, e-posta veya ad+şehir varsa yeni kayıt açılmaz,
   mevcut kaydın eksikleri tamamlanır.
6. **Takip** → durum (yeni → temas → görüşme → teklif → kazanıldı), sonraki adım ve tarih. Pano bu haftanın
   A listesini ve vadesi gelen takipleri gösterir.
7. **Teslim** → *Müşteri raporu* (yazdırılabilir / PDF) veya *CSV indir* (Excel'de doğrudan açılır).

## Puanlama (0–100)

| Bileşen | En fazla | Mantık |
|---|---|---|
| Sinyal ağırlığı | 30 | Projede tanımlı sinyalin ağırlığı |
| Sinyal tazeliği | 20 | Yarı ömre göre azalır (ilan hızlı, yatırım yavaş soğur) |
| Sektör / segment uyumu | 20 | Hedef listede: 20, değil: 4, hedef tanımsız: 10 |
| Konum uyumu | 10 | Hedef şehir/ilçede: 10, değil: 2, tanımsız: 5 |
| Büyüklük + unvan uyumu | 10 | Her biri 5 |
| İletişim tamlığı | 10 | Telefon 5 · e-posta 3 · yetkili kişi 2 |

**A** ≥ 70 (bu hafta ara) · **B** ≥ 50 (2 hafta içinde) · **C** izle. Eşikler proje bazında değiştirilebilir.
"Uygun değil" ve "kaybedildi" kayıtlar 0 puan alır.

## Yasal çerçeve (önemli)

- **B2B:** Firmaların kamuya açık kurumsal iletişim bilgileri (web sitesi, harita kaydı) toplanır. Kayıtlar
  "Kurumsal" izinle işaretlenir. "İzin yok" işaretlenen firmalar (ör. reddedenler, mevcut müşteriler) iletişime
  uygun sayılmaz.
- **B2C:** Bireylere SMS / e-posta / arama ile ticari ileti için **İYS onayı** (6563 sayılı Kanun) ve **KVKK**
  uyumu gerekir. B2C projelerinde yalnızca **"Açık rıza var"** işaretli kişiler iletişime uygun sayılır.
  Sistem internetten kişi numarası toplamaz; B2C listeleri form, kampanya, etkinlik, tavsiye gibi izinli
  kaynaklardan CSV ile içe aktarılır. B2C'de sistemin asıl işi hedef kitleyi (segment, şehir, sinyal) belirleyip
  izinli kişileri önceliklendirmektir.
- OpenStreetMap verisi © OpenStreetMap katkıcıları, ODbL lisansı; rapora kaynak notu otomatik eklenir.
- Web sitesi taraması kayıt başına en fazla 3 sayfa açar; çok sayıda siteyi art arda taramak yerine ihtiyaç
  olan kayıtlar için kullanın.

## Dosyalar

| Dosya | İçerik |
|---|---|
| `sunucu.py` | Yerel web sunucusu ve API |
| `motor.py` | Veritabanı, puanlama, mükerrer kontrolü, CSV içe/dışa aktarma |
| `kaynaklar.py` | OpenStreetMap araması ve web sitesinden iletişim çıkarma |
| `sablonlar.py` | Proje şablonları, sinyaller, OSM kategorileri — yeni sektör şablonu buraya eklenir |
| `web/` | Arayüz (HTML/CSS/JS) |
| `testler.py` | Otomatik testler: `python3 -m unittest testler` |
