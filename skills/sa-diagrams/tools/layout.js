// Lay out ELK JSON graphs: node layout.js <in.json> <out.json>. The input is one graph or an array of
// graphs (laid out in one process); the output has the same shape. Exit 1 with the error on failure.
const { readFileSync, writeFileSync } = require('fs');
const ELK = require('elkjs');

const [input, output] = process.argv.slice(2);
if (!input || !output) {
  console.error('usage: node layout.js <in.json> <out.json>');
  process.exit(1);
}
const elk = new ELK();
const graphs = JSON.parse(readFileSync(input, 'utf8'));
(Array.isArray(graphs) ? Promise.all(graphs.map((g) => elk.layout(g))) : elk.layout(graphs))
  .then((result) => writeFileSync(output, JSON.stringify(result)))
  .catch((error) => {
    console.error(error && error.message ? error.message : error);
    process.exit(1);
  });
