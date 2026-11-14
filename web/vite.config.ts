import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({plugins:[react()],base:'/scaleproof/',build:{outDir:'dist'},server:{port:5173}});
