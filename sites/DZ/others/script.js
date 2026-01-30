// 1. Счетчик
let count = 0;

function increment() {
  count = count + 1;
  document.getElementById('counter').textContent = count;
}

function decrement() {
  count = count - 1;
  document.getElementById('counter').textContent = count;
}

function reset() {
  count = 0;
  document.getElementById('counter').textContent = count;
}

// 2. Список задач
function addTask() {
  // Получаем текст из поля ввода
  const input = document.getElementById('taskInput');
  const text = input.value;

  // Проверяем, что поле не пустое
  if (text === '') {
    alert('Введите текст задачи!');
    return;
  }

  // Создаем новый элемент списка
  const list = document.getElementById('taskList');
  const newItem = document.createElement('li');
  newItem.textContent = text;

  // Добавляем в список
  list.appendChild(newItem);

  // Очищаем поле ввода
  input.value = '';
}

// 3. Смена цвета
const colors = ['lightblue', 'lightgreen', 'lightyellow', 'lightpink'];
let colorIndex = 0;

function changeColor() {
  const section = document.getElementById('colorSection');
  section.style.backgroundColor = colors[colorIndex];

  colorIndex = colorIndex + 1;
  if (colorIndex >= colors.length) {
    colorIndex = 0;
  }
}
