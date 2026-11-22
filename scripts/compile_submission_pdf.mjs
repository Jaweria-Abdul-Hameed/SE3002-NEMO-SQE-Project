import { chromium } from 'playwright';
import { fileURLToPath } from 'url';
import path from 'path';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function main() {
  const htmlPath = path.resolve(__dirname, '..', 'docs', 'FINAL_PROJECT_REPORT.html');
  const pdfPath = path.resolve(__dirname, '..', 'Project_24I-3025_24I-3135_24P-3099_A.pdf');

  if (!fs.existsSync(htmlPath)) {
    throw new Error(`HTML source file not found at: ${htmlPath}`);
  }

  console.log(`Launching Chromium to compile: ${htmlPath}`);
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  // Load the HTML report
  const fileUrl = `file://${htmlPath.replace(/\\/g, '/')}`;
  await page.goto(fileUrl, { waitUntil: 'load' });

  // Wait a moment for styles and SVG rendering
  await page.waitForTimeout(1000);

  console.log(`Rendering PDF to: ${pdfPath}`);
  await page.pdf({
    path: pdfPath,
    format: 'A4',
    printBackground: true,
    margin: {
      top: '16mm',
      bottom: '16mm',
      left: '14mm',
      right: '14mm',
    },
    displayHeaderFooter: false,
    preferCSSPageSize: true,
  });

  await browser.close();

  const stats = fs.statSync(pdfPath);
  console.log(`PDF successfully created! Size: ${(stats.size / 1024).toFixed(1)} KB`);
}

main().catch((err) => {
  console.error('Failed to compile PDF:', err);
  process.exit(1);
});
