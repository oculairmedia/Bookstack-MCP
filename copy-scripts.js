import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

// Get the directory name in ESM
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Define source and destination directories
const srcDir = path.join(__dirname, 'src', 'tools');
const destDir = path.join(__dirname, 'dist', 'tools');

// Create destination directory if it doesn't exist
if (!fs.existsSync(destDir)) {
  fs.mkdirSync(destDir, { recursive: true });
  console.log(`Created directory: ${destDir}`);
}

// Get all Python files from source directory
const pythonFiles = fs.readdirSync(srcDir).filter(file => file.endsWith('.py'));

// Copy each Python file to the destination directory
pythonFiles.forEach(file => {
  const srcPath = path.join(srcDir, file);
  const destPath = path.join(destDir, file);
  
  fs.copyFileSync(srcPath, destPath);
  console.log(`Copied: ${file}`);
});

console.log(`Successfully copied ${pythonFiles.length} Python files to ${destDir}`);