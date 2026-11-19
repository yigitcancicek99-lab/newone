"use strict";
// Mülakat, yapay zekâ analizi, sinyal radarı ve internette aday araştırması ekranları

// --- Yapay zekâ ayarları -----------------------------------------------------------
function yzNoktaGuncelle(d) {
  D.yz = d;
  $("#yzNokta").classList.toggle("acik", !!d?.hazir);
  $("#yzAyarBtn").title = d?.hazir ? `Hazır · ${d.model}` : "Yapay zekâ kapalı – ayarlamak için tıklayın";
}

function yzAyarModal() {
  const d = D.yz || {};
  $("#modalForm").innerHTML = `<h2>Yapay zekâ ayarları</h2>
    <p class="aciklama">Mülakat analizi, haberlerin değerlendirilmesi ve internette araştırma için Claude kullanılır.
      API anahtarını <b>console.anthropic.com</b> → API Keys bölümünden alabilirsiniz. Anahtar yalnızca bu bilgisayardaki
      veritabanında saklanır ve sadece Anthropic'e gönderilir.</p>
    ${d.kurulu ? "" : `<div class="bilgi"><b>Önce paketi kurun:</b> terminalde <code>pip install anthropic</code> çalıştırıp uygulamayı yeniden başlatın.</div>`}
    <div class="izgara" style="margin-top:12px">
      <label class="tam-satir">Claude API anahtarı ${d.anahtar_var ? `<span class="etiket">kayıtlı (${d.anahtar_kaynagi === "ortam" ? "ortam değişkeni" : "uygulama"})</span>` : ""}
        <input name="api_anahtari" type="password" autocomplete="off" placeholder="${d.anahtar_var ? "Değiştirmek için yeni anahtar girin" : "sk-ant-…"}"></label>
      <label class="tam-satir">Model<select name="model">${secenek(d.modeller || {}, d.model)}</select>
        <span class="k">Opus 5.5 en isabetli sonuçları verir. Çok sayıda haber taranan projelerde maliyeti düşürmek isterseniz Haiku 5.5 seçebilirsiniz.</span></label>
    </div>
    <div class="modal-alt">${d.anahtar_kaynagi === "uygulama" ? `<button type="button" class="btn tehlike" id="yzSil">Anahtarı sil</button>` : "<span></span>"}
      <div class="satir"><button type="button" class="btn" id="mIptal">Vazgeç</button><button class="btn birincil" type="submit">Kaydet</button></div></div>`;
  $("#mIptal").onclick = () => $("#modal").close();
  const sil = $("#yzSil");
  if (sil) sil.onclick = async () => { yzNoktaGuncelle(await api("/api/yz", "PUT", { api_anahtari: "" })); $("#modal").close(); };
  $("#modalForm").onsubmit = async (ev) => {
    ev.preventDefault();
    const f = Object.fromEntries(new FormData($("#modalForm")));
    const veri = { model: f.model };
    if (f.api_anahtari) veri.api_anahtari = f.api_anahtari;
    try { yzNoktaGuncelle(await api("/api/yz", "PUT", veri)); $("#modal").close(); bildir("Kaydedildi"); }
    catch (err) { bildir(err.message, true); }
  };
  $("#modal").showModal();
}

function yzGerekli() {
  if (D.yz?.hazir) return true;
  bildir("Bu özellik için yapay zekâ ayarlarından Claude API anahtarı girin.", true);
  yzAyarModal();
  return false;
}

// --- Mülakat -----------------------------------------------------------------------
function mulakatCiz() {
  const c = D.proje.mulakat || {};
  const dolu = D.sorular.reduce((n, b) => n + b.sorular.filter((s) => (c[s.kod] || "").trim()).length, 0);
  const toplam = D.sorular.reduce((n, b) => n + b.sorular.length, 0);
  const a = D.proje.yz_analiz || {};
  $("#sekme-mulakat").innerHTML = `
    <div class="kart">
      <div class="baslik"><div><h2>Müşteri mülakatı</h2>
        <p class="aciklama">Hizmet verdiğiniz firmayla görüşmede bu soruları sorun ve cevapları buraya yazın (kısa notlar yeterli).
          Ardından <b>Yapay zekâ ile analiz et</b>: ideal müşteri profili, satın alma sinyalleri, haber tarama sorguları,
          ilk temas mesajı ve sormanız gereken ek sorular çıkarılır.</p></div>
        <div class="satir"><span class="etiket">${dolu}/${toplam} cevaplandı</span>
          <a class="btn" href="/api/projeler/${D.proje.id}/mulakat-formu" target="_blank">Yazdırılabilir form</a></div></div>
    </div>
    <form id="mulakatForm">
      ${D.sorular.map((b) => `<div class="kart"><h2>${e(b.bolum)}</h2>
        ${b.sorular.map((s) => `<div class="soru"><b>${e(s.soru)}</b><div class="k">${e(s.neden)}</div>
          <textarea name="${s.kod}" rows="2">${e(c[s.kod] || "")}</textarea></div>`).join("")}</div>`).join("")}
      <div class="kart"><h2>Serbest görüşme notları</h2>
        <textarea name="serbest_notlar" rows="5">${e(c.serbest_notlar || "")}</textarea>
        ${(a.eksik_sorular || []).length ? `<h2 style="margin-top:16px">Yapay zekânın önerdiği ek soruların cevapları</h2>
          <ol class="k">${a.eksik_sorular.map((q) => `<li>${e(q)}</li>`).join("")}</ol>
          <textarea name="ek_cevaplar" rows="5" placeholder="Ek soruların cevaplarını buraya yazın, sonra tekrar analiz edin">${e(c.ek_cevaplar || "")}</textarea>` : ""}
      </div>
      <div class="satir" style="justify-content:flex-end;margin-bottom:16px">
        <button class="btn" type="submit">Cevapları kaydet</button>
        <button class="btn birincil" type="button" id="analizBtn">Kaydet ve yapay zekâ ile analiz et</button>
      </div>
    </form>
    <div id="analizKutu">${a.ozet ? analizHtml(a) : ""}</div>`;
  const kaydet = async () => {
    const mulakat = Object.fromEntries(new FormData($("#mulakatForm")));
    D.proje = await api(`/api/projeler/${D.proje.id}`, "PUT", { mulakat });
  };
  $("#mulakatForm").onsubmit = async (ev) => {
    ev.preventDefault();
    try { await kaydet(); bildir("Mülakat kaydedildi"); mulakatCiz(); } catch (err) { bildir(err.message, true); }
  };
  $("#analizBtn").onclick = async () => {
    if (!yzGerekli()) return;
    const b = $("#analizBtn"); b.disabled = true; b.textContent = "Analiz ediliyor (30–90 sn)…";
    try {
      await kaydet();
      D.proje = await api(`/api/projeler/${D.proje.id}/yz-analiz`, "POST", {});
      mulakatCiz();
      $("#analizKutu").scrollIntoView({ behavior: "smooth" });
    } catch (err) { bildir(err.message, true); b.disabled = false; b.textContent = "Kaydet ve yapay zekâ ile analiz et"; }
  };
  analizButonlari();
}

function analizHtml(a) {
  const liste = (x) => (x || []).length ? `<ul>${x.map((i) => `<li>${e(i)}</li>`).join("")}</ul>` : `<p class="k">—</p>`;
  const etiketler = (x) => (x || []).map((i) => `<span class="etiket">${e(i)}</span>`).join(" ") || "—";
  return `<div class="kart analiz">
    <div class="baslik"><div><h2>Yapay zekâ analizi</h2><div class="k">${trTarih(a.tarih)}</div></div>
      <div class="satir"><button class="btn birincil" id="uygulaBtn">Projeye uygula</button></div></div>
    <p>${e(a.ozet)}</p>
    <h3>İdeal müşteri</h3><p>${e(a.ideal_musteri)}</p>
    <div class="iki">
      <div><h3>Hedef sektörler</h3><div class="yatay">${etiketler(a.hedef_sektorler)}</div>
        <h3>Hedef şehirler</h3><div class="yatay">${etiketler(a.hedef_sehirler)}</div></div>
      <div><h3>Karar vericiler</h3><div class="yatay">${etiketler(a.hedef_unvanlar)}</div>
        <h3>Firma büyüklüğü</h3><div class="yatay">${etiketler((a.hedef_buyuklukler || []).map((k) => D.ayar.buyuklukler[k] || k))}</div></div>
    </div>
    <h3>Satın alma sinyalleri (müşteri ihtiyacını fark etmeden önce)</h3>
    <div class="tablo-kap"><table class="tablo"><thead><tr><th>Sinyal</th><th>Ağırlık</th><th>Yarı ömür</th><th>Nasıl tespit edilir</th></tr></thead>
      <tbody>${(a.sinyaller || []).map((s) => `<tr><td><b>${e(s.ad)}</b><div class="k">${e(s.kod)}</div></td><td>${s.agirlik}</td><td>${s.yari_omur} gün</td><td>${e(s.nasil_tespit)}</td></tr>`).join("")}</tbody></table></div>
    <div class="iki">
      <div><h3>Sinyal radarı sorguları</h3>${liste(a.haber_sorgulari)}</div>
      <div><h3>Veri kaynakları</h3>${liste(a.veri_kaynaklari)}
        ${(a.osm_kategoriler || []).length ? `<h3>Haritada aranacak kategoriler</h3><div class="yatay">${etiketler(a.osm_kategoriler)}</div>` : ""}</div>
    </div>
    <h3>Mesaj açısı</h3><p>${e(a.mesaj_acisi)}</p>
    <h3>İlk temas mesajı taslağı</h3><div class="mesaj-kutu">${e(a.ilk_temas_mesaji)}</div>
    <div class="iki">
      <div><h3>Firmaya sorulacak ek sorular</h3>${liste(a.eksik_sorular)}</div>
      <div><h3>Riskler</h3>${liste(a.riskler)}</div>
    </div>
  </div>`;
}

function analizButonlari() {
  const b = $("#uygulaBtn");
  if (!b) return;
  b.onclick = async () => {
    if (!confirm("Hedefler, sinyaller ve radar sorguları analizdeki değerlerle güncellensin mi? (Mevcut sinyaller korunur, yenileri eklenir.)")) return;
    try {
      D.proje = await api(`/api/projeler/${D.proje.id}/yz-uygula`, "POST", {});
      await projeSec(D.proje.id);
      sekmeGoster("radar");
      bildir("Uygulandı. Şimdi sinyal radarını açabilirsiniz.");
    } catch (err) { bildir(err.message, true); }
  };
}

// --- Sinyal radarı -------------------------------------------------------------------
function radarCiz() {
  const t = D.proje.tarama;
  const son = D.proje.son_tarama ? new Date(D.proje.son_tarama).toLocaleString("tr-TR") : "henüz taranmadı";
  $("#sekme-radar").innerHTML = `
    <div class="kart">
      <div class="baslik"><div><h2>Sinyal radarı</h2>
        <p class="aciklama">Sorgularınız Google Haberler'de ve eklediğiniz RSS kaynaklarında düzenli taranır. Yapay zekâ her haberi
          okuyup <b>hangi şirketin, hangi sebeple</b> yakında size ihtiyaç duyabileceğini değerlendirir; eşiği geçen şirketler
          sinyal ve kaynak linkiyle otomatik olarak listeye eklenir. Böylece müşteri ihtiyacını fark etmeden ona ulaşırsınız.</p></div>
        <div class="satir"><button class="btn birincil" id="taraBtn">Şimdi tara</button></div></div>
      <div class="k" id="taramaDurum">Son tarama: ${son}</div>
    </div>
    <form class="kart" id="radarForm">
      <h2>Tarama ayarları</h2>
      <div class="izgara">
        <div class="tam-satir secenekler">
          <label><input type="checkbox" name="aktif" ${t.aktif ? "checked" : ""}> Düzenli taramayı aç</label>
          <label><input type="checkbox" name="yz_kullan" ${t.yz_kullan ? "checked" : ""}> Haberleri yapay zekâ değerlendirsin</label>
        </div>
        <label>Tarama sıklığı (saat)<input type="number" name="aralik_saat" min="1" value="${t.aralik_saat}"></label>
        <label>Otomatik listeye ekleme eşiği (0–100)<input type="number" name="otomatik_lead_esik" min="0" max="101" value="${t.otomatik_lead_esik}"></label>
        <label class="tam-satir">Haber sorguları (her satıra bir sorgu)
          <textarea name="sorgular" rows="7" placeholder="${e(otomatikSorguIpucu())}">${e((t.sorgular || []).join("\n"))}</textarea>
          <span class="k">Boş bırakılırsa sinyal adları ve hedef sektörlerden otomatik üretilir. En iyi sorgular Mülakat → yapay zekâ analizinden gelir.</span></label>
        <label class="tam-satir">Ek RSS kaynakları (her satıra bir adres, isteğe bağlı)
          <textarea name="rss" rows="3" placeholder="ör. sektör dergisi, ticaret odası duyuruları, gazete ekonomi RSS adresi">${e((t.rss || []).join("\n"))}</textarea></label>
      </div>
      <p class="k">Düzenli tarama, uygulama açık olduğu sürece arka planda çalışır.</p>
      <div class="satir" style="justify-content:flex-end"><button class="btn" type="submit">Ayarları kaydet</button></div>
    </form>
    <div class="kart">
      <div class="baslik"><h2>Bulunan haberler</h2>
        <div class="satir">${[["ilgili", "Fırsatlar"], ["lead", "Listeye eklenenler"], ["incelenmemis", "İncelenmemiş"], ["", "Tümü"]]
          .map(([k, v]) => `<button class="btn kucuk ${D.radarFiltre === k ? "birincil" : ""}" data-filtre="${k}">${v}</button>`).join("")}</div></div>
      <div id="haberListesi"><p class="k">Yükleniyor…</p></div>
    </div>`;
  $$("#sekme-radar [data-filtre]").forEach((b) => (b.onclick = () => { D.radarFiltre = b.dataset.filtre; radarCiz(); }));
  $("#radarForm").onsubmit = async (ev) => {
    ev.preventDefault();
    const f = new FormData(ev.target);
    const satirlar = (k) => String(f.get(k) || "").split("\n").map((x) => x.trim()).filter(Boolean);
    const tarama = { ...t, aktif: !!f.get("aktif"), yz_kullan: !!f.get("yz_kullan"), aralik_saat: Number(f.get("aralik_saat")) || 12,
      otomatik_lead_esik: Number(f.get("otomatik_lead_esik")) || 70, sorgular: satirlar("sorgular"), rss: satirlar("rss") };
    try { D.proje = await api(`/api/projeler/${D.proje.id}`, "PUT", { tarama }); bildir("Kaydedildi"); radarCiz(); }
    catch (err) { bildir(err.message, true); }
  };
  $("#taraBtn").onclick = taramaBaslat;
  haberleriYukle();
  taramaDurumIzle();
}

function otomatikSorguIpucu() {
  const sek = (D.proje.hedef_sektorler || [])[0] || "";
  return D.proje.sinyaller.slice(0, 3).map((s) => `${sek} ${s.ad}`.trim()).join("\n");
}

async function haberleriYukle() {
  const pid = D.proje.id;
  const h = await api(`/api/projeler/${pid}/haberler?filtre=${D.radarFiltre ?? "ilgili"}`);
  const kutu = $("#haberListesi");
  if (!kutu || D.proje.id !== pid) return;
  kutu.innerHTML = h.length ? h.map(haberSatiri).join("") : `<p class="aciklama">Bu filtrede haber yok.</p>`;
  haberButonlari(kutu, h);
}

function haberSatiri(h) {
  const puan = h.uygunluk ?? "–";
  const renk = h.uygunluk >= 70 ? "var(--a)" : h.uygunluk >= 40 ? "var(--b)" : "var(--soluk)";
  return `<div class="haber" data-hid="${h.id}">
    <div class="puan-kutu" style="color:${renk}">${puan}<small>uygunluk</small></div>
    <div><a href="${e(h.link)}" target="_blank" rel="noopener">${e(h.baslik)}</a>
      <div class="k">${e(h.kaynak)} · ${trTarih(h.tarih)}${h.sorgu ? ` · sorgu: ${e(h.sorgu)}` : ""}</div>
      ${h.sirket ? `<div style="margin-top:4px"><b>${e(h.sirket)}</b> ${h.sinyal ? `<span class="etiket">${e(sinyalAdi(h.sinyal))}</span>` : ""}
        ${h.sehir ? `<span class="k">${e(h.sehir)}</span>` : ""}</div>` : ""}
      ${h.neden ? `<div class="k">${e(h.neden)}</div>` : ""}
      ${h.yaklasim ? `<div class="k"><b>Yaklaşım:</b> ${e(h.yaklasim)}</div>` : ""}</div>
    <div class="yatay">${h.lead_id ? `<button class="btn kucuk" data-ac="${h.lead_id}">Kaydı aç</button>`
      : `<button class="btn kucuk birincil" data-cevir="${h.id}">Listeye ekle</button>`}
      ${h.durum !== "ilgisiz" && !h.lead_id ? `<button class="btn kucuk" data-ilgisiz="${h.id}">İlgisiz</button>` : ""}</div>
  </div>`;
}

function haberButonlari(kutu, haberler) {
  $$("[data-ac]", kutu).forEach((b) => (b.onclick = async () => {
    if (!D.leadler.some((l) => l.id === Number(b.dataset.ac))) await leadleriYukle();
    leadModal(Number(b.dataset.ac));
  }));
  $$("[data-ilgisiz]", kutu).forEach((b) => (b.onclick = async () => {
    await api(`/api/haberler/${b.dataset.ilgisiz}`, "PUT", { durum: "ilgisiz" });
    b.closest(".haber").remove();
  }));
  $$("[data-cevir]", kutu).forEach((b) => (b.onclick = async () => {
    const h = haberler.find((x) => x.id === Number(b.dataset.cevir));
    const ad = h.sirket || prompt("Şirket adı:", "");
    if (!ad) return;
    try {
      await api(`/api/projeler/${D.proje.id}/leadler`, "POST", {
        ad, sektor: h.sektor, sehir: h.sehir, sinyal: h.sinyal, sinyal_ozet: h.baslik, sinyal_tarihi: h.tarih,
        kaynak: h.link, kaynak_turu: "haber", izin: "kurumsal", notlar: [h.neden, h.yaklasim && "Yaklaşım: " + h.yaklasim].filter(Boolean).join(" "),
      });
      await leadleriYukle();
      const yeni = D.leadler.find((l) => l.kaynak === h.link) || D.leadler.find((l) => l.ad === ad);
      if (yeni) await api(`/api/haberler/${h.id}`, "PUT", { durum: "lead", lead_id: yeni.id });
      bildir(`${ad} listeye eklendi`);
      projeSayisiniGuncelle();
      if (D.sekme === "radar") haberleriYukle();
    } catch (err) { bildir(err.message, true); }
  }));
}

async function taramaBaslat() {
  if (D.proje.tarama.yz_kullan && !D.yz?.hazir) bildir("Yapay zekâ ayarlı değil: haberler toplanacak ama şirket/sinyal çıkarılmayacak.");
  try {
    const s = await api(`/api/projeler/${D.proje.id}/tara`, "POST", {});
    if (!s.basladi) bildir(s.mesaj);
    D.radarCalisti = true; // bitince liste yenilensin (tarama ilk kontrolden önce bitse bile)
    taramaDurumIzle();
  } catch (err) { bildir(err.message, true); }
}

async function taramaDurumIzle() {
  clearTimeout(D.radarZaman);
  const pid = D.proje.id;
  const d = await api(`/api/projeler/${pid}/tarama-durum`).catch(() => null);
  const kutu = $("#taramaDurum");
  if (!d || !kutu || D.proje.id !== pid) return;
  const son = d.son_tarama ? new Date(d.son_tarama).toLocaleString("tr-TR") : "henüz taranmadı";
  kutu.innerHTML = d.calisiyor ? `<b>Taranıyor:</b> ${e(d.mesaj)}` : `Son tarama: ${son}${d.mesaj ? " · " + e(d.mesaj) : ""}`
    + (d.sonuc?.hatalar?.length ? `<div class="etiket uyari" title="${e(d.sonuc.hatalar.join("\n"))}">${d.sonuc.hatalar.length} kaynak hatası</div>` : "");
  $("#taraBtn").disabled = d.calisiyor;
  if (d.calisiyor) { D.radarCalisti = true; D.radarZaman = setTimeout(taramaDurumIzle, 2500); }
  else if (D.radarCalisti) { D.radarCalisti = false; haberleriYukle(); leadleriYukle(); projeSayisiniGuncelle(); }
}

// --- İnternette aday araştırması -------------------------------------------------------
async function ydAra(ev) {
  ev.preventDefault();
  if (!yzGerekli()) return;
  const f = Object.fromEntries(new FormData(ev.target));
  const durum = $("#ydDurum"), btn = $("#ydForm button[type=submit]");
  durum.textContent = "Claude internette araştırıyor… (1–3 dk)"; btn.disabled = true;
  try {
    const s = await api(`/api/projeler/${D.proje.id}/yz-aday`, "POST", f);
    D.ydAdaylar = s.adaylar;
    durum.textContent = `${s.adaylar.length} aday bulundu.`;
    ydCiz(s.rapor);
  } catch (err) { durum.textContent = ""; bildir(err.message, true); }
  btn.disabled = false;
}

function ydCiz(rapor) {
  const A = D.ydAdaylar || [];
  $("#ydSonuc").innerHTML = `<div class="kart">
    <div class="baslik"><h2>${A.length} aday</h2><div class="satir"><button class="btn birincil" id="ydEkle">Seçilenleri listeye ekle</button></div></div>
    <div class="tablo-kap" style="margin-top:10px"><table class="tablo"><thead><tr><th></th><th>Şirket</th><th>Sinyal</th><th>İletişim</th><th>Neden</th></tr></thead>
    <tbody>${A.map((a, i) => `<tr class="${a.mukerrer ? "soluk" : ""}"><td><input type="checkbox" data-i="${i}" ${a.mukerrer ? "" : "checked"}></td>
      <td><b>${e(a.ad)}</b>${a.mukerrer ? ' <span class="etiket">listede</span>' : ""}<div class="k">${e([a.sektor, a.sehir].filter(Boolean).join(" · "))}</div>
        ${a.web ? `<div class="k">${e(a.web)}</div>` : ""}</td>
      <td>${e(sinyalAdi(a.sinyal))}<div class="k">${e(a.sinyal_ozet)}</div><div class="k">${trTarih(a.sinyal_tarihi)}
        ${a.kaynak ? ` · <a href="${e(a.kaynak)}" target="_blank" rel="noopener">kaynak</a>` : ""}</div></td>
      <td>${e(a.telefon)}<div class="k">${e(a.eposta)}</div><div class="k">${e(a.unvan)}</div></td>
      <td class="k">${e(a.notlar)}</td></tr>`).join("")}</tbody></table></div>
    <details style="margin-top:10px"><summary class="k">Araştırma raporunun tamamı</summary><div class="mesaj-kutu">${e(rapor)}</div></details></div>`;
  $("#ydEkle").onclick = async () => {
    const secili = $$("#ydSonuc input[type=checkbox]:checked").map((c) => { const a = { ...A[c.dataset.i] }; delete a.mukerrer; return a; });
    if (!secili.length) return bildir("Seçili aday yok");
    try {
      const s = await api(`/api/projeler/${D.proje.id}/leadler`, "POST", { leadler: secili });
      bildir(`${s.eklenen} eklendi, ${s.mukerrer} zaten listedeydi.`);
      $$("#ydSonuc input[type=checkbox]:checked").forEach((c) => (A[c.dataset.i].mukerrer = true));
      ydCiz(rapor);
      await leadleriYukle(); projeSayisiniGuncelle();
    } catch (err) { bildir(err.message, true); }
  };
}

basla().catch((err) => bildir(err.message, true));
