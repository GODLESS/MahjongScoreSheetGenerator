#!/usr/bin/env node

"use strict";

const yargs   = require("yargs");
const convert = require("./lib/convert");

const argv = yargs
    .usage("Usage: $0 [--idx=n] [--rule=json] <logid|url> [...]")
    .option("idx", { alias: "i", type: "number",
                     description: "Game index (0-based, omit for all games)" })
    .option("rule", { alias: "r", type: "string",
                      description: "Rule JSON (default: {\"disp\":\"电脳麻雀\",\"aka\":1})" })
    .demandCommand(1)
    .argv;

const multi = argv._.length > 1;
let results = [];
let rule    = null;

if (argv.rule) {
    try {
        rule = JSON.parse(argv.rule);
    }
    catch (e) {
        console.error("Invalid rule JSON: " + e.message);
        process.exit(-1);
    }
}

function do_converts() {

    if (!argv._.length) {
        process.stdout.write(
            multi ? JSON.stringify(results) : JSON.stringify(results[0]));
        process.stdout.write("\n");
        process.exit(0);
    }

    let arg = argv._.shift();
    let idx = argv.idx != null ? argv.idx : null;

    convert(arg, { idx: idx, rule: rule })
        .then(json => {
            results.push(json);
            setTimeout(do_converts, 0);
        })
        .catch(e => {
            if      (e == 404) console.error(arg + ": not found.");
            else if (e == 500) console.error("Server Error.");
            else               console.error(arg + ": " + e.message);
            process.exit(-1);
        });
}

do_converts();
