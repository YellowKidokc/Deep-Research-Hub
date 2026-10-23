import express from 'express';
import path from 'node:path';
const app = express();
const root = path.join(import.meta.dirname, 'dist', 'public');
app.get('/__local_site', (_req, res) => res.json({site:'axiom-navigator-local'}));
app.use(express.static(root));
app.get('*', (_req, res) => res.sendFile(path.join(root, 'index.html')));
app.listen(8774, '127.0.0.1', () => console.log('Axiom Navigator: http://127.0.0.1:8774'));
