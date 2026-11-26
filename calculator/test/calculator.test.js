import { test } from 'node:test';
import assert from 'node:assert/strict';
import { compute, formatNumber, createCalculator } from '../src/calculator.js';

// Maps key characters to calculator methods:
// digits 0-9, '.', '+', '-', '*', '/', '=', 'C' clear, 'B' backspace,
// 'S' toggleSign, '%' percent.
function press(calc, keys) {
  for (const ch of keys) {
    if (ch >= '0' && ch <= '9') calc.inputDigit(ch);
    else if (ch === '.') calc.inputDecimal();
    else if (ch === '=') calc.equals();
    else if ('+-*/'.includes(ch)) calc.setOperator(ch);
    else if (ch === 'C') calc.clear();
    else if (ch === 'B') calc.backspace();
    else if (ch === 'S') calc.toggleSign();
    else if (ch === '%') calc.percent();
    else throw new Error(`test helper: unknown key '${ch}'`);
  }
  return calc;
}

function calcWith(keys) {
  return press(createCalculator(), keys);
}

// compute()

test('compute adds two numbers', () => {
  assert.equal(compute(2, '+', 3), 5);
});

test('compute subtracts the right operand from the left', () => {
  assert.equal(compute(2, '-', 5), -3);
});

test('compute multiplies two numbers', () => {
  assert.equal(compute(4, '*', 2.5), 10);
});

test('compute divides the left operand by the right', () => {
  assert.equal(compute(7, '/', 2), 3.5);
});

test('compute throws "Division by zero" when op is / and b is 0', () => {
  assert.throws(() => compute(5, '/', 0), { message: 'Division by zero' });
});

test('compute throws "Unknown operator" for an unsupported operator', () => {
  assert.throws(() => compute(1, '%', 2), { message: 'Unknown operator' });
});

// formatNumber()

test('formatNumber rounds 0.1 + 0.2 to 0.3', () => {
  assert.equal(formatNumber(0.1 + 0.2), '0.3');
});

test('formatNumber rounds 1/3 to 12 significant digits', () => {
  assert.equal(formatNumber(1 / 3), '0.333333333333');
});

test('formatNumber rounds 2/3 up at the 12th significant digit', () => {
  assert.equal(formatNumber(2 / 3), '0.666666666667');
});

test('formatNumber drops trailing zeros after the decimal point', () => {
  assert.equal(formatNumber(2.5), '2.5');
  assert.equal(formatNumber(1.1), '1.1');
});

test('formatNumber keeps zeros in the integer part', () => {
  assert.equal(formatNumber(100), '100');
});

test('formatNumber formats 0 and -0 as "0"', () => {
  assert.equal(formatNumber(0), '0');
  assert.equal(formatNumber(-0), '0');
});

test('formatNumber keeps the minus sign on negative numbers', () => {
  assert.equal(formatNumber(-3), '-3');
  assert.equal(formatNumber(-1.5), '-1.5');
});

test('formatNumber uses exponent form at 1e16 and above', () => {
  assert.equal(formatNumber(1e16), '1e+16');
  assert.equal(formatNumber(1e21), '1e+21');
});

test('formatNumber uses exponent form for non-zero values below 1e-9', () => {
  assert.equal(formatNumber(1e-10), '1e-10');
  assert.equal(formatNumber(1.5e-10), '1.5e-10');
});

test('formatNumber returns "Error" for NaN and both infinities', () => {
  assert.equal(formatNumber(NaN), 'Error');
  assert.equal(formatNumber(Infinity), 'Error');
  assert.equal(formatNumber(-Infinity), 'Error');
});

// createCalculator() basics and digit entry

test('a new calculator shows "0" with an empty expression', () => {
  const calc = createCalculator();
  assert.equal(calc.getDisplay(), '0');
  assert.equal(calc.getExpression(), '');
});

test('two calculators are independent of each other', () => {
  const a = createCalculator();
  const b = createCalculator();
  press(a, '12+');
  press(b, '7');
  assert.equal(a.getDisplay(), '12');
  assert.equal(a.getExpression(), '12 +');
  assert.equal(b.getDisplay(), '7');
  assert.equal(b.getExpression(), '');
});

test('inputDigit appends digits to build a multi-digit entry', () => {
  assert.equal(calcWith('123').getDisplay(), '123');
});

test('inputDigit replaces a leading zero', () => {
  assert.equal(calcWith('05').getDisplay(), '5');
});

test('inputDigit keeps a single zero when zero is repeated', () => {
  assert.equal(calcWith('00').getDisplay(), '0');
});

test('inputDigit ignores digits beyond the 16-digit limit', () => {
  assert.equal(calcWith('12345678901234567').getDisplay(), '1234567890123456');
});

test('inputDecimal on a fresh entry shows "0."', () => {
  assert.equal(calcWith('.').getDisplay(), '0.');
});

test('inputDecimal allows only one decimal point per entry', () => {
  assert.equal(calcWith('1.2.3').getDisplay(), '1.23');
});

// Operators and execution

test('operators execute immediately, left to right (2+3*4= gives 20)', () => {
  assert.equal(calcWith('2+3*4=').getDisplay(), '20');
});

test('pressing two operators in a row only replaces the pending operator', () => {
  assert.equal(calcWith('2+*3=').getDisplay(), '6');
});

test('pressing equals again repeats the last operation (2+3== gives 8)', () => {
  assert.equal(calcWith('2+3==').getDisplay(), '8');
});

test('equals with no pending operator leaves the display unchanged', () => {
  assert.equal(calcWith('7=').getDisplay(), '7');
});

test('operator after equals continues from the result', () => {
  assert.equal(calcWith('2+3=*2=').getDisplay(), '10');
});

test('getExpression shows the operator after equals applied to the result', () => {
  assert.equal(calcWith('2+3=*').getExpression(), '5 *');
});

test('a digit after equals starts a fresh calculation', () => {
  assert.equal(calcWith('2+3=7').getDisplay(), '7');
});

// clear, backspace, toggleSign, percent

test('clear resets the display to "0" and the expression to empty', () => {
  const calc = calcWith('12+3C');
  assert.equal(calc.getDisplay(), '0');
  assert.equal(calc.getExpression(), '');
});

test('backspace removes the last digit of the current entry', () => {
  assert.equal(calcWith('125B').getDisplay(), '12');
});

test('backspace shows "0" when the entry becomes empty or just "-"', () => {
  assert.equal(calcWith('5B').getDisplay(), '0');
  assert.equal(calcWith('5SB').getDisplay(), '0');
});

test('backspace does nothing right after equals', () => {
  assert.equal(calcWith('2+3=B').getDisplay(), '5');
});

test('backspace does nothing right after an operator', () => {
  const calc = calcWith('12+B');
  assert.equal(calc.getDisplay(), '12');
  assert.equal(calc.getExpression(), '12 +');
});

test('toggleSign negates the displayed value and leaves "0" unchanged', () => {
  assert.equal(calcWith('5S').getDisplay(), '-5');
  assert.equal(calcWith('5SS').getDisplay(), '5');
  assert.equal(calcWith('0S').getDisplay(), '0');
});

test('percent divides the displayed value by 100', () => {
  assert.equal(calcWith('50%').getDisplay(), '0.5');
});

// getExpression

test('getExpression shows the pending part while an operator is pending', () => {
  const calc = calcWith('12+');
  assert.equal(calc.getExpression(), '12 +');
  press(calc, '3');
  assert.equal(calc.getExpression(), '12 +');
});

test('getExpression shows the full expression after equals', () => {
  assert.equal(calcWith('2+3=').getExpression(), '2 + 3 =');
});

// Errors

test('division by zero on equals shows "Error" and clears the expression', () => {
  const calc = calcWith('5/0=');
  assert.equal(calc.getDisplay(), 'Error');
  assert.equal(calc.getExpression(), '');
});

test('division by zero when an operator is pressed shows "Error"', () => {
  assert.equal(calcWith('5/0+').getDisplay(), 'Error');
});

test('while showing "Error", operators, equals, decimal, sign, backspace and percent do nothing', () => {
  const calc = calcWith('5/0=');
  press(calc, '+=.SB%');
  assert.equal(calc.getDisplay(), 'Error');
  assert.equal(calc.getExpression(), '');
});

test('clear recovers from "Error" back to "0"', () => {
  const calc = calcWith('5/0=C');
  assert.equal(calc.getDisplay(), '0');
  assert.equal(calc.getExpression(), '');
});

test('a digit typed while showing "Error" starts a fresh calculation', () => {
  assert.equal(calcWith('5/0=7+2=').getDisplay(), '9');
});
