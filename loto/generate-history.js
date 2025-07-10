const fs = require('fs');
const path = require('path');

const NOTE_DIR = path.join(__dirname, 'note');
const OUT_FILE = path.join(__dirname, 'history.json');

function extractNumbers(text) {
  // 4-digit: not part of a longer number, not part of a series
  const fourDigit = Array.from(new Set(
    (text.match(/(?<!\d)\b\d{4}\b(?!\d)/g) || [])
  ));
  // 6-digit: not part of a longer number, not part of a series
  const sixDigit = Array.from(new Set(
    (text.match(/(?<!\d)\b\d{6}\b(?!\d)/g) || [])
  ));
  // Also extract numbers like 'AB 123456'
  const sixDigitWithPrefix = Array.from(new Set(
    (text.match(/[A-Z]{1,3}\s?\d{6}/g) || [])
  ));
  return { fourDigit, sixDigit, sixDigitWithPrefix };
}

function parseHtmlFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  // Try to extract date from title or meta
  let date = '';
  const titleMatch = content.match(/Date[:\s]*([0-9]{2}\/[0-9]{2}\/[0-9]{4})/i);
  if (titleMatch) date = titleMatch[1];
  // Fallback: try to find date in the first 200 lines
  if (!date) {
    const dateMatch = content.match(/\b([0-9]{2}\/[0-9]{2}\/[0-9]{4})\b/);
    if (dateMatch) date = dateMatch[1];
  }
  // Extract all winner numbers from the prizes section
  const winnerMatches = Array.from(content.matchAll(/"winners"\s*:\s*\[(.*?)\]/gs));
  let allNumbers = [];
  for (const match of winnerMatches) {
    // Remove quotes, split by comma/space, remove location in brackets
    let nums = match[1]
      .replace(/"/g, '')
      .replace(/\([^)]+\)/g, '')
      .split(/,|\s+/)
      .map(s => s.trim())
      .filter(s => s && /^[A-Z0-9 ]+$/.test(s));
    allNumbers = allNumbers.concat(nums);
  }
  // Fallback: also extract numbers from the whole file
  if (allNumbers.length === 0) {
    const { fourDigit, sixDigit, sixDigitWithPrefix } = extractNumbers(content);
    allNumbers = allNumbers.concat(fourDigit, sixDigit, sixDigitWithPrefix);
  }
  // Separate 4-digit and 6-digit numbers
  const numbers4 = Array.from(new Set(allNumbers.filter(n => /^\d{4}$/.test(n))));
  const numbers6 = Array.from(new Set(allNumbers.filter(n => /^([A-Z]{1,3}\s?)?\d{6}$/.test(n))));
  return { date, numbers4, numbers6 };
}

function main() {
  const files = fs.readdirSync(NOTE_DIR).filter(f => f.endsWith('.html'));
  const history = [];
  for (const file of files) {
    const filePath = path.join(NOTE_DIR, file);
    const result = parseHtmlFile(filePath);
    if (result.date && (result.numbers4.length || result.numbers6.length)) {
      history.push(result);
    }
  }
  fs.writeFileSync(OUT_FILE, JSON.stringify(history, null, 2), 'utf8');
  console.log(`Generated ${OUT_FILE} with ${history.length} draws.`);
}

main();
