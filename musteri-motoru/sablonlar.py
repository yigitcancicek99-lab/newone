"""
Proje şablonları ve OpenStreetMap kategori listesi.

Her şablon, yeni bir müşteri projesi açarken doldurulan varsayılan ayarlardır:
hangi satın alma sinyallerinin izleneceği, sinyallerin ağırlığı ve ne kadar
hızlı soğudukları (yarı ömür, gün), önerilen hedef sektörler/unvanlar.
Hepsi proje açıldıktan sonra arayüzden değiştirilebilir.
"""

# Sinyal: {"kod": ..., "ad": ..., "agirlik": 0-30, "yari_omur": gün}
def _s(kod, ad, agirlik, yari_omur):
    return {"kod": kod, "ad": ad, "agirlik": agirlik, "yari_omur": yari_omur}


SABLONLAR = {
    "yonetici_arama": {
        "ad": "Yönetici arama / İK danışmanlığı",
        "aciklama": "Executive search, işe alım, outplacement gibi B2B hizmetler (Cornerstone modeli).",
        "satis_tipi": "b2b",
        "teklif_turu": "hizmet",
        "hedef_sektorler": ["otomotiv", "endüstriyel", "üretim", "enerji", "teknoloji", "savunma", "finans"],
        "hedef_unvanlar": ["Genel Müdür", "CEO", "İK Direktörü", "Yönetim Kurulu Başkanı"],
        "hedef_buyuklukler": ["orta", "buyuk"],
        "sinyaller": [
            _s("ceo_ayrilik", "CEO/GM ayrıldı, vekaleten yönetiliyor", 30, 120),
            _s("ust_duzey_ilan", "Üst düzey pozisyon ilanı açık", 25, 21),
            _s("satin_alma", "Satın alma / birleşme", 22, 120),
            _s("halka_arz", "Halka arz", 20, 150),
            _s("yeni_yatirim", "Yeni yatırım / fabrika", 20, 180),
            _s("yeni_ceo", "Yeni CEO atandı", 15, 180),
            _s("hizli_buyume", "Hızlı büyüme", 12, 180),
            _s("kuculme", "Küçülme / yeniden yapılanma", 12, 90),
        ],
    },
    "yazilim_saas": {
        "ad": "Yazılım / SaaS / dijital hizmet",
        "aciklama": "Şirketlere yazılım, web sitesi, dijital pazarlama, IT hizmeti satanlar.",
        "satis_tipi": "b2b",
        "teklif_turu": "hizmet",
        "hedef_sektorler": ["perakende", "üretim", "lojistik", "sağlık", "eğitim", "e-ticaret"],
        "hedef_unvanlar": ["Genel Müdür", "BT Müdürü", "Pazarlama Müdürü", "Operasyon Müdürü"],
        "hedef_buyuklukler": ["kucuk", "orta"],
        "sinyaller": [
            _s("yatirim_aldi", "Yatırım / hibe aldı", 28, 120),
            _s("bt_ilani", "BT / dijital pozisyon ilanı açtı", 25, 30),
            _s("yeni_sube", "Yeni şube / bölge açtı", 20, 120),
            _s("web_zayif", "Web sitesi yok veya eski", 18, 365),
            _s("yeni_yonetici", "Yeni BT/pazarlama yöneticisi geldi", 18, 120),
            _s("rakip_kullanici", "Rakip ürünü kullanıyor / şikayetçi", 15, 180),
            _s("fuar", "Fuar katılımcısı", 10, 60),
        ],
    },
    "endustriyel_urun": {
        "ad": "Endüstriyel ürün / ekipman / hammadde",
        "aciklama": "Fabrikalara makine, yedek parça, ambalaj, kimyasal, enerji çözümü satanlar.",
        "satis_tipi": "b2b",
        "teklif_turu": "urun",
        "hedef_sektorler": ["üretim", "gıda", "tekstil", "otomotiv", "kimya", "plastik", "metal"],
        "hedef_unvanlar": ["Satın Alma Müdürü", "Fabrika Müdürü", "Bakım Müdürü", "Üretim Müdürü"],
        "hedef_buyuklukler": ["kucuk", "orta", "buyuk"],
        "sinyaller": [
            _s("yeni_fabrika", "Yeni fabrika / kapasite artışı", 30, 240),
            _s("tesvik_belgesi", "Yatırım teşvik belgesi aldı", 26, 240),
            _s("ihale", "İhale / satın alma talebi yayınladı", 25, 30),
            _s("ihracat_artisi", "İhracat artışı / yeni pazar", 18, 180),
            _s("satin_alma_ilani", "Satın alma / bakım ilanı açtı", 18, 45),
            _s("fuar", "Fuar katılımcısı", 12, 60),
            _s("tedarikci_sorunu", "Mevcut tedarikçiyle sorun", 20, 90),
        ],
    },
    "yerel_isletme": {
        "ad": "Yerel işletmelere satış (KOBİ)",
        "aciklama": "Restoran, klinik, kuaför, mağaza gibi yerel işletmelere ürün/hizmet satanlar.",
        "satis_tipi": "b2b",
        "teklif_turu": "hizmet",
        "hedef_sektorler": ["restoran", "kafe", "klinik", "güzellik", "spor salonu", "otel"],
        "hedef_unvanlar": ["İşletme Sahibi", "Müdür"],
        "hedef_buyuklukler": ["mikro", "kucuk"],
        "sinyaller": [
            _s("yeni_acilis", "Yeni açıldı", 28, 90),
            _s("web_yok", "Web sitesi yok", 20, 365),
            _s("dusuk_puan", "Düşük Google puanı / kötü yorumlar", 18, 120),
            _s("sosyal_zayif", "Sosyal medyası zayıf", 12, 365),
            _s("tadilat", "Tadilat / büyüme", 15, 90),
            _s("eleman_ilani", "Eleman ilanı verdi", 12, 30),
        ],
    },
    "b2c_tuketici": {
        "ad": "Tüketiciye satış (B2C)",
        "aciklama": "Bireysel müşterilere ürün/hizmet. Yalnızca izinli (açık rızalı) kişilerle çalışır.",
        "satis_tipi": "b2c",
        "teklif_turu": "urun",
        "hedef_sektorler": [],
        "hedef_unvanlar": [],
        "hedef_buyuklukler": [],
        "sinyaller": [
            _s("form_doldurdu", "Form / teklif talebi doldurdu", 30, 14),
            _s("sepet_terk", "Sepeti terk etti / fiyat sordu", 26, 7),
            _s("etkinlik", "Etkinlik / fuar ziyaretçisi", 18, 30),
            _s("tavsiye", "Tavsiye ile geldi", 24, 60),
            _s("eski_musteri", "Eski müşteri (yenileme zamanı)", 20, 180),
            _s("bulten_uyesi", "Bülten / kampanya üyesi", 10, 180),
        ],
    },
    "bos": {
        "ad": "Boş proje (kendim ayarlayacağım)",
        "aciklama": "Sinyalleri ve hedefleri sıfırdan tanımlayın.",
        "satis_tipi": "b2b",
        "teklif_turu": "hizmet",
        "hedef_sektorler": [],
        "hedef_unvanlar": [],
        "hedef_buyuklukler": [],
        "sinyaller": [
            _s("ilgi", "İlgi gösterdi / talep var", 25, 60),
            _s("yeni_olay", "Yeni olay (açılış, yatırım, değişim)", 20, 120),
        ],
    },
}

BUYUKLUKLER = {
    "mikro": "Mikro (1–9)",
    "kucuk": "Küçük (10–49)",
    "orta": "Orta (50–249)",
    "buyuk": "Büyük (250+)",
}

DURUMLAR = {
    "yeni": "Yeni",
    "temas": "Temas kuruldu",
    "gorusme": "Görüşme",
    "teklif": "Teklif",
    "kazanildi": "Kazanıldı",
    "kaybedildi": "Kaybedildi",
    "uygun_degil": "Uygun değil",
}

IZINLER = {
    "kurumsal": "Kurumsal (firmanın kamuya açık iletişim bilgisi)",
    "acik_riza": "Açık rıza var (İYS/form onayı)",
    "yok": "İzin yok – ticari ileti gönderilemez",
    "bilinmiyor": "Bilinmiyor",
}

# OpenStreetMap'ten işletme aramak için kategori -> etiket(ler)
OSM_KATEGORILER = {
    "Restoran": [("amenity", "restaurant")],
    "Kafe": [("amenity", "cafe")],
    "Fast food": [("amenity", "fast_food")],
    "Bar / pub": [("amenity", "bar"), ("amenity", "pub")],
    "Otel / pansiyon": [("tourism", "hotel"), ("tourism", "guest_house")],
    "Eczane": [("amenity", "pharmacy")],
    "Diş kliniği": [("amenity", "dentist"), ("healthcare", "dentist")],
    "Klinik / poliklinik": [("amenity", "clinic"), ("healthcare", "clinic")],
    "Doktor muayenehanesi": [("amenity", "doctors")],
    "Hastane": [("amenity", "hospital")],
    "Veteriner": [("amenity", "veterinary")],
    "Kuaför / berber": [("shop", "hairdresser")],
    "Güzellik merkezi": [("shop", "beauty")],
    "Spor salonu": [("leisure", "fitness_centre")],
    "Anaokulu": [("amenity", "kindergarten")],
    "Okul": [("amenity", "school")],
    "Dil / eğitim kursu": [("amenity", "language_school"), ("amenity", "training"), ("amenity", "driving_school")],
    "Market / süpermarket": [("shop", "supermarket"), ("shop", "convenience")],
    "Giyim mağazası": [("shop", "clothes")],
    "Mobilya mağazası": [("shop", "furniture")],
    "Hırdavat / yapı market": [("shop", "hardware"), ("shop", "doityourself")],
    "Elektronik mağazası": [("shop", "electronics"), ("shop", "mobile_phone")],
    "Optik": [("shop", "optician")],
    "Kırtasiye / kitapçı": [("shop", "stationery"), ("shop", "books")],
    "Oto servis": [("shop", "car_repair")],
    "Oto galeri": [("shop", "car")],
    "Oto yedek parça": [("shop", "car_parts")],
    "Akaryakıt istasyonu": [("amenity", "fuel")],
    "Emlak ofisi": [("office", "estate_agent")],
    "Avukat / hukuk bürosu": [("office", "lawyer")],
    "Muhasebe / mali müşavir": [("office", "accountant"), ("office", "tax_advisor")],
    "Sigorta acentesi": [("office", "insurance")],
    "Mimarlık ofisi": [("office", "architect")],
    "Yazılım / BT firması": [("office", "it")],
    "Reklam / ajans": [("office", "advertising_agency")],
    "Lojistik / nakliye": [("office", "logistics"), ("office", "moving_company")],
    "İnşaat firması": [("office", "construction_company"), ("craft", "builder")],
    "Şirket ofisi (genel)": [("office", "company")],
    "Fabrika / üretim tesisi": [("man_made", "works"), ("industrial", "factory")],
    "Toptancı": [("shop", "wholesale")],
}


# --- Müşteri (freelance işveren) mülakatı ------------------------------------------
# Her soru: (kod, soru, neden önemli). Cevaplar projede saklanır ve yapay zekâ
# analizine girdi olur: hedef kitle, sinyaller ve haber tarama sorguları buradan çıkar.
MULAKAT_BOLUMLERI = [
    ("Firma ve teklif", [
        ("firma_tanim", "Firmanızı ve ne yaptığınızı 2–3 cümleyle anlatır mısınız?",
         "Kim adına konuşacağımızı ve konumlamayı netleştirir."),
        ("urun_hizmet", "Satmak istediğiniz ürün/hizmet tam olarak nedir? Paketler, çeşitler, kapsam?",
         "Hangi müşteri tipine hangi paketin gideceğini belirler."),
        ("cozulen_sorun", "Müşterinin hangi sorununu çözüyorsunuz? Siz olmasanız müşteri ne yapardı?",
         "Sorunun dışarıdan görülebilen izleri sinyal olur."),
        ("fark", "Rakiplerden farkınız ne? Müşteriler sizi neden seçiyor?",
         "İlk temas mesajının ana cümlesi buradan çıkar."),
        ("fiyat", "Ortalama satış tutarı / fiyat aralığı nedir? Tek seferlik mi, abonelik mi?",
         "Hangi büyüklükteki firmanın bütçesi yeteceğini gösterir."),
        ("satis_suresi", "İlk temastan satışa ortalama ne kadar sürüyor?",
         "Sinyallerin ne kadar süre 'sıcak' kalacağını (yarı ömür) ayarlar."),
    ]),
    ("Mevcut müşteriler", [
        ("en_iyi_musteriler", "En iyi 5–10 müşteriniz kim? Ortak noktaları ne (sektör, büyüklük, durum)?",
         "En güvenilir ideal müşteri profili, mevcut iyi müşterilerin benzerleridir."),
        ("musteri_sektor", "Müşterileriniz hangi sektörlerden? En çok hangisinde başarılısınız?",
         "Hedef sektörler ve OSM/haber aramaları."),
        ("musteri_buyukluk", "Müşterilerinizin büyüklüğü nedir (çalışan sayısı, ciro, şube sayısı)?",
         "Hedef firma büyüklüğü."),
        ("musteri_konum", "Hangi şehir/bölgelerde hizmet veriyorsunuz? Uzak bölgelere satış yapabiliyor musunuz?",
         "Hedef şehirler ve arama bölgesi."),
        ("kayip_musteri", "Kaybettiğiniz veya size uygun olmayan müşteriler kimler? Kimlerle çalışmak istemezsiniz?",
         "Negatif filtre: zaman kaybettiren profilleri eler."),
        ("off_limits", "Kesinlikle aranmaması gereken firmalar var mı (mevcut müşteriler, ortaklar, rakipler)?",
         "Bu firmalar 'uygun değil / izin yok' olarak işaretlenir."),
    ]),
    ("Karar verici ve satın alma süreci", [
        ("karar_verici", "Satın alma kararını kim veriyor (unvan)? Kim etkiliyor, kim onaylıyor?",
         "Hedef unvanlar ve ulaşılacak kişi."),
        ("kullanici", "Ürünü/hizmeti günlük olarak kim kullanıyor?",
         "İkinci temas kişisi ve iç savunucu (champion)."),
        ("satin_alma_sureci", "Satın alma nasıl işliyor? Teklif, ihale, deneme, pilot, sözleşme?",
         "Takip adımları ve beklenen süre."),
        ("butce_donemi", "Bütçe dönemleri veya mevsimsellik var mı? Hangi aylarda karar veriliyor?",
         "Doğru zamanda temas için takvim."),
    ]),
    ("Tetikleyici olaylar (sinyaller)", [
        ("tetikleyici_olay", "Müşteriler genellikle hangi olaydan sonra size geliyor? (yeni yatırım, yönetici değişikliği, büyüme, sorun, mevzuat…)",
         "Sistemin haberlerde ve ilanlarda arayacağı ana sinyaller."),
        ("erken_belirti", "Müşteri ihtiyacını fark etmeden ÖNCE dışarıdan görülebilen belirtiler neler? (ilan, haber, web sitesi, yorumlar, ihale)",
         "Müşteri ihtiyacını bilmeden ona ulaşmamızı sağlayan bilgi."),
        ("mevzuat", "İhtiyacı doğuran veya zorunlu kılan mevzuat, standart, denetim, teşvik, son tarih var mı?",
         "Mevzuat değişiklikleri toplu ve zamanlı sinyal üretir."),
        ("aciliyet", "Hangi durumda ihtiyaç acil hale gelir?",
         "Yüksek ağırlıklı sinyaller."),
        ("ihtiyac_yok", "Hangi durumdaki bir firmanın size ihtiyacı olmaz?",
         "Yanlış pozitifleri azaltır."),
    ]),
    ("Pazar ve rakipler", [
        ("rakipler", "Başlıca rakipleriniz kimler? Rakip kullanan firmalara satış yapabiliyor musunuz?",
         "Rakip müşterileri ve rakip haberleri de sinyal olabilir."),
        ("ikame", "Müşteriler sizin yerine şu an ne kullanıyor (Excel, kendi ekibi, başka tedarikçi…)?",
         "Mesajda karşılaştırılacak 'mevcut durum'."),
        ("trendler", "Sektörünüzde talebi artıran güncel gelişmeler neler?",
         "Haber tarama sorgularına eklenir."),
    ]),
    ("Ulaşma", [
        ("kanal", "Hangi kanal işe yarıyor: telefon, e-posta, LinkedIn, WhatsApp, ziyaret, fuar?",
         "Hangi iletişim bilgisinin toplanacağını belirler."),
        ("mesaj", "Müşteriyi ikna eden cümle veya başarı hikâyesi nedir? Referans gösterilebilecek müşteri var mı?",
         "İlk temas mesajı ve referans."),
        ("kapi_acici", "Kapı açıcı bir teklifiniz var mı (ücretsiz analiz, deneme, demo, numune)?",
         "Düşük riskli ilk adım dönüşümü artırır."),
        ("temas_kimin_adina", "Temas kimin adına yapılacak? Toplantıları kim yapacak? Haftada kaç toplantı kaldırırsınız?",
         "Liste hacmi ve haftalık ritim."),
        ("izinli_veri", "Elinizde izinli müşteri/aday verisi var mı (CRM, form, İYS onaylı liste, fuar kartları)?",
         "B2C ve yeniden kazanım için yasal başlangıç listesi."),
    ]),
    ("Hedef ve çalışma modeli", [
        ("hedef", "Önümüzdeki 3 ayda kaç toplantı / yeni müşteri hedefliyorsunuz?",
         "Liste büyüklüğü ve önceliklendirme eşikleri."),
        ("odeme_modeli", "Çalışma ve ödeme modeli: sabit ücret, toplantı başı, satış primi?",
         "Raporlama ve başarı ölçütü."),
        ("materyal", "Sunum, broşür, fiyat listesi, referans listesi gibi materyaller var mı?",
         "Takip e-postalarına eklenecek içerik."),
    ]),
]

# YZ kullanılmadığında haber taramasında kullanılacak genel sinyal kelimeleri
GENEL_SINYAL_KELIMELERI = [
    "yatırım", "fabrika", "tesis", "kapasite", "yeni şube", "açılış", "atandı", "genel müdür",
    "satın aldı", "birleşme", "halka arz", "ihale", "teşvik", "ihracat", "büyüme", "işe alım",
]
