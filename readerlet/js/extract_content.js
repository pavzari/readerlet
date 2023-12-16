const fs = require("fs");
const { Readability } = require("@mozilla/readability");
const { JSDOM } = require("jsdom");

const INPUT_EXTENSION = ".html";
const OUTPUT_EXTENSION = ".content.json";

function readFile(path) {
  try {
    return fs.readFileSync(path, { encoding: "utf8" });
  } catch (error) {
    console.error(`Error reading file: ${error.message}`);
    process.exit(1);
  }
}

function writeFile(content, path) {
  try {
    fs.writeFileSync(path, content, { encoding: "utf8" });
  } catch (error) {
    console.error(`Error writing file: ${error.message}`);
    process.exit(1);
  }
}

function extractContent() {
  // Usage: node extract-content.js <htmlfileInputPath>

  if (!process.argv[2]) {
    console.error("Error: HTML input file argument missing.");
    process.exit(1);
  }

  const inputPath = process.argv[2];
  const outputPath = inputPath.replace(INPUT_EXTENSION, OUTPUT_EXTENSION);

  if (!fs.existsSync(inputPath)) {
    console.error(`Error: Input file '${inputPath}' does not exist.`);
    process.exit(1);
  }

  const html = readFile(inputPath);
  const doc = new JSDOM(html);
  const reader = new Readability(doc.window.document);
  const article = reader.parse();

  writeFile(JSON.stringify(article), outputPath);
  writeFile(article.content, "parsed-article.html");
  console.log("HTML processing completed.");

  // article JSON contains the content and some other fields to be extracted
  // in python.

  // "parsed-article.html" is the "content" key in the json - for testing purposes.

  // python json.load to load the json output.
}

extractContent();
