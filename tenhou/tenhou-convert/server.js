#!/usr/bin/env node

"use strict";

const yargs   = require("yargs");
const express = require("express");
const convert = require("./lib/convert");

const argv = yargs
    .option("port",    { alias: "p", default: 8002 })
    .option("baseurl", { alias: "b", default: "/convert/" })
    .option("docroot", { alias: "d" })
    .argv;

const port = argv.port;
const base = ("" + argv.baseurl)
                .replace(/^(?!\/.*)/, "/$&")
                .replace(/\/$/, "") + "/";
const docs = argv.docroot;

const app = express();

app.get(base + ":id", (req, res, next) => {
    let id  = req.params.id;
    let idx = req.query.idx != null ? +req.query.idx : null;

    convert(id, { idx: idx })
        .then(json => res.json(json))
        .catch(e => {
            if      (e == 404) next();
            else if (e == 500) res.status(502).json({ error: "Bad Gateway" });
            else               res.status(415).json({ error: e.message });
        });
});

if (docs) app.use(express.static(docs));
app.use((req, res) => res.status(404).json({ error: "Not Found" }));

app.listen(port,
    () => console.log(
        "Server start on http://127.0.0.1:" + port + base,
        docs ? "(docroot=" + docs + ")" : "")
).on("error", e => {
    console.error("" + e);
    process.exit(-1);
});
