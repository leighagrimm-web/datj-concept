// Encrypt the Company bundle with a password (PBKDF2-SHA256 + AES-GCM), same as the browser decrypts it.
import { readFileSync, writeFileSync } from 'node:fs';
import { webcrypto as C } from 'node:crypto';
const [,, src, out, pw] = process.argv;
const enc = new TextEncoder(), b64 = (u) => Buffer.from(u).toString('base64');
const salt = C.getRandomValues(new Uint8Array(16)), iv = C.getRandomValues(new Uint8Array(12));
const base = await C.subtle.importKey('raw', enc.encode(pw), 'PBKDF2', false, ['deriveKey']);
const key = await C.subtle.deriveKey({ name: 'PBKDF2', salt, iterations: 250000, hash: 'SHA-256' }, base, { name: 'AES-GCM', length: 256 }, false, ['encrypt']);
const ct = await C.subtle.encrypt({ name: 'AES-GCM', iv }, key, enc.encode(readFileSync(src, 'utf8')));
writeFileSync(out, JSON.stringify({ v: 1, it: 250000, s: b64(salt), i: b64(iv), c: b64(new Uint8Array(ct)) }));
console.log('encrypted', readFileSync(src).length, 'bytes');
