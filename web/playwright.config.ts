import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'../tests/browser',use:{baseURL:'http://127.0.0.1:5173/scaleproof/'},webServer:{command:'npm run dev',url:'http://127.0.0.1:5173/scaleproof/',reuseExistingServer:!process.env.CI},reporter:[['list'],['json',{outputFile:'browser-results.json'}]]});
