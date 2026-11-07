# Haftalık Çalışma Planı (Work Schedule)

Executive search satışında başarı, **tek büyük hamleden değil sabit ritimden** gelir. Satış döngüsü 12–18 ay sürebilir; bugün aradığın şirket aylar sonra müşteri olur. Bu yüzden takvim korunur, toplantı dışı bloklar iptal edilmez.

---

## KPI hunisi (önerilen başlangıç hedefleri)

```
 Haftalık
 ┌──────────────────────────────────────┐
 │  25  yeni sinyal / yeni hesap         │  ← sinyal taraması
 ├──────────────────────────────────┐   │
 │  60  temas (tel + e-posta + LI)   │   │  ← çok kanallı ilk temas + takipler
 ├──────────────────────────────┐   │   │
 │  15  karar vericiyle konuşma  │   │   │
 ├──────────────────────────┐   │   │   │
 │   3  keşif toplantısı     │   │   │   │
 ├──────────────────────┐   │   │   │   │
 │   1  teklif (2 haftada)│  ...
 └──────────────────────┘
 Aylık hedef: 1 mandate veya market mapping işi (3. aydan itibaren)
```

---

## Haftalık takvim

| Saat | Pazartesi | Salı | Çarşamba | Perşembe | Cuma |
|---|---|---|---|---|---|
| 08:30–09:30 | **Sinyal taraması** (KAP, atamalar, yatırım haberleri) → CSV'ye ekle | Sinyal taraması (LinkedIn direktör ilanları) | Sinyal taraması (halka arz, Rekabet Kurulu kararları) | Sinyal taraması | Sinyal taraması + haftalık özet |
| 09:30–10:00 | `python araclar/pipeline.py hafta` → haftalık liste | Günün listesi | Günün listesi | Günün listesi | — |
| 10:00–12:00 | **Arama bloğu 1** (en sıcak A hesaplar) | Arama bloğu | **Arama bloğu** | Arama bloğu | Takip e-postaları |
| 12:00–13:00 | Öğle | Öğle | Öğle | Öğle | Öğle |
| 13:00–14:30 | Kişiselleştirilmiş e-posta + LinkedIn mesajları | Toplantılar / danışmanla keşif görüşmeleri | Kişiselleştirilmiş e-posta + LinkedIn | Toplantılar | Teklif hazırlama |
| 14:30–16:30 | **Arama bloğu 2** | Teklif / pazar haritası hazırlığı | **Arama bloğu 2** | Arama bloğu 2 | **Haftalık değerlendirme** (pano, huni, öğrenilenler) |
| 16:30–17:30 | CRM güncelleme | CRM güncelleme | İçerik: Pazar Nabzı bülteni / LinkedIn paylaşımı | CRM güncelleme | Gelecek haftanın planı + Gülşah Hanım'a 5 satırlık rapor |

**Kurallar**
1. Arama blokları kutsaldır: bu saatlere iç toplantı konmaz.
2. Her temas aynı gün CSV/CRM'e işlenir (`durum`, `sonraki_adim`, `sonraki_adim_tarihi`).
3. Salı–Perşembe 10:00–12:00 karar vericilere ulaşmak için en verimli pencere; pazartesi sabahı ve cuma öğleden sonra ağır arama yapılmaz.
4. Her A hesabı için 4 haftada 8 temaslık takip ritmi uygulanır (aşağıda).

---

## 8 temaslık takip ritmi (bir hesap için 4 hafta)

| Gün | Kanal | İçerik |
|---|---|---|
| 1 | LinkedIn bağlantı isteği | Kısa, satışsız not (sinyale referans) |
| 1 | E-posta | Sinyale özel mesaj (bkz. `05-temas-sablonlari.md`) |
| 3 | Telefon | 30 saniyelik açılış, amaç: 20 dk toplantı |
| 7 | E-posta | Değer: kısa pazar içgörüsü / maaş bandı bilgisi |
| 10 | Telefon | İkinci deneme, farklı saat |
| 14 | LinkedIn mesajı | Pazar Nabzı bülteninden ilgili bir veri |
| 21 | E-posta | "Doğru kişi siz misiniz?" yönlendirme sorusu |
| 28 | E-posta | Kibar kapanış: "Şimdilik dosyayı kapatıyorum, ihtiyaç olursa…" → 3 ay sonra yeniden dene |

---

## Aylık ritim

| Hafta | Ekstra görev |
|---|---|
| 1. hafta | Pazar Nabzı bülteni gönderimi (İK direktörleri listesi) |
| 2. hafta | Global ağ çağrısı: diğer Cornerstone ofislerine "Türkiye'ye gelen müşteriniz var mı?" |
| 3. hafta | Kaybedilen/duran fırsatların gözden geçirilmesi |
| 4. hafta | Aylık rapor: huni, sinyal verimi, sonraki ay odak sektörü |
