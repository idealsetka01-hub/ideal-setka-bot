// IDEAL SETKA Mini App
const tg = window.Telegram?.WebApp;
if (tg) { tg.ready(); tg.expand(); }

const content = document.getElementById("content");
const pageTitle = document.getElementById("pageTitle");
const backBtn = document.getElementById("backBtn");
const cartBtn = document.getElementById("cartBtn");
const cartCount = document.getElementById("cartCount");

let cart = []; // [{product_id, desc, size, price, unit, qty}]
let navStack = []; // ekranlar tarixi ["categories", "products:<id>:<name>", "cart", "checkout"]
let categoriesCache = [];
let currentProducts = [];

function tgUser() {
  return tg?.initDataUnsafe?.user || null;
}

function fmtPrice(n) {
  if (n === null || n === undefined) return "aniqlanmagan";
  return n.toLocaleString("ru-RU").replace(/,/g, " ") + " so‘m";
}

function updateCartBadge() {
  const total = cart.reduce((s, i) => s + i.qty, 0);
  cartCount.textContent = total;
}

function go(screen) {
  navStack.push(screen);
  render(screen);
}

function goBack() {
  navStack.pop();
  const prev = navStack.pop() || "categories";
  go(prev);
}

backBtn.onclick = () => goBack();
cartBtn.onclick = () => go("cart");

async function api(path, options) {
  const res = await fetch(path, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Xatolik yuz berdi" }));
    throw new Error(err.detail || "Xatolik yuz berdi");
  }
  return res.json();
}

async function checkAvailability() {
  const s = await api("/api/settings");
  if (s.technical_mode) {
    content.innerHTML = `<div class="state-msg">🔧 TEXNIK ISHLAR OLIB BORILMOQDA<br><br>Hozirda botimiz va Mini App’da texnik sozlash ishlari olib borilmoqda.<br><br>⏳ Iltimos, birozdan so‘ng qayta urinib ko‘ring.</div>`;
    return false;
  }
  if (!s.webapp_enabled) {
    content.innerHTML = `<div class="state-msg">🔧 Mini App vaqtincha o‘chirilgan.<br><br>Iltimos, botdagi kategoriyalar orqali buyurtma bering.</div>`;
    return false;
  }
  return true;
}

async function loadCategories() {
  categoriesCache = await api("/api/categories");
}

async function render(screen) {
  backBtn.hidden = navStack.length <= 1;

  if (screen === "categories") {
    pageTitle.textContent = "IDEAL SETKA";
    await loadCategories();
    content.innerHTML = document.getElementById("tpl-categories").innerHTML;
    const grid = document.getElementById("categoryGrid");
    grid.innerHTML = categoriesCache.map(c => `
      <button class="category-card" data-id="${c.id}" data-name="${c.name}">
        <img src="${c.image_url || ''}" onerror="this.style.visibility='hidden'">
        <span class="name">${c.name}</span>
      </button>`).join("");
    grid.querySelectorAll(".category-card").forEach(btn => {
      btn.onclick = () => go(`products:${btn.dataset.id}:${btn.dataset.name}`);
    });
    return;
  }

  if (screen.startsWith("products:")) {
    const [, catId, catName] = screen.split(":");
    pageTitle.textContent = catName;
    currentProducts = await api(`/api/products/${catId}`);
    content.innerHTML = document.getElementById("tpl-products").innerHTML;
    const list = document.getElementById("productList");
    if (!currentProducts.length) {
      list.innerHTML = `<div class="state-msg">Hozircha mahsulot mavjud emas.</div>`;
      return;
    }
    list.innerHTML = currentProducts.map(p => `
      <div class="product-card" data-id="${p.id}">
        <div class="desc">${p.desc}</div>
        <div class="meta">${p.is_eco_roll ? "📏 Standart: 10 metr / 1 rulon" : `Birlik: ${p.unit}`}</div>
        <div class="price">${p.price_text}</div>
        <div class="qty-row">
          ${p.is_eco_roll ? "" : `
            <button class="minus">−</button>
            <input type="text" class="qtyInput" value="1" inputmode="numeric">
            <button class="plus">+</button>
          `}
          <button class="add-btn">Savatga qo‘shish</button>
        </div>
      </div>`).join("");

    list.querySelectorAll(".product-card").forEach(card => {
      const id = parseInt(card.dataset.id);
      const product = currentProducts.find(p => p.id === id);
      const qtyInput = card.querySelector(".qtyInput");
      card.querySelector(".minus")?.addEventListener("click", () => {
        let v = parseInt(qtyInput.value) || 1;
        qtyInput.value = Math.max(1, v - 1);
      });
      card.querySelector(".plus")?.addEventListener("click", () => {
        let v = parseInt(qtyInput.value) || 1;
        qtyInput.value = v + 1;
      });
      card.querySelector(".add-btn").addEventListener("click", () => {
        let qty = 1;
        if (qtyInput) {
          const raw = qtyInput.value.trim();
          if (!/^[0-9]+$/.test(raw) || parseInt(raw) <= 0) {
            tg?.showAlert ? tg.showAlert("Faqat butun son kiriting (masalan: 1, 2, 5, 10)") : alert("Faqat butun son kiriting");
            return;
          }
          qty = parseInt(raw);
        }
        addToCart(product, qty);
        tg?.HapticFeedback?.notificationOccurred("success");
      });
    });
    return;
  }

  if (screen === "cart") {
    pageTitle.textContent = "Savat";
    content.innerHTML = document.getElementById("tpl-cart").innerHTML;
    const list = document.getElementById("cartList");
    if (!cart.length) {
      list.innerHTML = `<div class="state-msg">Savat bo‘sh.</div>`;
      document.getElementById("checkoutBtn").hidden = true;
      document.getElementById("cartTotal").textContent = "";
      return;
    }
    list.innerHTML = cart.map((item, idx) => `
      <div class="cart-item">
        <div class="info">
          <div>${item.desc}</div>
          <div class="sub">${item.qty} ${item.unit} × ${fmtPrice(item.price)}</div>
        </div>
        <button class="remove-btn" data-idx="${idx}">✕</button>
      </div>`).join("");
    list.querySelectorAll(".remove-btn").forEach(btn => {
      btn.onclick = () => {
        cart.splice(parseInt(btn.dataset.idx), 1);
        updateCartBadge();
        render("cart");
      };
    });
    const total = cart.reduce((s, i) => s + (i.price || 0) * i.qty, 0);
    document.getElementById("cartTotal").textContent = `Jami: ${fmtPrice(total)}`;
    document.getElementById("checkoutBtn").onclick = () => go("checkout");
    return;
  }

  if (screen === "checkout") {
    pageTitle.textContent = "Buyurtma";
    content.innerHTML = document.getElementById("tpl-checkout").innerHTML;
    const form = document.getElementById("checkoutForm");
    const user = tgUser();
    if (user?.first_name) document.getElementById("fullName").value = [user.first_name, user.last_name].filter(Boolean).join(" ");
    form.onsubmit = async (e) => {
      e.preventDefault();
      await submitOrder(form);
    };
    return;
  }
}

function addToCart(product, qty) {
  const existing = cart.find(i => i.product_id === product.id);
  if (existing) {
    existing.qty += qty;
  } else {
    cart.push({
      product_id: product.id, desc: product.desc, size: product.size,
      price: product.price, unit: product.unit, qty,
    });
  }
  updateCartBadge();
}

async function submitOrder(form) {
  const user = tgUser();
  if (!user?.id) {
    tg?.showAlert ? tg.showAlert("Foydalanuvchi aniqlanmadi. Iltimos, Mini App'ni Telegram ichidan oching.") : alert("Foydalanuvchi aniqlanmadi.");
    return;
  }
  const payment_method = form.querySelector('input[name="pay"]:checked').value;
  const payload = {
    telegram_id: user.id,
    username: user.username || null,
    full_name: document.getElementById("fullName").value.trim(),
    phone: document.getElementById("phone").value.trim(),
    address: document.getElementById("address").value.trim(),
    payment_method,
    items: cart.map(i => ({ product_id: i.product_id, qty: i.qty })),
  };

  try {
    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = "Yuborilmoqda...";
    const result = await api("/api/order", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    cart = [];
    updateCartBadge();
    showSuccess(result);
  } catch (err) {
    tg?.showAlert ? tg.showAlert(err.message) : alert(err.message);
    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.disabled = false;
    submitBtn.textContent = "Buyurtmani tasdiqlash";
  }
}

function showSuccess(result) {
  pageTitle.textContent = "Tayyor";
  backBtn.hidden = true;
  content.innerHTML = document.getElementById("tpl-success").innerHTML;
  const text = result.needs_receipt
    ? `Buyurtmangiz qabul qilindi!<br><br>🆔 #${result.order_code}<br>🧾 Jami: ${fmtPrice(result.total)}<br><br>Iltimos, botga qaytib to‘lov chekini rasm shaklida yuboring.`
    : `Buyurtmangiz qabul qilindi!<br><br>🆔 #${result.order_code}<br>🧾 Jami: ${fmtPrice(result.total)}<br><br>Tez orada operatorlarimiz siz bilan bog‘lanishadi.`;
  document.getElementById("successText").innerHTML = text;
  document.getElementById("backToBotBtn").onclick = () => tg?.close ? tg.close() : go("categories");
}

(async function init() {
  updateCartBadge();
  const ok = await checkAvailability();
  if (!ok) return;
  go("categories");
})();
