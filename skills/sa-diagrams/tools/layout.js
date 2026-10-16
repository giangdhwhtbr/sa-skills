// Lay out an ELK JSON graph: node layout.js <in.json> <out.json>. Exit 1 with the error on failure.
const { readFileSync, writeFileSync } = require('fs');
const ELK = require('elkjs');

const [input, output] = process.argv.slice(2);
if (!input || !output) {
  console.error('usage: node layout.js <in.json> <out.json>');
  process.exit(1);
}
new ELK()
  .layout(JSON.parse(readFileSync(input, 'utf8')))
  .then((graph) => writeFileSync(output, JSON.stringify(graph)))
  .catch((error) => {
    console.error(error && error.message ? error.message : error);
    process.exit(1);
  });
