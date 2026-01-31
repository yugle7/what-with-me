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
  url.searchParams.set("what", id);
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

const toHtml = (item) => {
  let { name, items } = item;
  items = items
    .map(
      ({ name, value, unit }) =>
        `<p>${name} - <span>${value} ${unit}</span></p>`,
    )
    .join("");
  return `<h2>${name}</h2>${items}`;
};

function resize() {
  if (this.offsetHeight <= this.scrollHeight) {
    this.style.height = this.scrollHeight + "px";
  }
}

const whats = {
  food: {
    placeholder: [
      "Бутерброд",
      "Хлеб 100 гр",
      "Масло 10 г",
      "Порция 230г",
      "Тарелка 300 мл",
    ].join("\n"),
  },
  symptom: {
    placeholder: "Сыпь на спине",
  },
};

function addSection(article) {
  const placeholder = whats[article.id].placeholder;
  rows = placeholder.split("\n").length;
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
  const text = e.target.previousElementSibling.value.trim();
  if (text === "") {
    return;
  }
  const section = article.lastElementChild;
  section.classList.add("changed");

  const created = Date.now();
  create(created, text)
    .then((item) => {
      section.innerHTML = toHtml(item);
      section.setAttribute("data-text", text);
      section.setAttribute("data-item", JSON.stringify(item));
      section.setAttribute("data-created", created);
      section.onclick = toForm;
      addSection(article);
    })
    .finally(() => section.classList.remove("changed"));
}

function toForm(e) {
  e.preventDefault();
  const section = e.currentTarget;
  section.onclick = null;

  const text = section.getAttribute("data-text");
  section.innerHTML = `
<textarea name="text">${text}</textarea>
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
  const created = section.getAttribute("data-created");
  remove(created).then(() => section.remove());
}

function toItem(e) {
  e.preventDefault();
  e.stopPropagation();

  const section = e.target.parentElement.parentElement;
  const text = section.firstElementChild.value;

  if (section.getAttribute("data-text") === text) {
    const item = JSON.parse(section.getAttribute("data-item"));
    section.innerHTML = toHtml(item);
    section.onclick = toForm;
  } else {
    section.classList.add("changed");
    const created = section.getAttribute("data-created");
    update(created, text)
      .then((item) => {
        section.setAttribute("data-text", text);
        section.setAttribute("data-item", JSON.stringify(item));
        section.innerHTML = toHtml(item);
        section.onclick = toForm;
      })
      .finally(() => {
        section.classList.remove("changed");
      });
  }
}

async function update(created, text) {
  const to = new URL(url.href);
  to.searchParams.set("action", "update");
  to.searchParams.set("created", created);
  to.searchParams.set("text", text);
  res = await fetch(to);
  return res.ok;
}

async function create(created, text) {
  const to = new URL(url.href);
  to.searchParams.set("action", "create");
  to.searchParams.set("created", created);
  to.searchParams.set("text", text);
  res = await fetch(to);
  return res.ok;
}

async function remove(created) {
  const to = new URL(url.href);
  to.searchParams.set("action", "remove");
  to.searchParams.set("created", created);
  const res = await fetch(to);
  return res.ok;
}

read().then((user) => toUser(user));

load().then((items) =>
  Object.keys(whats).forEach((id) =>
    toSections(
      document.getElementById(id),
      items.filter((i) => i.what.slice(2, -1) === id),
    ),
  ),
);

async function load() {
  const to = new URL(url.href);
  to.searchParams.set("action", "load");
  const res = await fetch(to);
  return res.ok ? await res.json() : [];
}

function toSections(article, items) {
  article.innerHTML = items
    .map(
      ({ created, text }) =>
        `<section data-created="${created}" data-text="${text}">${toHtml(text)}</section>`,
    )
    .join("");
  article.querySelectorAll("section").forEach((s) => (s.onclick = toForm));
  addSection(article);
}

async function write(e) {
  e.preventDefault();
  const to = new URL(url.href);
  to.searchParams.set("action", "write");

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

  to.searchParams.set("time_zone", time_zone);
  if (birthday) {
    to.searchParams.set("birthday", asDigits(birthday));
  }
  if (height) {
    to.searchParams.set("height", height);
  }
  if (weight) {
    to.searchParams.set("weight", weight);
  }
  if (target_weight) {
    to.searchParams.set("target_weight", target_weight);
  }
  if (male || female) {
    to.searchParams.set("male", male);
  }
  const res = await fetch(to);
  return res.ok;
}

async function read() {
  const to = new URL(url.href);
  to.searchParams.set("action", "read");
  const res = await fetch(to);
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
  article = document.getElementById("user");

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
