Telegram.WebApp.ready();
Telegram.WebApp.onEvent("themeChanged", function () {
  document.documentElement.className = Telegram.WebApp.colorScheme;
});

let params = new URLSearchParams(Telegram.WebApp.initData);
let user = JSON.parse(decodeURIComponent(params.get("user")));

let hash = params.get("hash");
params.delete("hash");
let checkDataString = Array.from(params.entries())
  .sort(([a], [b]) => a.localeCompare(b))
  .map(([key, value]) => `${key}=${value}`)
  .join("\n");

const url = new URL("https://functions.yandexcloud.net/d4eml76h9lths80k2r9n");

user = { id: 164671585 };
hash = "";
checkDataString = "";

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

url.searchParams.set("user_id", user["id"]);
url.searchParams.set("hash", hash);
url.searchParams.set("checkDataString", checkDataString);

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
    .map(([name, value]) => `<p>${name} - <span>${value}</span>$</p>`)
    .join("");
  return `<h2>${name}</h2>${items}`;
};

function resize() {
  if (this.offsetHeight <= this.scrollHeight) {
    this.style.height = this.scrollHeight + "px";
  }
}

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

read().then((user) => toUser(user));

load().then((items) =>
  [0, 1].forEach((id) =>
    toSections(
      document.getElementById(id),
      items.filter((i) => i.what === id),
    ),
  ),
);

const data = {};
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
  const res = await toFetch("write", params);
  article.classList.remove("changed");
  return res.ok;
}

async function read() {
  const res = await toFetch("read");
  return res.ok ? await res.json() : {};
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

  article.lastElementChild.firstElementChild.onclick = write;
}
