"use strict";
// Müşteri Bulma Motoru — arayüz
const D = {
  ayar: null, projeler: [], proje: null, leadler: [], sekme: "pano",
  osmAdaylar: [], siralama: { alan: "puan", ters: true },
};
const $ = (s, k = document) => k.querySelector(s);
const $$ = (s, k = document) => [...k.querySelectorAll(s)];
const e = (m) => String(m ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

async function api(yol, yontem = "GET", govde) {
  const yanit = await fetch(yol, {
    method: yontem,
    headers: govde ? { "Content-Type": "application/json" } : {},
    body: govde ? JSON.stringify(govde) : undefined,
  });
  const veri = await yanit.json().catch(() => ({}));
  if (!yanit.ok) throw new Error(veri.hata || `Hata ${yanit.status}`);
  return veri;
}

function bildir(mesaj, hata = false) {
  const b = $("#bildirim");
  b.textContent = mesaj;
  b.className = "bildirim goster" + (hata ? " hata" : "");
  clearTimeout(bildir.z);
  bildir.z = setTimeout(() => (b.className = "bildirim"), hata ? 6000 : 3000);
}

const secenek = (obj, secili) => Object.entries(obj)
  .map(([k, v]) => `<option value="${e(k)}"${k === secili ? " selected" : ""}>${e(v)}</option>`).join("");
const sinyalAdi = (kod) => (D.proje?.sinyaller.find((s) => s.kod === kod) || {}).ad || kod || "";
const sinyalSecenek = (secili = "", bos = "— Sinyal yok —") =>
  `<option value="">${bos}</option>` + D.proje.sinyaller
    .map((s) => `<option value="${e(s.kod)}"${s.kod === secili ? " selected" : ""}>${e(s.ad)}</option>`).join("");
const bugunISO = () => new Date().toISOString().slice(0, 10);
const trTarih = (iso) => (iso ? iso.split("-").reverse().join(".") : "");

// --- Başlangıç -------------------------------------------------------------
async function basla() {
  D.ayar = await api("/api/ayarlar");
  $("#fDurum").innerHTML += secenek(D.ayar.durumlar);
  $("#osmKategori").innerHTML = D.ayar.osm_kategoriler.map((k) => `<option>${e(k)}</option>`).join("");
  $("#iceIzin").innerHTML = secenek(D.ayar.izinler, "bilinmiyor");
  if (!D.ayar.ornek_var) $("#ornekBtn").classList.add("gizli");
  $("#yeniProjeBtn").onclick = $("#bosYeniBtn").onclick = yeniProjeModal;
  $("#ornekBtn").onclick = async () => {
    try { const p = await api("/api/ornek-proje", "POST", {}); await projeleriYukle(p.id); bildir("Örnek proje yüklendi"); }
    catch (err) { bildir(err.message, true); }
  };
  $$(".sekmeler button").forEach((b) => (b.onclick = () => sekmeGoster(b.dataset.sekme)));
  ["#fAra", "#fOncelik", "#fDurum", "#fSinyal", "#fIletisim"].forEach((s) => ($(s).oninput = listeCiz));
  $("#yeniLeadBtn").onclick = () => leadModal(null);
  $("#topluZenginBtn").onclick = topluZenginlestir;
  $("#osmForm").onsubmit = osmAra;
  $("#iceForm").onsubmit = iceAktar;
  const son = Number(localStorageOku("sonProje"));
  await projeleriYukle(son || null);
}

function localStorageOku(k) { try { return localStorage.getItem(k); } catch { return null; } }
function localStorageYaz(k, v) { try { localStorage.setItem(k, v); } catch { /* yoksay */ } }

async function projeleriYukle(secilecek) {
  D.projeler = await api("/api/projeler");
  const nav = $("#projeListesi");
  nav.innerHTML = D.projeler.map((p) =>
    `<a data-id="${p.id}">${e(p.ad)}<small>${e(p.musteri || (p.satis_tipi || "").toUpperCase())} · ${p.lead_sayisi} kayıt</small></a>`).join("");
  $$("a", nav).forEach((a) => (a.onclick = () => projeSec(Number(a.dataset.id))));
  if (!D.projeler.length) {
    $("#bosEkran").classList.remove("gizli");
    $("#projeEkran").classList.add("gizli");
    return;
  }
  $("#bosEkran").classList.add("gizli");
  const id = D.projeler.some((p) => p.id === secilecek) ? secilecek : D.projeler[0].id;
  await projeSec(id);
}

async function projeSec(id) {
  D.proje = await api(`/api/projeler/${id}`);
  localStorageYaz("sonProje", id);
  $$("#projeListesi a").forEach((a) => a.classList.toggle("aktif", Number(a.dataset.id) === id));
  $("#projeEkran").classList.remove("gizli");
  $("#projeAd").textContent = D.proje.ad;
  const tip = D.proje.satis_tipi === "b2c" ? "B2C – tüketiciye" : "B2B – firmalara";
  const teklif = D.proje.teklif_turu === "urun" ? "ürün" : "hizmet";
  $("#projeAlt").textContent = [D.proje.musteri, `${tip} ${teklif} satışı`, D.proje.teklif].filter(Boolean).join(" · ");
  $("#raporBtn").href = `/api/projeler/${id}/rapor?oncelik=A,B&durum=yeni,temas,gorusme,teklif`;
  $("#disaBtn").href = `/api/projeler/${id}/disa-aktar`;
  $("#fSinyal").innerHTML = `<option value="">Tüm sinyaller</option><option value="-">Sinyalsiz</option>` +
    D.proje.sinyaller.map((s) => `<option value="${e(s.kod)}">${e(s.ad)}</option>`).join("");
  $("#iceSinyal").innerHTML = sinyalSecenek("", "— Yok —");
  $("#iceIzin").value = D.proje.satis_tipi === "b2c" ? "bilinmiyor" : "kurumsal";
  $("#osmSonuc").innerHTML = "";
  await leadleriYukle();
  sekmeGoster(D.sekme);
}

async function leadleriYukle() {
  D.leadler = await api(`/api/projeler/${D.proje.id}/leadler`);
  panoCiz();
  listeCiz();
}

function sekmeGoster(ad) {
  D.sekme = ad;
  $$(".sekmeler button").forEach((b) => b.classList.toggle("aktif", b.dataset.sekme === ad));
  $$(".sekme").forEach((s) => s.classList.toggle("gizli", s.id !== `sekme-${ad}`));
  if (ad === "ayar") ayarCiz();
}

// --- Pano --------------------------------------------------------------------
function panoCiz() {
  const L = D.leadler;
  const aktif = L.filter((l) => !["kazanildi", "kaybedildi", "uygun_degil"].includes(l.durum));
  const say = (f) => L.filter(f).length;
  const yuzde = (n) => (L.length ? Math.round((100 * n) / L.length) : 0);
  const telefonlu = say((l) => l.telefon || l.telefon2);
  const epostali = say((l) => l.eposta);
  const kutu = (deger, etiket) => `<div class="kutu"><b>${deger}</b><span>${etiket}</span></div>`;

  const sinir = new Date(); sinir.setDate(sinir.getDate() + 7);
  const sinirISO = sinir.toISOString().slice(0, 10);
  const takipler = aktif.filter((l) => l.sonraki_tarih && l.sonraki_tarih <= sinirISO)
    .sort((a, b) => a.sonraki_tarih.localeCompare(b.sonraki_tarih));
  const yeniA = aktif.filter((l) => l.durum === "yeni" && l.oncelik === "A" && l.iletisime_uygun).slice(0, 12);

  const huniSira = ["yeni", "temas", "gorusme", "teklif", "kazanildi"];
  const enCok = Math.max(1, ...huniSira.map((d) => say((l) => l.durum === d)));
  const huni = huniSira.map((d) => {
    const n = say((l) => l.durum === d);
    return `<div class="huni-satir"><span>${e(D.ayar.durumlar[d])}</span>
      <div class="huni-cubuk"><div style="width:${(100 * n) / enCok}%"></div></div><b>${n}</b></div>`;
  }).join("");

  const kucukTablo = (liste, bos, sutun) => liste.length
    ? `<table class="tablo"><tbody>${liste.map((l) => `<tr data-id="${l.id}">
        <td><span class="rozet ${l.oncelik}">${l.oncelik}</span></td>
        <td><b>${e(l.ad)}</b><div class="k">${e([l.sehir, l.sektor].filter(Boolean).join(" · "))}</div></td>
        <td>${sutun(l)}</td></tr>`).join("")}</tbody></table>`
    : `<p class="aciklama">${bos}</p>`;

  $("#sekme-pano").innerHTML = `
    <div class="kutular">
      ${kutu(L.length, "Toplam kayıt")}
      ${kutu(say((l) => l.oncelik === "A"), "A – bu hafta ara")}
      ${kutu(say((l) => l.oncelik === "B"), "B – 2 hafta içinde")}
      ${kutu(`${yuzde(telefonlu)}%`, `Telefonu olan (${telefonlu})`)}
      ${kutu(`${yuzde(epostali)}%`, `E-postası olan (${epostali})`)}
      ${kutu(say((l) => l.iletisime_uygun), D.proje.satis_tipi === "b2c" ? "Açık rızalı (ulaşılabilir)" : "İletişime uygun")}
    </div>
    <div class="iki">
      <div class="kart"><h2>Bu hafta aranacak yeni A'lar</h2>
        ${kucukTablo(yeniA, "Henüz A öncelikli yeni kayıt yok. Sinyal ekleyin veya hedefleri daraltın.",
          (l) => `${e(l.telefon || l.eposta || "iletişim eksik")}<div class="k">${e(sinyalAdi(l.sinyal))}</div>`)}
      </div>
      <div class="kart"><h2>Satış hunisi</h2>${huni}
        <h2 style="margin-top:18px">Vadesi gelen takipler (7 gün)</h2>
        ${kucukTablo(takipler, "Vadesi gelen takip yok.",
          (l) => `<b>${trTarih(l.sonraki_tarih)}</b><div class="k">${e(l.sonraki_adim)}</div>`)}
      </div>
    </div>
    ${D.proje.satis_tipi === "b2c" ? `<div class="bilgi"><b>B2C hatırlatma:</b> Bireylere SMS/e-posta/arama ile ticari ileti göndermek
      için İYS'de kayıtlı onay gerekir (6563 sayılı Kanun) ve kişisel veriler KVKK kapsamındadır. Bu projede yalnızca
      <b>“Açık rıza var”</b> işaretli kişiler iletişime uygun sayılır. Kişi listesi satın almak veya internetten kişi
      numarası toplamak yerine form, kampanya, etkinlik ve tavsiye gibi izinli kaynaklarla liste büyütün.</div>` : ""}`;
  $$("#sekme-pano tr[data-id]").forEach((tr) => (tr.onclick = () => leadModal(Number(tr.dataset.id))));
}

// --- Liste -------------------------------------------------------------------
function filtreliLeadler() {
  const ara = $("#fAra").value.toLocaleLowerCase("tr");
  const o = $("#fOncelik").value, d = $("#fDurum").value, s = $("#fSinyal").value, il = $("#fIletisim").value;
  return D.leadler.filter((l) => {
    if (o && l.oncelik !== o) return false;
    if (d && l.durum !== d) return false;
    if (s === "-" ? l.sinyal : s && l.sinyal !== s) return false;
    if (il === "telefonlu" && !(l.telefon || l.telefon2)) return false;
    if (il === "telefonsuz" && (l.telefon || l.telefon2)) return false;
    if (il === "epostasiz" && l.eposta) return false;
    if (ara) {
      const metin = [l.ad, l.sehir, l.ilce, l.sektor, l.yetkili, l.unvan, l.telefon, l.eposta, l.web, l.notlar, l.sinyal_ozet]
        .join(" ").toLocaleLowerCase("tr");
      if (!metin.includes(ara)) return false;
    }
    return true;
  });
}

function listeCiz() {
  const liste = filtreliLeadler();
  const { alan, ters } = D.siralama;
  liste.sort((a, b) => {
    const x = a[alan] ?? "", y = b[alan] ?? "";
    const k = typeof x === "number" ? x - y : String(x).localeCompare(String(y), "tr");
    return ters ? -k : k;
  });
  const basliklar = [["puan", "Puan"], ["ad", "Firma / Kişi"], ["sektor", "Sektör"], ["sehir", "Konum"],
    ["telefon", "İletişim"], ["sinyal", "Sinyal"], ["durum", "Durum"], ["sonraki_tarih", "Sonraki adım"]];
  const ok = (a) => (a === alan ? (ters ? " ↓" : " ↑") : "");
  $("#leadTablo").innerHTML = `<thead><tr>${basliklar.map(([a, b]) => `<th data-alan="${a}">${b}${ok(a)}</th>`).join("")}</tr></thead>
    <tbody>${liste.map((l) => `<tr data-id="${l.id}" class="${["kaybedildi", "uygun_degil"].includes(l.durum) ? "soluk" : ""}">
      <td><span class="rozet ${l.oncelik}">${l.oncelik}</span> ${l.puan.toFixed(0)}</td>
      <td><b>${e(l.ad)}</b>${l.yetkili ? `<div class="k">${e(l.yetkili)}${l.unvan ? " – " + e(l.unvan) : ""}</div>` : ""}
        ${l.web ? `<div class="k">${e(l.web.replace(/^https?:\/\/(www\.)?/, "").replace(/\/$/, ""))}</div>` : ""}</td>
      <td>${e(l.sektor)}</td>
      <td>${e(l.sehir)}${l.ilce ? `<div class="k">${e(l.ilce)}</div>` : ""}</td>
      <td>${e(l.telefon) || '<span class="etiket uyari">telefon yok</span>'}${l.eposta ? `<div class="k">${e(l.eposta)}</div>` : ""}
        ${l.iletisime_uygun ? "" : '<div><span class="etiket uyari">izin yok</span></div>'}</td>
      <td>${e(sinyalAdi(l.sinyal))}${l.sinyal_tarihi ? `<div class="k">${trTarih(l.sinyal_tarihi)}</div>` : ""}</td>
      <td><span class="etiket">${e(D.ayar.durumlar[l.durum] || l.durum)}</span></td>
      <td>${e(l.sonraki_adim)}${l.sonraki_tarih ? `<div class="k">${trTarih(l.sonraki_tarih)}</div>` : ""}</td>
    </tr>`).join("")}</tbody>`;
  if (!liste.length) $("#leadTablo").innerHTML += `<tbody><tr><td colspan="8" class="k">Kayıt yok. “Müşteri bul” veya “İçe aktar” sekmelerinden liste oluşturun.</td></tr></tbody>`;
  $$("#leadTablo th").forEach((th) => (th.onclick = () => {
    const a = th.dataset.alan;
    D.siralama = { alan: a, ters: D.siralama.alan === a ? !D.siralama.ters : a === "puan" };
    listeCiz();
  }));
  $$("#leadTablo tbody tr[data-id]").forEach((tr) => (tr.onclick = () => leadModal(Number(tr.dataset.id))));
}

// --- Lead formu --------------------------------------------------------------
function leadModal(id) {
  const l = id ? D.leadler.find((x) => x.id === id) : { durum: "yeni", izin: D.proje.satis_tipi === "b2c" ? "bilinmiyor" : "kurumsal", tur: D.proje.satis_tipi === "b2c" ? "kisi" : "firma" };
  const b2c = D.proje.satis_tipi === "b2c";
  const g = (ad, etiket, tur = "text", ek = "") =>
    `<label>${etiket}<input name="${ad}" type="${tur}" value="${e(l[ad] || "")}" ${ek}></label>`;
  const detay = l.puan_detay ? Object.entries(l.puan_detay).map(([k, v]) => `${k.replace("_", "/")}: ${v}`).join(" · ") : "";
  $("#modalForm").innerHTML = `
    <div class="baslik"><h2>${id ? e(l.ad) : "Yeni kayıt"}</h2>
      ${id ? `<div><span class="rozet ${l.oncelik}">${l.oncelik}</span> <b>${l.puan.toFixed(0)}</b> <span class="k">${e(detay)}</span></div>` : ""}</div>
    <div class="izgara">
      ${g("ad", b2c ? "Ad soyad *" : "Firma adı *", "text", "required")}
      <label>Tür<select name="tur">${secenek({ firma: "Firma", kisi: "Kişi" }, l.tur)}</select></label>
      ${g("sektor", b2c ? "Segment / ilgi alanı" : "Sektör")}
      <label>Büyüklük<select name="buyukluk"><option value="">—</option>${secenek(D.ayar.buyuklukler, l.buyukluk)}</select></label>
      ${g("sehir", "Şehir")}${g("ilce", "İlçe")}
      <label class="tam-satir">Adres<input name="adres" value="${e(l.adres || "")}"></label>
      <div class="grup-baslik">İletişim</div>
      ${g("yetkili", b2c ? "İlgili kişi" : "Yetkili kişi")}${g("unvan", "Unvan")}
      ${g("telefon", "Telefon", "tel")}${g("telefon2", "Telefon 2", "tel")}
      ${g("eposta", "E-posta", "email")}${g("web", "Web sitesi")}
      ${g("linkedin", "LinkedIn")}${g("instagram", "Instagram")}
      <label>İzin durumu<select name="izin">${secenek(D.ayar.izinler, l.izin || "bilinmiyor")}</select></label>
      <div class="grup-baslik">Sinyal (neden şimdi?)</div>
      <label>Sinyal<select name="sinyal">${sinyalSecenek(l.sinyal)}</select></label>
      ${g("sinyal_tarihi", "Sinyal tarihi", "date")}
      <label class="tam-satir">Sinyal özeti<input name="sinyal_ozet" value="${e(l.sinyal_ozet || "")}"></label>
      <label class="tam-satir">Kaynak (link)<input name="kaynak" value="${e(l.kaynak || "")}"></label>
      <div class="grup-baslik">Takip</div>
      <label>Durum<select name="durum">${secenek(D.ayar.durumlar, l.durum)}</select></label>
      ${g("sonraki_adim", "Sonraki adım")}${g("sonraki_tarih", "Sonraki adım tarihi", "date")}
      <label class="tam-satir">Notlar<textarea name="notlar" rows="3">${e(l.notlar || "")}</textarea></label>
    </div>
    <div class="modal-alt">
      <div class="satir">
        ${id ? `<button type="button" class="btn tehlike" id="mSil">Sil</button>` : ""}
        ${id && l.web ? `<button type="button" class="btn" id="mZengin">Siteden iletişim topla</button>` : ""}
        ${l.kaynak ? `<a class="btn" href="${e(l.kaynak)}" target="_blank" rel="noopener">Kaynağı aç</a>` : ""}
      </div>
      <div class="satir"><button type="button" class="btn" id="mIptal">Vazgeç</button>
        <button type="submit" class="btn birincil">Kaydet</button></div>
    </div>`;
  const dlg = $("#modal");
  $("#mIptal").onclick = () => dlg.close();
  $("#modalForm").onsubmit = async (ev) => {
    ev.preventDefault();
    const veri = Object.fromEntries(new FormData($("#modalForm")));
    try {
      if (id) await api(`/api/leadler/${id}`, "PUT", veri);
      else {
        const s = await api(`/api/projeler/${D.proje.id}/leadler`, "POST", veri);
        if (s.mukerrer) bildir("Bu kayıt zaten vardı; boş alanları dolduruldu.");
      }
      dlg.close();
      await leadleriYukle();
      if (!id) projeSayisiniGuncelle();
    } catch (err) { bildir(err.message, true); }
  };
  if (id) {
    $("#mSil").onclick = async () => {
      if (!confirm(`“${l.ad}” silinsin mi?`)) return;
      await api(`/api/leadler/${id}`, "DELETE");
      dlg.close(); await leadleriYukle(); projeSayisiniGuncelle();
    };
    const z = $("#mZengin");
    if (z) z.onclick = async () => {
      z.disabled = true; z.textContent = "Taranıyor…";
      try {
        const s = await api(`/api/leadler/${id}/zenginlestir`, "POST", {});
        bildir(s.guncellenen.length ? `Eklendi: ${s.guncellenen.join(", ")}` : "Yeni bilgi bulunamadı");
        await leadleriYukle(); leadModal(id);
      } catch (err) { bildir(err.message, true); z.disabled = false; z.textContent = "Siteden iletişim topla"; }
    };
  }
  if (!dlg.open) dlg.showModal();
}

async function projeSayisiniGuncelle() {
  const p = await api("/api/projeler");
  D.projeler = p;
  const bu = p.find((x) => x.id === D.proje.id);
  const a = $(`#projeListesi a[data-id="${D.proje.id}"] small`);
  if (a && bu) a.textContent = `${bu.musteri || bu.satis_tipi.toUpperCase()} · ${bu.lead_sayisi} kayıt`;
}

// --- Toplu zenginleştirme ------------------------------------------------------
async function topluZenginlestir() {
  const hedef = filtreliLeadler().filter((l) => l.web && (!(l.telefon || l.telefon2) || !l.eposta));
  if (!hedef.length) return bildir("Web adresi olup iletişimi eksik kayıt yok (filtreler uygulanıyor).");
  if (!confirm(`${hedef.length} kaydın web sitesi taranacak (kayıt başına birkaç saniye). Devam edilsin mi?`)) return;
  const kutu = $("#zenginIlerleme"), cubuk = $(".cubuk div", kutu), yazi = $("span", kutu), btn = $("#topluZenginBtn");
  kutu.classList.remove("gizli"); btn.disabled = true;
  let bulunan = 0, hata = 0;
  for (let i = 0; i < hedef.length; i++) {
    yazi.textContent = `${i + 1}/${hedef.length} · ${hedef[i].ad}`;
    cubuk.style.width = `${(100 * i) / hedef.length}%`;
    try {
      const s = await api(`/api/leadler/${hedef[i].id}/zenginlestir`, "POST", {});
      if (s.guncellenen.length) bulunan++;
    } catch { hata++; }
  }
  cubuk.style.width = "100%";
  yazi.textContent = `Bitti: ${bulunan} kayıt güncellendi, ${hata} siteye ulaşılamadı.`;
  btn.disabled = false;
  await leadleriYukle();
}

// --- OSM araması -----------------------------------------------------------------
async function osmAra(ev) {
  ev.preventDefault();
  const veri = Object.fromEntries(new FormData(ev.target));
  const durum = $("#osmDurum");
  durum.textContent = "Aranıyor… (büyük şehirlerde 30–60 sn sürebilir)";
  $("#osmSonuc").innerHTML = "";
  try {
    D.osmAdaylar = await api(`/api/projeler/${D.proje.id}/osm-ara`, "POST", veri);
    durum.textContent = `${D.osmAdaylar.length} işletme bulundu.`;
    osmSonucCiz();
  } catch (err) { durum.textContent = ""; bildir(err.message, true); }
}

function osmSonucCiz() {
  const A = D.osmAdaylar;
  if (!A.length) { $("#osmSonuc").innerHTML = `<div class="kart k">Sonuç yok. İl/ilçe adını kontrol edin veya başka kategori deneyin.</div>`; return; }
  const tel = A.filter((a) => a.telefon).length, web = A.filter((a) => a.web).length;
  $("#osmSonuc").innerHTML = `<div class="kart">
    <div class="baslik"><div><h2>${A.length} sonuç</h2><div class="k">${tel} telefonlu · ${web} web siteli · ${A.filter((a) => a.mukerrer).length} zaten listede</div></div>
      <div class="satir">
        <label class="k">Eklenenlere sinyal: <select id="osmSinyal">${sinyalSecenek()}</select></label>
        <button class="btn" id="osmTumu">Tümünü seç</button>
        <button class="btn birincil" id="osmEkle">Seçilenleri ekle</button></div></div>
    <div class="tablo-kap" style="margin-top:10px"><table class="tablo"><thead><tr><th></th><th>Ad</th><th>Adres</th><th>Telefon</th><th>Web / e-posta</th></tr></thead>
    <tbody>${A.map((a, i) => `<tr class="${a.mukerrer ? "soluk" : ""}">
      <td><input type="checkbox" data-i="${i}" ${a.mukerrer ? "" : "checked"}></td>
      <td><b>${e(a.ad)}</b>${a.mukerrer ? ' <span class="etiket">listede</span>' : ""}</td>
      <td class="k">${e(a.adres || a.ilce)}</td><td>${e(a.telefon)}</td>
      <td class="k">${e(a.web)}${a.eposta ? "<br>" + e(a.eposta) : ""}</td></tr>`).join("")}</tbody></table></div></div>`;
  $$("#osmSonuc tbody tr").forEach((tr) => (tr.onclick = (ev) => {
    if (ev.target.tagName !== "INPUT") { const c = $("input", tr); c.checked = !c.checked; }
  }));
  $("#osmTumu").onclick = () => { const k = $$("#osmSonuc input[type=checkbox]"); const hepsi = k.every((c) => c.checked); k.forEach((c) => (c.checked = !hepsi)); };
  $("#osmEkle").onclick = async () => {
    const sinyal = $("#osmSinyal").value;
    const secili = $$("#osmSonuc input[type=checkbox]:checked").map((c) => ({ ...A[c.dataset.i], sinyal, sinyal_tarihi: sinyal ? bugunISO() : "" }));
    if (!secili.length) return bildir("Seçili kayıt yok");
    secili.forEach((s) => delete s.mukerrer);
    try {
      const s = await api(`/api/projeler/${D.proje.id}/leadler`, "POST", { leadler: secili });
      bildir(`${s.eklenen} eklendi, ${s.mukerrer} mükerrer (boş alanları dolduruldu).`);
      D.osmAdaylar.forEach((a, i) => { if ($(`#osmSonuc input[data-i="${i}"]`).checked) a.mukerrer = true; });
      osmSonucCiz();
      await leadleriYukle(); projeSayisiniGuncelle();
    } catch (err) { bildir(err.message, true); }
  };
}

// --- İçe aktarma ------------------------------------------------------------------
async function iceAktar(ev) {
  ev.preventDefault();
  const dosya = $("#iceDosya").files[0];
  let metin = $("#iceMetin").value;
  if (dosya) metin = await dosyaOku(dosya);
  if (!metin.trim()) return bildir("Dosya seçin veya metin yapıştırın", true);
  const f = Object.fromEntries(new FormData(ev.target));
  const varsayilan = { sektor: f.sektor, sehir: f.sehir, sinyal: f.sinyal, izin: f.izin, sinyal_tarihi: f.sinyal ? bugunISO() : "" };
  try {
    const s = await api(`/api/projeler/${D.proje.id}/ice-aktar`, "POST", { csv: metin, varsayilan });
    $("#iceSonuc").innerHTML = `<div class="bilgi"><b>${s.eklenen}</b> kayıt eklendi · <b>${s.mukerrer}</b> mükerrer · <b>${s.hatali}</b> hatalı
      <div class="k">Eşlenen sütunlar: ${Object.entries(s.esleme).map(([b, a]) => `${e(b)} → ${e(a)}`).join(", ")}</div>
      ${s.eslesmeyen.length ? `<div class="k">Notlara yazılan sütunlar: ${s.eslesmeyen.map(e).join(", ")}</div>` : ""}
      ${s.hatalar.length ? `<div class="k">${s.hatalar.map(e).join("<br>")}</div>` : ""}</div>`;
    ev.target.reset(); $("#iceMetin").value = "";
    await leadleriYukle(); projeSayisiniGuncelle();
  } catch (err) { bildir(err.message, true); }
}

async function dosyaOku(dosya) {
  const tampon = await dosya.arrayBuffer();
  try { return new TextDecoder("utf-8", { fatal: true }).decode(tampon); }
  catch { return new TextDecoder("windows-1254").decode(tampon); } // Türkçe Excel CSV'leri
}

// --- Proje ----------------------------------------------------------------------
function yeniProjeModal() {
  const sablonlar = D.ayar.sablonlar;
  $("#modalForm").innerHTML = `<h2>Yeni proje</h2>
    <p class="aciklama">Proje = bir müşteriniz için (veya sattığınız bir ürün/hizmet için) hedef kitle ve kurallar. Şablon sadece başlangıç ayarlarıdır; sonra değiştirebilirsiniz.</p>
    <div class="izgara">
      <label>Proje adı *<input name="ad" required placeholder="ör. ABC Yazılım – İstanbul klinikleri"></label>
      <label>Müşteri (kimin için çalışıyorsunuz)<input name="musteri" placeholder="ör. ABC Yazılım Ltd."></label>
      <label class="tam-satir">Şablon<select name="sablon" id="ySablon">${Object.entries(sablonlar).map(([k, v]) => `<option value="${k}">${e(v.ad)}</option>`).join("")}</select>
        <span class="k" id="ySablonAcik"></span></label>
      <label class="tam-satir">Satılan ürün / hizmet<input name="teklif" placeholder="ör. Klinik randevu yazılımı"></label>
      <label class="tam-satir">Hedef şehirler (virgülle)<input name="hedef_sehirler" placeholder="ör. İstanbul, Kocaeli"></label>
    </div>
    <div class="modal-alt"><span></span><div class="satir"><button type="button" class="btn" id="mIptal">Vazgeç</button>
      <button class="btn birincil" type="submit">Oluştur</button></div></div>`;
  const aciklama = () => ($("#ySablonAcik").textContent = sablonlar[$("#ySablon").value].aciklama);
  $("#ySablon").onchange = aciklama; aciklama();
  $("#mIptal").onclick = () => $("#modal").close();
  $("#modalForm").onsubmit = async (ev) => {
    ev.preventDefault();
    try {
      const p = await api("/api/projeler", "POST", Object.fromEntries(new FormData($("#modalForm"))));
      $("#modal").close();
      D.sekme = "ayar";
      await projeleriYukle(p.id);
      bildir("Proje oluşturuldu. Hedefleri ve sinyalleri kontrol edin.");
    } catch (err) { bildir(err.message, true); }
  };
  $("#modal").showModal();
}

function ayarCiz() {
  const p = D.proje;
  const liste = (a) => e((p[a] || []).join(", "));
  $("#sekme-ayar").innerHTML = `<form id="ayarForm">
    <div class="kart"><h2>Genel</h2><div class="izgara">
      <label>Proje adı<input name="ad" value="${e(p.ad)}" required></label>
      <label>Müşteri<input name="musteri" value="${e(p.musteri)}"></label>
      <label>Satış tipi<select name="satis_tipi">${secenek({ b2b: "B2B – firmalara", b2c: "B2C – tüketiciye" }, p.satis_tipi)}</select></label>
      <label>Ne satılıyor<select name="teklif_turu">${secenek({ urun: "Ürün", hizmet: "Hizmet" }, p.teklif_turu)}</select></label>
      <label class="tam-satir">Ürün / hizmet açıklaması<input name="teklif" value="${e(p.teklif)}"></label>
    </div></div>
    <div class="kart"><h2>İdeal müşteri profili</h2>
      <p class="aciklama">Kayıtlar bu hedeflere uydukça puan alır. Boş bırakılan hedef puanı etkilemez (nötr).</p>
      <div class="izgara">
        <label class="tam-satir">${p.satis_tipi === "b2c" ? "Hedef segmentler / ilgi alanları" : "Hedef sektörler"} (virgülle)<input name="hedef_sektorler" value="${liste("hedef_sektorler")}"></label>
        <label class="tam-satir">Hedef şehir / ilçeler (virgülle)<input name="hedef_sehirler" value="${liste("hedef_sehirler")}"></label>
        <label class="tam-satir">Hedef unvanlar – karar vericiler (virgülle)<input name="hedef_unvanlar" value="${liste("hedef_unvanlar")}"></label>
        <div class="tam-satir"><span class="k">Hedef firma büyüklüğü</span><div class="secenekler">
          ${Object.entries(D.ayar.buyuklukler).map(([k, v]) => `<label><input type="checkbox" name="buyukluk_${k}" ${p.hedef_buyuklukler.includes(k) ? "checked" : ""}> ${e(v)}</label>`).join("")}
        </div></div>
        <label>A eşiği (bu hafta ara)<input name="esik_a" type="number" min="0" max="100" value="${p.esik_a}"></label>
        <label>B eşiği (2 hafta içinde)<input name="esik_b" type="number" min="0" max="100" value="${p.esik_b}"></label>
      </div></div>
    <div class="kart"><h2>Satın alma sinyalleri</h2>
      <p class="aciklama"><b>Ağırlık</b> (0–30): sinyalin satın almayı ne kadar güçlü gösterdiği. <b>Yarı ömür</b> (gün): sinyalin
        değerinin kaç günde yarıya indiği — ilanlar hızlı soğur, yatırımlar aylarca sıcak kalır.
        Puan (0–100) = sinyal 30 + tazelik 20 + sektör 20 + konum 10 + büyüklük/unvan 10 + iletişim tamlığı 10.</p>
      <table class="tablo sinyal-tablo"><thead><tr><th>Kod</th><th>Ad</th><th>Ağırlık</th><th>Yarı ömür</th><th></th></tr></thead>
        <tbody id="sinyalSatirlari">${p.sinyaller.map(sinyalSatiri).join("")}</tbody></table>
      <button type="button" class="btn kucuk" id="sinyalEkle" style="margin-top:8px">+ Sinyal ekle</button>
    </div>
    <div class="satir" style="justify-content:space-between">
      <button type="button" class="btn tehlike" id="projeSil">Projeyi sil</button>
      <button class="btn birincil" type="submit">Ayarları kaydet</button></div>
  </form>`;
  const satirBagla = () => $$("#sinyalSatirlari .sil").forEach((b) => (b.onclick = () => b.closest("tr").remove()));
  satirBagla();
  $("#sinyalEkle").onclick = () => {
    $("#sinyalSatirlari").insertAdjacentHTML("beforeend", sinyalSatiri({ kod: "", ad: "", agirlik: 15, yari_omur: 90 }));
    satirBagla();
  };
  $("#projeSil").onclick = async () => {
    if (!confirm(`“${p.ad}” ve içindeki ${D.leadler.length} kayıt kalıcı olarak silinsin mi?`)) return;
    await api(`/api/projeler/${p.id}`, "DELETE");
    await projeleriYukle(null);
  };
  $("#ayarForm").onsubmit = async (ev) => {
    ev.preventDefault();
    const f = new FormData(ev.target);
    const sinyaller = $$("#sinyalSatirlari tr").map((tr) => {
      const [kod, ad, agirlik, yari] = $$("input", tr).map((i) => i.value.trim());
      return { kod: kod || slug(ad), ad: ad || kod, agirlik: Number(agirlik) || 0, yari_omur: Number(yari) || 90 };
    }).filter((s) => s.kod);
    const veri = {
      ad: f.get("ad"), musteri: f.get("musteri"), satis_tipi: f.get("satis_tipi"), teklif_turu: f.get("teklif_turu"),
      teklif: f.get("teklif"), hedef_sektorler: f.get("hedef_sektorler"), hedef_sehirler: f.get("hedef_sehirler"),
      hedef_unvanlar: f.get("hedef_unvanlar"), esik_a: f.get("esik_a"), esik_b: f.get("esik_b"), sinyaller,
      hedef_buyuklukler: Object.keys(D.ayar.buyuklukler).filter((k) => f.get(`buyukluk_${k}`)),
    };
    try {
      await api(`/api/projeler/${p.id}`, "PUT", veri);
      await projeleriYukle(p.id);
      sekmeGoster("ayar");
      bildir("Kaydedildi; puanlar yeniden hesaplandı.");
    } catch (err) { bildir(err.message, true); }
  };
}

const sinyalSatiri = (s) => `<tr><td><input value="${e(s.kod)}" placeholder="otomatik"></td><td><input value="${e(s.ad)}" placeholder="ör. Yeni şube açtı"></td>
  <td><input type="number" min="0" max="30" value="${s.agirlik}"></td><td><input type="number" min="1" value="${s.yari_omur}"></td>
  <td><button type="button" class="btn kucuk tehlike sil">Sil</button></td></tr>`;
const slug = (m) => m.toLocaleLowerCase("tr").replace(/[çğıöşü]/g, (c) => ({ ç: "c", ğ: "g", ı: "i", ö: "o", ş: "s", ü: "u" }[c]))
  .replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "");

basla().catch((err) => bildir(err.message, true));
