import { createCalculator } from './calculator.js';

const calc = createCalculator();

const keys = document.getElementById('keys');
const displayEl = document.getElementById('display');
const expressionEl = document.getElementById('expression');
const operatorButtons = Array.from(keys.querySelectorAll('[data-operator]'));

const OPERATORS = ['+', '-', '*', '/'];
const ACTIONS = new Set(['clear', 'backspace', 'toggleSign', 'percent', 'inputDecimal', 'equals']);

function pendingOperator(expression) {
  const trimmed = expression.trim();
  const last = trimmed.slice(-1);
  return OPERATORS.includes(last) ? last : null;
}

function render() {
  const display = calc.getDisplay();
  const expression = calc.getExpression();

  displayEl.textContent = display;
  displayEl.classList.toggle('long', display.length > 10 && display.length <= 14);
  displayEl.classList.toggle('very-long', display.length > 14);
  expressionEl.textContent = expression;

  const pending = pendingOperator(expression);
  for (const btn of operatorButtons) {
    btn.setAttribute('aria-pressed', String(btn.dataset.operator === pending));
  }
}

function runAction(action) {
  if (ACTIONS.has(action)) calc[action]();
}

keys.addEventListener('click', (event) => {
  const btn = event.target.closest('button');
  if (!btn || !keys.contains(btn)) return;

  if (btn.dataset.digit !== undefined) {
    calc.inputDigit(btn.dataset.digit);
  } else if (btn.dataset.operator !== undefined) {
    calc.setOperator(btn.dataset.operator);
  } else if (btn.dataset.action !== undefined) {
    runAction(btn.dataset.action);
  } else {
    return;
  }
  render();
});

document.addEventListener('keydown', (event) => {
  if (event.ctrlKey || event.metaKey || event.altKey) return;
  const { key } = event;
  let handled = true;

  if (key >= '0' && key <= '9' && key.length === 1) {
    calc.inputDigit(key);
  } else if (OPERATORS.includes(key)) {
    calc.setOperator(key);
  } else if (key === '.') {
    calc.inputDecimal();
  } else if (key === 'Enter' || key === '=') {
    calc.equals();
  } else if (key === 'Backspace') {
    calc.backspace();
  } else if (key === 'Escape') {
    calc.clear();
  } else if (key === '%') {
    calc.percent();
  } else {
    handled = false;
  }

  if (handled) {
    event.preventDefault();
    render();
  }
});

render();
