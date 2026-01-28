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

let url = new URL("https://functions.yandexcloud.net/d4eml76h9lths80k2r9n");

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

const placeholders = {
  food: "Бутерброд\nХлеб 100г\nМасло 10г\nСыр 25г\nПорция 230г",
  symptom: "Сыпь на спине",
};

function toArticle(id) {
  menu.style.display = "none";
  backButton.style.display = "block";
  if (article) {
    article.style.display = "none";
  }
  article = document.getElementById(id);
  article.style.display = "flex";
  url.searchParams.set("table", id);

  if (id === "user") {
    read().then((user) => toUser(user));
  } else if (id === "plot") {
  } else if (article.innerHTML === "") {
    load().then((items) => toSections(items));
  }
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

function toHtml(text) {
  if (article.id === "food") {
    let { title, foods } = toJson(text);
    foods = foods
      .map(({ title, weight }) => `<p>${title} - <span>${weight}г</span></p>`)
      .join("");
    return `<h2>${title}</h2>${foods}`;
  }
  return `<h3>${text}</h3>`;
}

function toJson(text) {
  const lines = text.split("\n").map((l) => l.trim());
  return {
    title: lines[0],
    foods: lines
      .map((f) => /(.+?)[ -]+(\d+)[ грамов.]*/.exec(f))
      .filter(Boolean)
      .map((m) => ({
        title: m[1],
        weight: Math.abs(parseInt(m[2])),
      })),
  };
}

function resize() {
  if (this.offsetHeight <= this.scrollHeight) {
    this.style.height = this.scrollHeight + "px";
  }
}

function addSection() {
  const placeholder = placeholders[article.id];
  rows = placeholder.split("\n").length;
  article.insertAdjacentHTML(
    "beforeend",
    `<section>
  <textarea name="text" placeholder="${placeholder}" rows=${rows} inputmode="text"></textarea>
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
  section.innerHTML = toHtml(text);
  section.setAttribute("data-text", text);
  const created = Date.now().toString();
  section.setAttribute("data-created", created);
  create(created, text);
  section.onclick = toForm;
  addSection();
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
    section.innerHTML = toHtml(text);
    section.onclick = toForm;
  } else {
    section.classList.add("changed");
    const created = section.getAttribute("data-created");
    update(created, text)
      .then(() => {
        section.setAttribute("data-text", text);
        section.innerHTML = toHtml(text);
        section.onclick = toForm;
      })
      .finally(() => {
        section.classList.remove("changed");
      });
  }
}

async function update(created, text) {
  url.searchParams.set("action", "update");
  const to = new URL(url.href);
  to.searchParams.set("created", created);
  to.searchParams.set("text", text);
  res = await fetch(to);
  return res.ok;
}

async function create(created, text) {
  url.searchParams.set("action", "create");
  const to = new URL(url.href);
  to.searchParams.set("created", created);
  to.searchParams.set("text", text);
  res = await fetch(to);
  return res.ok;
}

async function remove(created) {
  url.searchParams.set("action", "remove");
  const to = new URL(url.href);
  to.searchParams.set("created", created);
  const res = await fetch(to);
  return res.ok;
}

async function load() {
  url.searchParams.set("action", "load");
  const res = await fetch(url);
  return res.ok ? await res.json() : [];
}

function toSections(items) {
  article.innerHTML = items
    .map(
      ({ created, text }) =>
        `<section data-created="${created}" data-text="${text}">${toHtml(text)}</section>`,
    )
    .join("");
  article.querySelectorAll("section").forEach((s) => (s.onclick = toForm));
  addSection();
}

async function write(e) {
  e.preventDefault();
  url.searchParams.set("action", "write");
  const to = new URL(url.href);

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
  url.searchParams.set("action", "read");
  const res = await fetch(url);
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
