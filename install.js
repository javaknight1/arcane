#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const https = require('https');
const { execSync } = require('child_process');

const platform = process.platform;
const arch = process.arch;

let binaryName;
let downloadUrl;

// Map platform to binary name
switch (platform) {
  case 'darwin':
    binaryName = 'roadmap-notion-macos';
    break;
  case 'linux':
    binaryName = 'roadmap-notion-linux';
    break;
  case 'win32':
    binaryName = 'roadmap-notion-windows.exe';
    break;
  default:
    console.error(`Unsupported platform: ${platform}`);
    process.exit(1);
}

// Get the latest release version
const version = require('./package.json').version;
downloadUrl = `https://github.com/robavery/roadmap-notion/releases/download/v${version}/${binaryName}`;

const binDir = path.join(__dirname, 'bin');
const binaryPath = path.join(binDir, platform === 'win32' ? 'roadmap-notion.exe' : 'roadmap-notion');

// Ensure bin directory exists
if (!fs.existsSync(binDir)) {
  fs.mkdirSync(binDir, { recursive: true });
}

console.log(`Downloading ${binaryName} from ${downloadUrl}...`);

const file = fs.createWriteStream(binaryPath);

https.get(downloadUrl, (response) => {
  if (response.statusCode === 302 || response.statusCode === 301) {
    // Handle redirects
    https.get(response.headers.location, (redirectResponse) => {
      redirectResponse.pipe(file);
      file.on('finish', () => {
        file.close();
        fs.chmodSync(binaryPath, '755');
        console.log('✅ roadmap-notion installed successfully!');
        console.log('Run: npx roadmap-notion --help');
      });
    });
  } else if (response.statusCode === 200) {
    response.pipe(file);
    file.on('finish', () => {
      file.close();
      fs.chmodSync(binaryPath, '755');
      console.log('✅ roadmap-notion installed successfully!');
      console.log('Run: npx roadmap-notion --help');
    });
  } else {
    console.error(`Failed to download binary: ${response.statusCode}`);
    process.exit(1);
  }
}).on('error', (err) => {
  console.error('Download failed:', err.message);
  process.exit(1);
});