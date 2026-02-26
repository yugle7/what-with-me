// ============================================================================
// Инициализация Telegram WebApp
// ============================================================================

Telegram.WebApp.ready();
Telegram.WebApp.onEvent("themeChanged", function () {
  document.documentElement.className = Telegram.WebApp.colorScheme;
});

// ============================================================================
// Настройка URL и параметров пользователя
// ============================================================================

const url = new URL("https://functions.yandexcloud.net/d4eml76h9lths80k2r9n");

// Получаем параметры из Telegram WebApp
let params = new URLSearchParams(Telegram.WebApp.initData);
let user = JSON.parse(decodeURIComponent(params.get("user")));

let hash = params.get("hash");
params.delete("hash");
let checkDataString = Array.from(params.entries())
  .sort(([a], [b]) => a.localeCompare(b))
  .map(([key, value]) => `${key}=${value}`)
  .join("\n");

// Используем данные из Telegram (или значения по умолчанию для тестирования)
user = { id: 164671585 };
hash = "";
checkDataString = "";

// Устанавливаем параметры в URL
url.searchParams.set("user_id", user["id"]);
url.searchParams.set("hash", hash);
url.searchParams.set("checkDataString", checkDataString);

// ============================================================================
// Функция для выполнения API-запросов
// ============================================================================

function toFetch(action, params = {}) {
  const to = new URL(url.href);
  to.searchParams.set("action", action);
  Object.entries(params).forEach(([key, value]) =>
    to.searchParams.set(key, value),
  );
  if (article && /^\d+$/.test(article.id)) {
    to.searchParams.set("what", article.id);
  }
  return fetch(to);
}

// ============================================================================
// Навигация по меню
// ============================================================================

const menu = document.getElementById("menu");
const articles = document.querySelectorAll("article");
const menuButtons = document.querySelectorAll("menu button");
const backButton = document.getElementById("back");

let article;

function toArticle(id) {
  menu.style.display = "none";
  backButton.style.display = "block";
  if (article) {
    article.style.display = "none";
  }
  article = document.getElementById(id);
  article.style.display = "flex";
}

function toMenu() {
  menu.style.display = "flex";
  backButton.style.display = "none";
  if (article) {
    article.style.display = "none";
  }
}

menuButtons.forEach((button) =>
  button.addEventListener("click", () => toArticle(button.getAttribute("to"))),
);

backButton.onclick = toMenu;

// ============================================================================
// Работа с текстом и формами
// ============================================================================

function setCursorToEnd(textarea) {
  textarea.focus();
  textarea.setSelectionRange(textarea.value.length, textarea.value.length);
}

function getText(textarea) {
  return textarea.value
    .toLowerCase()
    .replace(/ё/g, "е")
    .replace(/[^0-9a-zа-я\- \n.,]/g, "")
    .trim();
}

const toHtml = (item) => {
  let { name, items } = item;

  items = Object.entries(items)
    .map(([name, value]) => `<p>${name} - <span>${value}</span></p>`)
    .join("");
  return `<h2>${name}</h2>${items}`;
};

function resize() {
  if (this.offsetHeight <= this.scrollHeight) {
    this.style.height = this.scrollHeight + "px";
  }
}

// ============================================================================
// Работа с секциями и элементами
// ============================================================================

const placeholders = [
  [
    "Бутерброд",
    "Хлеб 100 гр",
    "Масло 10 г",
    "Порция 230г",
    "Тарелка 300 мл",
  ].join("\n"),
  "Сыпь на спине",
];

const data = {}; // Хранилище для данных элементов

function addSection(article) {
  const placeholder = placeholders[article.id];
  const rows = placeholder.split("\n").length;
  article.insertAdjacentHTML(
    "beforeend",
    `<section>
  <textarea name="text" placeholder="${placeholder}" rows=${rows}></textarea>
  <button type="button">Добавить</button>
</section>`,
  );
  const section = article.lastElementChild;
  section.lastElementChild.onclick = addItem;
  section.firstElementChild.addEventListener("input", resize);
}

function addItem(e) {
  e.preventDefault();
  e.stopPropagation();
  const text = getText(e.target.previousElementSibling);
  if (text === "") {
    return;
  }
  const section = article.lastElementChild;
  section.classList.add("changed");

  const created = Date.now();
  create(created, text)
    .then((item) => {
      section.innerHTML = toHtml(item);
      data[created] = { text, item };
      section.id = created;
      section.onclick = toForm;
      addSection(article);
    })
    .finally(() => section.classList.remove("changed"));
}

function toForm(e) {
  e.preventDefault();
  const section = e.currentTarget;
  section.onclick = null;

  section.innerHTML = `
<textarea name="text">${data[section.id].text}</textarea>
<div>
  <button type="button">Удалить</button>
  <button type="button">Сохранить</button>
</div>`;

  const textarea = section.firstElementChild;
  setCursorToEnd(textarea);
  textarea.style.height = textarea.scrollHeight + "px";
  textarea.addEventListener("input", resize);
  const buttons = section.lastElementChild;
  buttons.firstElementChild.onclick = removeSection;
  buttons.lastElementChild.onclick = toItem;
}

function removeSection(e) {
  e.preventDefault();
  const section = e.target.parentElement.parentElement;
  section.classList.add("changed");
  remove(section.id).then(() => section.remove());
}

function toItem(e) {
  e.preventDefault();
  e.stopPropagation();

  const section = e.target.parentElement.parentElement;
  const text = getText(section.firstElementChild);

  if (data[section.id].text === text) {
    section.innerHTML = toHtml(data[section.id].item);
    section.onclick = toForm;
  } else {
    section.classList.add("changed");
    update(section.id, text)
      .then((item) => {
        data[section.id] = { text, item };
        section.innerHTML = toHtml(item);
        section.onclick = toForm;
      })
      .finally(() => {
        section.classList.remove("changed");
      });
  }
}

// ============================================================================
// API-функции для работы с данными
// ============================================================================

async function update(created, text) {
  const res = await toFetch("update", { created, text });
  return res.ok ? await res.json() : {};
}

async function create(created, text) {
  const res = await toFetch("create", { created, text });
  return res.ok ? await res.json() : {};
}

async function remove(created) {
  const res = await toFetch("remove", { created });
  return res.ok;
}

async function read() {
  const res = await toFetch("read");
  return res.ok ? await res.json() : {};
}

async function load() {
  const res = await toFetch("load");
  const items = res.ok ? await res.json() : [];
  items.forEach(({ created, text, item }) => (data[created] = { text, item }));
  return items;
}

function toSections(article, items) {
  article.innerHTML = items
    .map(
      ({ created, item }) =>
        `<section id="${created}">${toHtml(item)}</section>`,
    )
    .join("");

  article.querySelectorAll("section").forEach((s) => (s.onclick = toForm));
  addSection(article);
}

// ============================================================================
// Функции для работы с профилем пользователя
// ============================================================================

async function write(e) {
  e.preventDefault();
  article.classList.add("changed");
  const time_zone = (article.querySelector('input[name="time_zone"]').value =
    user.time_zone || 3);
  const birthday = article.querySelector('input[name="birthday"]').value;
  const height = article.querySelector('input[name="height"]').value;
  const weight = article.querySelector('input[name="weight"]').value;
  const target_weight = article.querySelector(
    'input[name="target_weight"]',
  ).value;
  const male = article.querySelector('input[name="sex"][value="male"]').checked;
  const female = article.querySelector(
    'input[name="sex"][value="female"]',
  ).checked;
  const activity = article.querySelector('select[name="activity"]').value;

  const params = { time_zone };
  if (birthday) {
    params.birthday = asDigits(birthday);
  }
  if (height) {
    params.height = height;
  }
  if (weight) {
    params.weight = weight;
  }
  if (target_weight) {
    params.target_weight = target_weight;
  }
  if (male || female) {
    params.male = male;
  }
  params.activity = activity;
  const res = await toFetch("write", params);
  article.classList.remove("changed");
  return res.ok;
}

const asDigits = (s) => s.replaceAll("-", "");

const asString = (s) => {
  s = s.toString();
  const y = s.slice(0, 4);
  const m = s.slice(4, 6);
  const d = s.slice(6, 8);
  return `${y}-${m}-${d}`;
};

function toUser(user) {
  user.birthday = user.birthday && asString(user.birthday);
  const article = document.getElementById("user");

  article.querySelector('input[name="time_zone"]').value = user.time_zone || 3;
  article.querySelector('input[name="birthday"]').value = user.birthday || "";
  article.querySelector('input[name="height"]').value = user.height || "";
  article.querySelector('input[name="weight"]').value = user.weight || "";
  article.querySelector('input[name="target_weight"]').value =
    user.target_weight || "";

  article.querySelector('input[name="sex"][value="male"]').checked =
    user.male == true;
  article.querySelector('input[name="sex"][value="female"]').checked =
    user.male == false;

  if (user.activity) {
    article.querySelector('select[name="activity"]').value = user.activity;
  }

  article.lastElementChild.firstElementChild.onclick = write;
}

// ============================================================================
// Графики и визуализация данных
// ============================================================================

// Ссылки на DOM-элементы для графиков
const paths = document.getElementById("paths");
const dates = document.getElementById("dates");
const names = document.getElementById("names");
const links = document.getElementById("links");

// Цвета и метки для данных
const colors = {};
const labels = {};
let normas;

// Параметры отображения графиков
const dh = 2;
const sh = 100 - 2 * dh;
const days = 7;

// Вычисление диапазона дат
const maxDate = new Date();
const minDate = new Date(maxDate);
minDate.setDate(minDate.getDate() - days);
minDate.setHours(0, 0, 0, 0);
maxDate.setHours(0, 0, 0, 0);

// Данные о питательных веществах и их цветах
const nutrientsData = {
  nutrients: {
    energy: "#00FFFF",
    fat: "#CCFF00",
    carbohydrate: "#FF00FF",
    protein: "#00FF00",
  },
};

// Хеш-функция для создания уникальных идентификаторов
const toHash = (i) => {
  let h = 2166136261;
  for (let j = 0; j < i.length; j++) {
    h ^= i.charCodeAt(j);
    h *= 16777619;
  }
  return String(h >>> 0);
};

// Инициализация цветов и меток
for (const key in nutrientsData) {
  for (const label in nutrientsData[key]) {
    const color = nutrientsData[key][label];
    const hash = toHash(`${key} ${label}`);
    colors[hash] = color;
    labels[hash] = label;
  }
}

// Переменные для хранения данных графиков
let hists = {};
let lines = {};
let selected = null;
const displayed = [];

// ============================================================================
// Вспомогательные функции для дат
// ============================================================================

// Добавление кнопок с датами
const addDates = () => {
  const buttons = [];
  const d = new Date(minDate);
  for (let i = 0; i <= days; i++) {
    buttons.push(`<button>${d.getDate()}</button>`);
    d.setDate(d.getDate() + 1);
  }
  dates.innerHTML = buttons.join("\n");
};

// ============================================================================
// Функции для работы с осями и линиями
// ============================================================================

// Добавление горизонтальной оси
function addAxis() {
  const norm = document.createElementNS("http://www.w3.org/2000/svg", "line");
  const y = dh + (2 * sh) / 3;
  norm.setAttribute("x1", 0);
  norm.setAttribute("y1", y);
  norm.setAttribute("x2", 100);
  norm.setAttribute("y2", y);
  norm.setAttribute("stroke-width", "1");
  paths.appendChild(norm);
}

// ============================================================================
// Функции для отображения ссылок/кнопок выбора данных
// ============================================================================

const addLinks = (hashes) => {
  const dst = [];
  for (const key in nutrientsData) {
    const buttons = [];
    for (const label in nutrientsData[key]) {
      const hash = toHash(`${key} ${label}`);
      if (hashes.indexOf(hash) >= 0) {
        const color = nutrientsData[key][label];
        buttons.push(
          `<button data-hash=${hash} style="--color: ${color}">${label}</button>`,
        );
      }
    }
    if (buttons.length) {
      dst.push(`<div>${buttons.join("\n")}</div>`);
    }
  }
  links.innerHTML = dst.join("\n");

  links.querySelectorAll("button").forEach((b) => {
    b.addEventListener("click", (e) => display(e.currentTarget));
  });
};

// ============================================================================
// Функции для расчёта координат и сглаживания
// ============================================================================

// Преобразование значения Y в координату
function getY(y) {
  if (y <= 0) return 0;
  if (y <= 2) return y / 3;
  return 1 - 2 / y / 3;
}

// Сглаживание линии (catmull-rom spline)
function smooth(points) {
  if (points.length < 2) return "";
  if (points.length === 2) {
    return `M ${points[0].x},${points[0].y} L ${points[1].x},${points[1].y}`;
  }

  let d = `M ${points[0].x},${points[0].y}`;

  for (let i = 0; i < points.length - 1; i++) {
    const p1 = points[i];
    const p2 = points[i + 1];

    if (p2.y < 100 - dh || p1.y < 100 - dh) {
      const p0 = points[Math.max(0, i - 1)];
      const p3 = points[Math.min(points.length - 1, i + 2)];

      const cp1x = p1.x + (p2.x - p0.x) / 6;
      const cp1y = p1.y + (p2.y - p0.y) / 6;
      const cp2x = p2.x - (p3.x - p1.x) / 6;
      const cp2y = p2.y - (p3.y - p1.y) / 6;

      d += ` C ${cp1x},${cp1y} ${cp2x},${cp2y} ${p2.x},${p2.y}`;
    } else {
      d += ` L ${p2.x},${p2.y}`;
    }
  }

  return d;
}

// ============================================================================
// Функции для добавления гистограмм и линий на график
// ============================================================================

// Добавление гистограммы
function addHist(hists, hash) {
  const h = hists[hash];
  const n = normas[hash];
  console.log(n);

  const points = [];
  for (let x = 0; x <= days; x++) {
    const cx = dh + (x * sh) / days;
    const cy = dh + (1 - getY(h[x] / n)) * sh;
    points.push({ x: cx, y: cy });
  }

  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.dataset.hash = hash;
  if (selected) {
    path.style.opacity = "0.5";
  }

  path.setAttribute("d", smooth(points));
  path.setAttribute("fill", "none");
  path.setAttribute("stroke", colors[hash]);
  path.setAttribute("stroke-width", "3");
  path.setAttribute("vector-effect", "non-scaling-stroke");
  path.setAttribute("stroke-linejoin", "round");
  path.setAttribute("stroke-linecap", "round");
  paths.appendChild(path);

  const name = document.createElement("button");
  name.style.setProperty("--color", colors[hash]);
  name.dataset.hash = hash;
  name.textContent = labels[hash];

  name.addEventListener("click", () => fade(hash));
  names.appendChild(name);
}

// Добавление линии
function addLine(lines, hash) {
  const l = lines[hash];
  const n = normas[hash];

  const points = [];
  for (let x = 0; x <= days; x++) {
    const cx = dh + (x * (100 - 2 * dh)) / days;
    let y = 0;
    if (l.length === 1) {
      y = l[0].y;
    } else {
      for (let j = 0; j < l.length - 1; j++) {
        if (x >= l[j].x && x <= l[j + 1].x) {
          const t = (x - l[j].x) / (l[j + 1].x - l[j].x);
          y = l[j].y + t * (l[j + 1].y - l[j].y);
          break;
        }
      }
    }
    const cy = dh + (1 - getY(y / n)) * (100 - 2 * dh);
    points.push({ x: cx, y: cy });
  }

  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  if (selected) {
    path.style.opacity = "0.5";
  }
  path.setAttribute("d", smooth(points));
  path.setAttribute("fill", "none");
  path.setAttribute("stroke", colors[hash]);
  path.setAttribute("stroke-width", "3");
  path.setAttribute("vector-effect", "non-scaling-stroke");
  path.setAttribute("stroke-linejoin", "round");
  path.setAttribute("stroke-linecap", "round");
  paths.appendChild(path);

  const name = document.createElement("button");
  name.style.setProperty("--color", colors[hash]);
  name.dataset.hash = hash;
  name.textContent = labels[hash];

  name.addEventListener("click", () => fade(hash));
  names.appendChild(name);
}

// ============================================================================
// Функции управления видимостью и выделением
// ============================================================================

// Выделение/снятие выделения с графика
function fade(hash) {
  selected = selected == hash ? null : hash;
  let p;
  paths.querySelectorAll("path").forEach((path) => {
    path.style.opacity =
      selected && path.dataset.hash !== selected ? "0.5" : "1";
    if (selected && path.dataset.hash === selected) {
      p = path;
    }
  });
  p && paths.appendChild(p);
  names.querySelectorAll("button").forEach((name) => {
    name.style.opacity =
      selected && name.dataset.hash !== selected ? "0.5" : "1";
  });
}

// Отображение/скрытие графика по клику на ссылку
function display(link) {
  if (!link) return;
  const hash = link.dataset.hash;
  var i = displayed.indexOf(hash);
  if (i === -1) {
    link.style.opacity = "0.5";
    displayed.push(hash);
    if (lines[hash]) {
      addLine(lines, hash);
    } else if (hists[hash]) {
      addHist(hists, hash);
    }
  } else {
    link.style.opacity = "1";
    displayed.splice(i, 1);
    const path = paths.querySelector(`[data-hash="${hash}"]`);
    if (hash === selected) {
      fade(null);
    }
    paths.removeChild(path);
    const name = names.querySelector(`[data-hash="${hash}"]`);
    if (name) {
      names.removeChild(name);
    }
  }
}

// ============================================================================
// Функции для работы с данными
// ============================================================================

// Получение количества дней от минимальной даты
function getDays(when) {
  const ms = new Date(when * 1000) - minDate;
  return ms / (1000 * 60 * 60 * 24);
}

// Получение суточных норм пользователя
function getNormas(user) {
  const age =
    (new Date().getTime() - new Date(user.birthday).getTime()) / 31536000000;
  console.log(age);
  console.log(user);
  user.activity = 1.2;

  const bmr =
    10 * user.weight + 6.25 * user.height - 5 * age + (user.sex ? 5 : -161);
  const calories = bmr * user.activity;

  const dst = {};
  dst[toHash("nutrients energy")] = calories;
  dst[toHash("nutrients protein")] = calories * 0.14;
  dst[toHash("nutrients fat")] = calories * 0.3;
  dst[toHash("nutrients carbohydrate")] = calories * 0.56;
  return dst;
}

// Обработка данных симптомов в линии
function getLines(items) {
  const lines = {};
  items.forEach((item) => {
    const x = getDays(item.when);
    if (x >= 0 && x <= days) {
      ["symptoms"].forEach((key) => {
        if (key in item) {
          Object.entries(item[key]).forEach((label, y) => {
            const hash = toHash(`${key} ${label}`);
            if (!lines[hash]) {
              lines[hash] = [];
            }
            lines[hash].push({ x, y });
          });
        }
      });
    }
  });
  return lines;
}

// Обработка данных питания в гистограммы
function getHists(items) {
  const hists = {};

  items.forEach((item) => {
    const x = Math.round(getDays(item.when));

    if (x >= 0 && x <= days) {
      ["nutrients", "vitamins", "minerals"].forEach((key, j) => {
        if (key in item) {
          Object.entries(item[key]).forEach(([label, y]) => {
            const hash = toHash(`${key} ${label}`);
            if (!hists[hash]) {
              hists[hash] = Array(days + 1).fill(0);
            }
            hists[hash][x] += y;
          });
        }
      });
    }
  });
  return hists;
}

// ============================================================================
// Загрузка и отображение данных
// ============================================================================

// Асинхронная функция получения данных
async function take() {
  const res = await toFetch("take");
  return res.ok ? await res.json() : [];
}

function toPlot(user, items) {
  normas = getNormas(user);
  console.log(normas);

  addDates();
  addAxis();
  hists = getHists(items);
  lines = getLines(items);
  const hashes = Object.keys(hists).concat(Object.keys(lines));
  addLinks(hashes);
  ["nutrients energy"].forEach((k) =>
    display(links.querySelector(`[data-hash="${toHash(k)}"]`)),
  );
}

// ============================================================================
// Инициализация данных пользователя и меню
// ============================================================================

load().then((items) =>
  [0, 1].forEach((id) =>
    toSections(
      document.getElementById(id),
      items.filter((i) => i.what === id),
    ),
  ),
);

Promise.all([read(), take()]).then(([user, items]) => {
  toUser(user);
  toPlot(user, items);
});
