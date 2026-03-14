#!/usr/bin/env node
/**
 * Martian Converter - Convert Markdown to Notion Blocks
 *
 * CLI tool that reads markdown from stdin or file and outputs Notion blocks JSON
 *
 * Usage:
 *   echo "# Hello" | node martian_convert.js
 *   node martian_convert.js --file input.md
 *   node martian_convert.js --help
 */

const { markdownToBlocks } = require('@tryfabric/martian');
const fs = require('fs');
const readline = require('readline');

function printHelp() {
  console.log(`
Martian Markdown to Notion Blocks Converter

Usage:
  node martian_convert.js [options]

Options:
  --file <path>    Read markdown from file instead of stdin
  --help           Show this help message

Examples:
  echo "# Hello" | node martian_convert.js
  node martian_convert.js --file input.md
`);
}

async function readFromFile(filePath) {
  try {
    return fs.readFileSync(filePath, 'utf-8');
  } catch (error) {
    console.error(JSON.stringify({
      error: true,
      message: `Failed to read file: ${error.message}`
    }));
    process.exit(1);
  }
}

async function readFromStdin() {
  return new Promise((resolve) => {
    let input = '';
    const rl = readline.createInterface({
      input: process.stdin,
      terminal: false
    });

    rl.on('line', (line) => {
      input += line + '\n';
    });

    rl.on('close', () => {
      resolve(input);
    });
  });
}

function convertMarkdown(markdown) {
  try {
    const blocks = markdownToBlocks(markdown);
    return {
      error: false,
      blocks: blocks
    };
  } catch (error) {
    return {
      error: true,
      message: error.message
    };
  }
}

async function main() {
  const args = process.argv.slice(2);

  if (args.includes('--help') || args.includes('-h')) {
    printHelp();
    process.exit(0);
  }

  const fileIndex = args.indexOf('--file');
  let markdown;

  if (fileIndex !== -1 && args[fileIndex + 1]) {
    const filePath = args[fileIndex + 1];
    markdown = await readFromFile(filePath);
  } else {
    markdown = await readFromStdin();
  }

  if (!markdown || markdown.trim() === '') {
    console.error(JSON.stringify({
      error: true,
      message: 'No markdown input provided'
    }));
    process.exit(1);
  }

  const result = convertMarkdown(markdown);
  console.log(JSON.stringify(result, null, 2));
}

main().catch((error) => {
  console.error(JSON.stringify({
    error: true,
    message: error.message
  }));
  process.exit(1);
});
