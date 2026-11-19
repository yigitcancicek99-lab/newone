# Tam sürümü internete kurma (Render.com)

Bu adımlarla Müşteri Bulma Motoru'nun **tüm özellikleri** (sinyal radarı, web sitesinden iletişim toplama,
harita araması, yapay zekâ) tek bir linkte, 7/24 çalışır. Sinyal radarı siz bilgisayarınızı kapatsanız da taramaya
devam eder. Süre: ~15 dakika. Maliyet: Render Starter planı ~7 $/ay + 1 GB disk ~0,25 $/ay + Claude API kullanımı.

## 1. Kodu ana dala alın

GitHub'da `yigitcancicek99-lab/newone` deposunda `ccr-917ee464-dzx9eq` dalını `main` dalına birleştirin
(Pull request → Merge). Render varsayılan olarak `main` dalını kullanır.

## 2. Render hesabı

1. <https://render.com> → **Get Started** → **GitHub ile giriş yapın**.
2. Render'ın `newone` deposuna erişmesine izin verin.

## 3. Blueprint ile kurulum

1. Render panelinde **New + → Blueprint**.
2. `newone` deposunu seçin. Render, depodaki `render.yaml` dosyasını okuyup `musteri-motoru` servisini önerir.
3. İstenen iki değeri girin:
   - **MOTOR_SIFRE**: uygulamaya giriş şifreniz (en az 8 karakter, başkasıyla paylaşmayın).
   - **ANTHROPIC_API_KEY**: Claude API anahtarınız (console.anthropic.com → API Keys). İsterseniz boş bırakıp
     sonra uygulamadaki *Yapay zekâ ayarları*ndan da girebilirsiniz.
4. **Apply** → kurulum 2–4 dakika sürer.

## 4. Kullanım

- Linkiniz `https://musteri-motoru-XXXX.onrender.com` biçimindedir (Render panelinde servis sayfasının üstünde).
- Açınca tarayıcı kullanıcı adı ve şifre sorar: **kullanıcı adı herhangi bir şey olabilir**, şifre MOTOR_SIFRE.
- Veriler Render'daki kalıcı diskte (`/var/data/motor.db`) durur; yeniden dağıtımlarda silinmez.
- Yedek almak için: Liste → CSV indir (her proje için).

## Notlar

- Ücretsiz Render planı uygulamayı 15 dakika kullanılmayınca uyutur ve kalıcı disk sunmaz; bu yüzden veriler
  kaybolur ve düzenli tarama çalışmaz. `render.yaml` bu nedenle Starter planını kullanır.
- Kod güncellendiğinde (`main` dalına yeni commit) Render otomatik olarak yeniden kurar.
- Şifre en az 8 karakter olmazsa uygulama güvenlik için başlamaz.
