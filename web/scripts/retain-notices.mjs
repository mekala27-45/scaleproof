import {copyFileSync,mkdirSync} from 'node:fs';
const fonts=['fenix','lunasima','rubik-mono-one'];
mkdirSync('public/licenses',{recursive:true});
for(const font of fonts)copyFileSync(`node_modules/@fontsource/${font}/LICENSE`,`public/licenses/${font}.txt`);
