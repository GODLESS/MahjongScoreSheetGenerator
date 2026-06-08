/*
 *  convert.js — core integration module
 *
 *  Pipeline: Tenhou log ID → fetch XML → 电脑麻雀 JSON → 天凤观战 JSON
 */
"use strict";

const getlog  = require("@kobalab/tenhou-log/lib/getlog")();
const convlog = require("@kobalab/tenhou-log");
const logconv = require("@kobalab/tenhou-url-log");

/**
 * Extract a pure log ID from a full Tenhou URL.
 * Supports:
 *   http://tenhou.net/0/log/?{id}
 *   http://tenhou.net/0/log/?{id}&...
 *   Just plain {id}
 */
function extract_log_id(input) {
    // Format 1: tenhou.net/0/log/?{id}
    if (input.includes("tenhou.net/0/log/")) {
        let match = input.match(/[?&]([^?&=#]+)$/);
        if (match) return match[1];
    }
    // Format 2: tenhou.net/0/?log={id}
    if (input.includes("tenhou.net")) {
        let match = input.match(/[?&]log=([^&#]+)/);
        if (match) return match[1];
        // Format 3: extract GM-pattern ID from any URL
        match = input.match(/(\\d{4}gm-\\w{4}-\\w{4}-\\w{8})/);
        if (match) return match[1];
    }
    return input;
}

/**
 * Convert a Tenhou log ID (or URL) to Tenhou spectator JSON.
 *
 * @param {string}  input   — log ID or full Tenhou log URL
 * @param {object}  options — { idx, rule, title }
 * @param {number}  options.idx   — game index (0-based), null = all games
 * @param {object}  options.rule  — rule descriptor (default: {disp:"电脳麻雀", aka:1})
 * @param {string}  options.title — override title (default: log ID)
 * @returns {Promise<object>}     — Tenhou spectator JSON object
 */
function convert(input, options = {}) {
    let id    = extract_log_id(input);
    let idx   = options.idx != null ? options.idx : null;
    let rule  = options.rule || { disp: "电脳麻雀", aka: 1 };
    let title = options.title || id;

    return getlog(id).then(xml => {
        let paipu = convlog(xml, title);
        return logconv(paipu, idx, rule);
    });
}

module.exports = convert;
