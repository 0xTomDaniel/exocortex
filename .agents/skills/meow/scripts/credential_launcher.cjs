// Deliver arguments to the installed official CLI in-process, not through OS argv.
// stdin is private input; stdout/stderr must be captured by the caller.
const fs = require('node:fs');
try {
  const input = JSON.parse(fs.readFileSync(0, 'utf8'));
  if (!Array.isArray(input.args) || !input.args.every(x => typeof x === 'string')) {
    throw new Error('Invalid arguments');
  }
  const entry = fs.realpathSync(process.argv[2]);
  process.argv = [process.execPath, entry, ...input.args];
  require(entry);
} catch (_) {
  process.stderr.write('Meow launcher failed; raw details withheld.\n');
  process.exitCode = 1;
}
