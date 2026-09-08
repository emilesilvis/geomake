import catalog from './.generated/puzzles.json' with { type: 'json' };
import { createApp } from './api.js';

export default createApp(catalog);
