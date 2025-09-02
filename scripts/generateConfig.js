const fs = require('fs');
const path = require('path');

// Read .env.frontend
const envPath = path.join(__dirname, '..', '.env.frontend');
const envContent = fs.readFileSync(envPath, 'utf8');

// Parse environment variables
const config = {};
envContent.split('\n').forEach(line => {
  const [key, value] = line.split('=');
  if (key && value) {
    config[key.trim()] = value.trim();
  }
});

// Generate config.js
const configJs = `
// Auto-generated configuration file
// Do not edit manually - generated from .env.frontend
window.CONFIG = ${JSON.stringify(config, null, 2)};
`;

// Write to public/config.js
const outputPath = path.join(__dirname, '..', 'public', 'config.js');
fs.writeFileSync(outputPath, configJs);

console.log('Generated public/config.js from .env.frontend');