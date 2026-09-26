import {defineConfig} from 'vite';
export default defineConfig({server:{proxy:{'/api':'http://127.0.0.1:8000'}},build:{outDir:'dist',rollupOptions:{output:{manualChunks(id){if(id.includes('node_modules')){if(/recharts|d3-|victory-vendor/.test(id))return 'charts';return 'vendor';}}}}}});
