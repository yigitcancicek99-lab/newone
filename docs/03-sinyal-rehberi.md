# Sinyal Rehberi — Müşteri Adayı Nerede, Nasıl Bulunur?

Bir şirket ancak bir **olay** yaşadığında üst düzey yönetici arar. Bu rehber, o olayları erken yakalamak için hangi kaynağa ne sıklıkla bakılacağını ve her sinyalin hangi Cornerstone hizmetine dönüştüğünü anlatır.

Her bulunan sinyal `data/hedef-hesaplar.csv` dosyasına bir satır olarak eklenir; `sinyal_turu` sütunu aşağıdaki kodlardan biri olmalıdır (araç puanlamayı buna göre yapar).

---

## Sinyal türleri ve ağırlıkları

| Kod (`sinyal_turu`) | Ne demek | Neden önemli | Puan ağırlığı |
|---|---|---|---|
| `ceo_ayrilik` | CEO/GM/CFO ayrıldı, yerine **vekaleten** atama yapıldı | Açık ve acil bir C-level arama | 30 |
| `ust_duzey_ilan` | Şirket direktör/GM/C-level ilanını **kendisi** açmış | İhtiyaç teyitli; 2–3 hafta açık kalmışsa pasif adaya ulaşamıyorlar | 25 |
| `satin_alma` | Birleşme / devralma tamamlandı | Yeni sahip yeni yönetim kurar + entegrasyon + fazla kadro | 22 |
| `halka_arz` | Halka arz oldu / SPK onayı aldı | Bağımsız YK üyesi, CFO, yatırımcı ilişkileri ihtiyacı | 20 |
| `yeni_yatirim` | Yeni fabrika, Türkiye'ye giriş, bölgesel merkez | Ülke müdürü, fabrika müdürü, ilk yönetim ekibi | 20 |
| `yeni_ceo` | Yeni CEO atandı | 6–12 ay içinde kendi ekibini kurar | 15 |
| `hizli_buyume` | Ciro/kapasite hedefini katlıyor, yeni iş kolu | Yeni direktör kadrosu, halef planlaması | 12 |
| `kuculme` | İşten çıkarma, tesis kapatma, yeniden yapılanma | Outplacement / kariyer geçiş hizmeti | 12 |
| `izleme` | Somut sinyal yok, sektör/hedef şirket | İlişki kurma, uzun vade | 5 |

---

## Kaynaklar ve tarama sıklığı

| Kaynak | Ne aranır | Sıklık | Sinyal |
|---|---|---|---|
| **KAP** (kap.org.tr) — "Özel Durum Açıklaması" | "Genel Müdür", "vekaleten", "görevinden ayrılmıştır", "atanmasına" | Her gün 10 dk | `ceo_ayrilik`, `yeni_ceo` |
| **LinkedIn İş İlanları** | Türkiye, son 30 gün, Direktör/Yönetici seviyesi (hazır linkler: `04-linkedin-aramalari.md`) | Haftada 2 | `ust_duzey_ilan` |
| **Rekabet Kurumu** — Kurul kararları (birleşme ve devralma) | Türkiye'deki hedef şirketler | Haftalık | `satin_alma` |
| **SPK haftalık bülteni** / halka arz takvimleri | Onaylanan halka arzlar | Haftalık | `halka_arz` |
| **Atama haberleri** (Capital "Şirket Panosu", Marketing Türkiye "Haftanın atamaları", Bloomberg HT) | Yeni CEO / GM atamaları | Haftalık | `yeni_ceo` |
| **Yatırım haberleri** (Sanayi Gazetesi, Ekonomi Gazetesi, Dünya, Yatırım Ofisi) | "fabrika", "yatırım", "Türkiye'ye geliyor", "bölgesel merkez" | Haftalık | `yeni_yatirim` |
| **OSB / serbest bölge duyuruları** (İZBAŞ, TOSB, Manisa OSB) | Yeni yer tahsisleri | Aylık | `yeni_yatirim` |
| **Fuar katılımcı listeleri** (SAHA savunma fuarı, ICCI enerji fuarı vb.) | Orta ölçekli büyüyen tedarikçiler | Fuar dönemlerinde | `hizli_buyume` / `izleme` |
| **İSO 500 / İSO İkinci 500** | Büyüyen sanayi şirketleri | Yılda 1 | `izleme` |
| **Cornerstone global ağı** | Türkiye'ye yatırım yapan yabancı müşteriler | Aylık | `yeni_yatirim` |

---

## Sinyal → Hizmet eşlemesi

| Sinyal | Birincil hizmet | Çapraz satış |
|---|---|---|
| `ceo_ayrilik` | Retained Executive Search (CEO/GM/CFO) | Onboarding koçluğu, sonra halef planlaması |
| `ust_duzey_ilan` | Retained / Director Recruitment | Market mapping (aynı rol başka lokasyonlarda da varsa) |
| `satin_alma` | Executive Search (yeni yönetim) | Merger Integration Support, Team Effectiveness, Career Transition |
| `halka_arz` | Board Search (bağımsız YK üyesi) + CFO/IR araması | Board Assessment (1. yıl sonunda) |
| `yeni_yatirim` | "İlk 5 yönetici" paketi (ülke/fabrika/finans/İK/satış) | Market mapping, interim yönetici (açılış dönemi) |
| `yeni_ceo` | Executive Search (yeni ekip) | Leadership Development, Team Effectiveness |
| `hizli_buyume` | Director Recruitment, CEO Succession Planning | Organizational Culture |
| `kuculme` | Career Transition (outplacement) | İleride toparlanma döneminde search |

---

## Eleme kuralları
- İlanı bir **işe alım / danışmanlık firması** açmışsa (Randstad, Adecco, ManpowerGroup, Michael Page, Hays, LHH vb.) → hesap listeye girmez; rakip listesine yazılır.
- Cornerstone'un **mevcut müşterileri ve off-limits şirketleri** → `durum=off-limits`.
- Müdür altı kademe (şef, vardiya amiri) → girmez.
