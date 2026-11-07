# Hazır LinkedIn Aramaları

Linklere tıklayıp sonuçları tara; ilanı **şirket kendisi** açtıysa hedef listeye ekle (`sinyal_turu=ust_duzey_ilan`). İlanı bir işe alım firması açtıysa geç.

Filtre açıklaması: `geoId=102105699` = Türkiye, `f_TPR=r2592000` = son 30 gün, `f_TPR=r604800` = son 7 gün, `f_E=5,6` = Direktör + Yönetici (Executive) seviyesi.

## Genel üst düzey (son 7 gün)
- Direktör / GM / CFO — https://www.linkedin.com/jobs/search/?geoId=102105699&f_E=5%2C6&f_TPR=r604800&keywords=director%20OR%20direkt%C3%B6r%20OR%20%22general%20manager%22%20OR%20CFO
- Ülke müdürü — https://www.linkedin.com/jobs/search/?geoId=102105699&f_TPR=r2592000&keywords=%22country%20manager%22%20OR%20%22%C3%BClke%20m%C3%BCd%C3%BCr%C3%BC%22

## Fonksiyon bazlı (son 30 gün)
- Finans liderleri — https://www.linkedin.com/jobs/search/?geoId=102105699&f_TPR=r2592000&keywords=%22finance%20director%22%20OR%20%22finans%20direkt%C3%B6r%C3%BC%22%20OR%20CFO
- Üretim / fabrika — https://www.linkedin.com/jobs/search/?geoId=102105699&f_TPR=r2592000&keywords=%22fabrika%20m%C3%BCd%C3%BCr%C3%BC%22%20OR%20%22%C3%BCretim%20direkt%C3%B6r%C3%BC%22%20OR%20%22plant%20manager%22
- Satış liderleri — https://www.linkedin.com/jobs/search/?geoId=102105699&f_E=5%2C6&f_TPR=r2592000&keywords=%22sales%20director%22%20OR%20%22sat%C4%B1%C5%9F%20direkt%C3%B6r%C3%BC%22
- İK liderleri — https://www.linkedin.com/jobs/search/?geoId=102105699&f_E=5%2C6&f_TPR=r2592000&keywords=%22HR%20director%22%20OR%20%22%C4%B0K%20direkt%C3%B6r%C3%BC%22%20OR%20CHRO
- Teknoloji liderleri — https://www.linkedin.com/jobs/search/?geoId=102105699&f_E=5%2C6&f_TPR=r2592000&keywords=CTO%20OR%20CIO%20OR%20%22technology%20director%22

## Sektör bazlı (son 30 gün, Direktör+)
- Enerji — https://www.linkedin.com/jobs/search/?geoId=102105699&f_E=5%2C6&f_TPR=r2592000&keywords=enerji%20OR%20energy%20OR%20solar%20OR%20santral
- Otomotiv — https://www.linkedin.com/jobs/search/?geoId=102105699&f_E=5%2C6&f_TPR=r2592000&keywords=otomotiv%20OR%20automotive
- Savunma — https://www.linkedin.com/jobs/search/?geoId=102105699&f_E=5%2C6&f_TPR=r2592000&keywords=savunma%20OR%20defense%20OR%20aerospace

## Kişi bulma (hedef şirkette karar verici)
LinkedIn kişi aramasında: `"<Şirket adı>" İnsan Kaynakları Direktörü` veya `"<Şirket adı>" CHRO`, `"<Şirket adı>" Genel Müdür`.
Bulunan kişi CSV'de `hedef_kisi` sütununa yazılır.
