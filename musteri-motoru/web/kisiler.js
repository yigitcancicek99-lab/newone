"use strict";
// Kayıt penceresindeki "Kişiler ve kanallar" bölümü: firmada ulaşılacak kişiler (LinkedIn profilleriyle),
// hedef unvanlara göre hazır LinkedIn / Google aramaları ve tek tıkla iletişim kanalları.
const KISI_ROLLERI = { karar_verici: "Karar verici", etkileyen: "Etkileyen / öneren", kullanici: "Kullanıcı", kapi: "Kapı açıcı (asistan, santral)", diger: "Diğer" };

function kanalOzet(l) {
  const k = l.kisiler || [];
  const parca = [];
  if (k.length) parca.push(`${k.length} kişi${k.some((x) => x.linkedin) ? " · LinkedIn" : ""}`);
  for (const [a, t] of [["whatsapp", "WhatsApp"], ["iletisim_formu", "form"], ["linkedin", "şirket sayfası"]]) if (l[a]) parca.push(t);
  return parca.length ? `<div><span class="etiket">${e(parca.join(" · "))}</span></div>` : "";
}

function linkedinAramalari(firma, unvanlar) {
  const enc = encodeURIComponent;
  const hedefler = (unvanlar || []).filter(Boolean).slice(0, 6);
  const lnk = (q) => `https://www.linkedin.com/search/results/people/?keywords=${enc(q)}`;
  const xray = (u) => `https://www.google.com/search?q=${enc(`site:linkedin.com/in "${firma}"${u ? ` "${u}"` : ""}`)}`;
  return `<div class="yatay" style="align-items:center"><span class="k">LinkedIn'de çalışan ara:</span>
      <a class="btn kucuk" target="_blank" rel="noopener" href="${e(lnk(firma))}">Tüm çalışanlar</a>
      ${hedefler.map((u) => `<a class="btn kucuk" target="_blank" rel="noopener" href="${e(lnk(firma + " " + u))}">${e(u)}</a>`).join("")}</div>
    <div class="yatay" style="align-items:center;margin-top:6px"><span class="k">Google'da profil ara:</span>
      ${(hedefler.length ? hedefler : [""]).map((u) => `<a class="btn kucuk" target="_blank" rel="noopener" href="${e(xray(u))}">${e(u || "Tüm profiller")}</a>`).join("")}</div>
    <p class="k" style="margin:6px 0 0">Açılan sonuçlardaki profil adresini (linkedin.com/in/…) aşağıya “Kişi ekle” ile kaydedin.</p>`;
}

function kanalLinkleri(l) {
  const enc = encodeURIComponent, ham = (t) => String(t || "").replace(/\D/g, "");
  const k = [];
  if (l.telefon) k.push([`tel:${ham(l.telefon)}`, `Ara ${l.telefon}`]);
  if (l.telefon2) k.push([`tel:${ham(l.telefon2)}`, `Ara ${l.telefon2}`]);
  if (l.whatsapp) k.push([`https://wa.me/${ham(l.whatsapp)}`, "WhatsApp"]);
  if (l.eposta) k.push([`mailto:${l.eposta}`, l.eposta]);
  if (l.iletisim_formu) k.push([l.iletisim_formu, "İletişim formu"]);
  if (l.web) k.push([l.web, "Web sitesi"]);
  if (l.linkedin) k.push([l.linkedin, "LinkedIn sayfası"]);
  if (l.instagram) k.push([/^https?:/.test(l.instagram) ? l.instagram : `https://instagram.com/${l.instagram.replace(/^@/, "")}`, "Instagram"]);
  if (l.facebook) k.push([l.facebook, "Facebook"]);
  if (l.x) k.push([l.x, "X"]);
  k.push([`https://www.google.com/maps/search/${enc(`${l.ad} ${l.sehir || ""}`)}`, "Haritada bul"]);
  return `<div class="yatay">${k.map(([h, t]) => `<a class="btn kucuk" href="${e(h)}" target="_blank" rel="noopener">${e(t)}</a>`).join("")}</div>`;
}

// durum = { kisiler: [...] } — pencere kapanınca kaydedilecek liste
function kisiBolumuCiz(kok, durum, firma, unvanlar, duzenlenen = null) {
  const K = durum.kisiler;
  const form = (k = {}) => `<div class="izgara kisi-form" style="margin-top:8px">
      <label>Ad soyad<input id="kAd" value="${e(k.ad || "")}"></label>
      <label>Unvan<input id="kUnvan" value="${e(k.unvan || "")}" list="kUnvanlar"></label>
      <label>Rol<select id="kRol">${secenek(KISI_ROLLERI, k.rol || "karar_verici")}</select></label>
      <label>LinkedIn profili<input id="kLinkedin" value="${e(k.linkedin || "")}" placeholder="linkedin.com/in/…"></label>
      <label>Kurumsal e-posta<input id="kEposta" type="email" value="${e(k.eposta || "")}"></label>
      <label>Kurumsal telefon / dahili<input id="kTelefon" value="${e(k.telefon || "")}"></label>
      <label class="tam-satir">Not / kaynak<input id="kNot" value="${e(k.not || k.kaynak || "")}" placeholder="ör. Şirket sitesi yönetim sayfası; ilk temas LinkedIn"></label>
      <datalist id="kUnvanlar">${(unvanlar || []).map((u) => `<option value="${e(u)}">`).join("")}</datalist>
      <div class="tam-satir satir"><button type="button" class="btn birincil kucuk" id="kKaydet">${duzenlenen != null ? "Kişiyi güncelle" : "Kişiyi ekle"}</button>
        <button type="button" class="btn kucuk" id="kVazgec">Vazgeç</button></div></div>`;
  kok.innerHTML = `${firma ? linkedinAramalari(firma, unvanlar) : ""}
    <div class="tablo-kap" style="margin-top:10px"><table class="tablo"><tbody>
      ${K.length ? K.map((k, i) => `<tr><td><b>${e(k.ad || "(adı yok)")}</b><div class="k">${e(k.unvan)}</div></td>
        <td><span class="etiket">${e(KISI_ROLLERI[k.rol] || "Diğer")}</span></td>
        <td>${k.linkedin ? `<a href="${e(k.linkedin)}" target="_blank" rel="noopener">LinkedIn profili</a>` : '<span class="k">profil yok</span>'}
          ${k.eposta ? `<div class="k">${e(k.eposta)}</div>` : ""}${k.telefon ? `<div class="k">${e(k.telefon)}</div>` : ""}
          ${k.kaynak && /^https?:/.test(k.kaynak) ? `<div class="k"><a href="${e(k.kaynak)}" target="_blank" rel="noopener">kaynak</a></div>` : k.not ? `<div class="k">${e(k.not)}</div>` : ""}</td>
        <td style="white-space:nowrap"><button type="button" class="btn kucuk" data-kduzen="${i}">Düzenle</button>
          <button type="button" class="btn kucuk tehlike" data-ksil="${i}">Sil</button></td></tr>`).join("")
        : `<tr><td class="k">Henüz kişi yok. Yukarıdaki aramalarla, “Siteden iletişim topla” veya “YZ ile araştır” ile bulabilirsiniz.</td></tr>`}
    </tbody></table></div>
    ${duzenlenen != null || durum.formAcik ? form(duzenlenen != null ? K[duzenlenen] : {}) : `<button type="button" class="btn kucuk" id="kYeni" style="margin-top:8px">+ Kişi ekle</button>`}`;
  const yeniden = (d = null) => kisiBolumuCiz(kok, durum, firma, unvanlar, d);
  $$("[data-ksil]", kok).forEach((b) => (b.onclick = () => { K.splice(Number(b.dataset.ksil), 1); yeniden(); }));
  $$("[data-kduzen]", kok).forEach((b) => (b.onclick = () => yeniden(Number(b.dataset.kduzen))));
  const yeni = $("#kYeni", kok);
  if (yeni) yeni.onclick = () => { durum.formAcik = true; yeniden(); };
  const kaydet = $("#kKaydet", kok);
  if (kaydet) {
    $("#kVazgec", kok).onclick = () => { durum.formAcik = false; yeniden(); };
    kaydet.onclick = () => {
      const v = (id) => $("#" + id, kok).value.trim();
      const kisi = { ...(duzenlenen != null ? K[duzenlenen] : {}), ad: v("kAd"), unvan: v("kUnvan"), rol: v("kRol"),
        linkedin: v("kLinkedin"), eposta: v("kEposta"), telefon: v("kTelefon"), not: v("kNot") };
      if (!kisi.ad && !kisi.linkedin && !kisi.eposta) return bildir("Ad, LinkedIn profili veya e-postadan en az biri gerekli", true);
      if (kisi.linkedin && !/linkedin\.com\/in\//i.test(kisi.linkedin)) bildir("Not: bu bir kişi profili (linkedin.com/in/…) gibi görünmüyor.");
      if (duzenlenen != null) K[duzenlenen] = kisi; else K.push(kisi);
      durum.formAcik = false;
      yeniden();
    };
  }
}
