# Calculator

A browser-based calculator implementing standard arithmetic and state management with ES modules.

## Features

- Operations: addition (`+`), subtraction (`-`), multiplication (`*`), and division (`/`).
- Chained left-to-right evaluation: operations evaluate immediately as subsequent operators are entered (for example, `2 + 3 * 4 = 20`).
- Repeated equals: pressing equals repeatedly reapplies the last operator and operand.
- Percent: divides the active display value by 100.
- Sign toggle: negates the current value between positive and negative.
- Backspace: deletes the last entered digit during entry.
- 16-digit entry limit: prevents entering more than 16 digits for a single operand.
- 12-significant-digit results: formats calculated numbers up to 12 significant digits.
- Division by zero shows Error: displays `Error` and resets pending operations.

## Keyboard Shortcuts

| Key | Action |
| --- | --- |
| `0` to `9` | Input digit |
| `+`, `-`, `*`, `/` | Set operator |
| `.` | Input decimal point |
| `Enter`, `=` | Calculate result (equals). When a button has keyboard focus, `Enter` presses that button instead. |
| `Backspace` | Backspace |
| `Escape` | Clear all |
| `%` | Percent |

## Run Locally

This is a static site that uses ES modules, so it must be served over HTTP rather than opened directly as a file.

Serve from the `calculator/` directory using Python without installing dependencies:

```sh
python -m http.server
```

## Tests

Run the test suite using Node.js built-in test runner (Node 20 or later, no install needed):

```sh
cd calculator
node --test
```

Automated tests run on every push and pull request to `dev` via the CI step in [.github/workflows/validate.yml](../.github/workflows/validate.yml).

## Deploy

Deploys are hosted on Netlify and configured in [../netlify.toml](../netlify.toml) with `base = "calculator"`.

Only the `dev` branch builds; other branches are skipped using the `ignore` command (`[ "$BRANCH" != "dev" ]`) to save build credits. Security headers (such as CSP, X-Frame-Options, and X-Content-Type-Options) are defined in `netlify.toml`.

## Files

| File | Description |
| --- | --- |
| [index.html](index.html) | HTML document defining screen structure and button layout |
| [styles.css](styles.css) | Stylesheet providing responsive layout, theme variables, and key styling |
| [package.json](package.json) | Package manifest configuring module type and test script |
| [src/calculator.js](src/calculator.js) | Core calculation logic, formatting, and state management |
| [src/ui.js](src/ui.js) | DOM interactions, event listeners, and keyboard bindings |
| [test/calculator.test.js](test/calculator.test.js) | Unit tests verifying arithmetic, state transitions, and formatting |

## Engine API

Exports from [src/calculator.js](src/calculator.js):

- `compute(a, op, b)`: Computes arithmetic operations (`+`, `-`, `*`, `/`) between two numbers.
- `formatNumber(n)`: Formats numbers with up to 12 significant digits, switching to exponential notation when needed.
- `createCalculator()`: Factory function creating a stateful calculator instance.

Calculator instance methods:

- `inputDigit(d)`: Enters a single numeric digit character (`'0'` through `'9'`).
- `inputDecimal()`: Enters a decimal point for fractional numbers.
- `setOperator(op)`: Sets the current operator and evaluates any pending operation.
- `equals()`: Evaluates the pending operation or repeats the previous operation.
- `clear()`: Resets calculator state and display back to initial values.
- `backspace()`: Removes the last entered character from the active entry.
- `toggleSign()`: Inverts the sign of the current value.
- `percent()`: Divides the currently active value by 100.
- `getDisplay()`: Returns the string currently shown on the primary display.
- `getExpression()`: Returns the secondary expression string representation.
