export function compute(a, op, b) {
  switch (op) {
    case '+': return a + b;
    case '-': return a - b;
    case '*': return a * b;
    case '/':
      if (b === 0) throw new Error('Division by zero');
      return a / b;
    default: throw new Error('Unknown operator');
  }
}

function expandExponential(text) {
  const [coefficient, exponent] = text.split('e');
  if (exponent === undefined) return text;

  const sign = coefficient.startsWith('-') ? '-' : '';
  const unsigned = sign ? coefficient.slice(1) : coefficient;
  const digits = unsigned.replace('.', '');
  const point = unsigned.includes('.') ? unsigned.indexOf('.') : unsigned.length;
  const position = point + Number(exponent);
  if (position <= 0) return `${sign}0.${'0'.repeat(-position)}${digits}`;
  if (position >= digits.length) {
    return sign + digits + '0'.repeat(position - digits.length);
  }
  return `${sign}${digits.slice(0, position)}.${digits.slice(position)}`;
}

export function formatNumber(n) {
  if (!Number.isFinite(n)) return 'Error';
  if (n === 0) return '0';

  const magnitude = Math.abs(n);
  if (magnitude >= 1e16 || magnitude < 1e-9) {
    return n.toExponential(11).replace(/\.?0+e/, 'e');
  }

  // JavaScript also uses exponents below 1e-6; these displays need decimals.
  return expandExponential(String(Number(n.toPrecision(12))));
}

export function createCalculator() {
  let display = '0';
  let expression = '';
  let value = 0;
  let left = null;
  let operator = null;
  let lastOperator = null;
  let lastOperand = null;
  // Only an entry can be edited; operators and equals leave a displayed value.
  let phase = 'entry';

  function clear() {
    display = '0';
    expression = '';
    value = 0;
    left = null;
    operator = null;
    lastOperator = null;
    lastOperand = null;
    phase = 'entry';
  }

  function showError() {
    clear();
    display = 'Error';
  }

  function showValue(nextValue) {
    if (!Number.isFinite(nextValue)) {
      showError();
      return false;
    }
    value = nextValue;
    display = formatNumber(value);
    return true;
  }

  function evaluate(a, op, b) {
    try {
      return showValue(compute(a, op, b));
    } catch {
      showError();
      return false;
    }
  }

  return {
    inputDigit(d) {
      if (typeof d !== 'string' || !/^[0-9]$/.test(d)) return;
      if (display === 'Error' || phase === 'result') clear();

      const entry = expandExponential(display);
      if (phase === 'operator' || entry === '0') {
        display = d;
      } else if (entry === '-0') {
        display = d === '0' ? '0' : `-${d}`;
      } else {
        if (entry.replace(/[^0-9]/g, '').length >= 16) return;
        display = entry + d;
      }
      value = Number(display);
      phase = 'entry';
    },

    inputDecimal() {
      if (display === 'Error') return;
      if (phase === 'result') clear();
      if (phase === 'operator') {
        display = '0.';
      } else {
        const entry = expandExponential(display);
        if (entry.includes('.')) return;
        display = entry + '.';
      }
      value = Number(display);
      phase = 'entry';
    },

    setOperator(op) {
      if (display === 'Error' || !['+', '-', '*', '/'].includes(op)) return;
      if (operator !== null && phase === 'entry') {
        if (!evaluate(left, operator, value)) return;
      }
      left = value;
      operator = op;
      lastOperator = null;
      lastOperand = null;
      expression = `${formatNumber(left)} ${operator}`;
      phase = 'operator';
    },

    equals() {
      if (display === 'Error') return;
      let a = left;
      let op = operator;
      let b = value;
      if (op === null) {
        if (phase !== 'result' || lastOperator === null) return;
        a = value;
        op = lastOperator;
        b = lastOperand;
      }
      if (!evaluate(a, op, b)) return;
      expression = `${formatNumber(a)} ${op} ${formatNumber(b)} =`;
      lastOperator = op;
      lastOperand = b;
      left = null;
      operator = null;
      phase = 'result';
    },

    clear,

    backspace() {
      if (display === 'Error' || phase !== 'entry') return;
      display = expandExponential(display).slice(0, -1);
      if (display === '' || display === '-' || !Number.isFinite(Number(display))) {
        display = '0';
      }
      value = Number(display);
    },

    toggleSign() {
      if (display === 'Error') return;
      if (value === 0 && phase === 'entry' && display.includes('.')) {
        // A zero decimal entry still being typed ("0.", "-0.00") keeps its point.
        display = display.startsWith('-') ? display.slice(1) : `-${display}`;
        value = Number(display);
      } else if (value === 0) {
        display = '0';
      } else {
        value = -value;
        display = display.startsWith('-') ? display.slice(1) : `-${display}`;
      }
      if (phase === 'operator') phase = 'entry';
    },

    percent() {
      if (display === 'Error') return;
      if (!showValue(value / 100)) return;
      if (phase === 'operator') phase = 'entry';
    },

    getDisplay() {
      return display;
    },

    getExpression() {
      return expression;
    },
  };
}
