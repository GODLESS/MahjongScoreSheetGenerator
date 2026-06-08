const assert  = require("assert");

const convert = require("../");

suite("convert()", () => {

    test("function exists", () => assert.ok(convert));

    test("returns a Promise", () => {
        let p = convert("test");
        assert.ok(p instanceof Promise);
        p.catch(() => {}); // suppress unhandled rejection
    });

    test("rejects with 404 for bad ID", done => {
        convert("badid").catch(code => {
            assert.equal(code, 404);
            done();
        });
    });

    test("converts known log ID", done => {
        convert("2016031822gm-0009-10011-896da481")
            .then(json => {
                assert.ok(json.title);
                assert.ok(Array.isArray(json.name));
                assert.equal(json.name.length, 4);
                assert.ok(json.rule);
                assert.ok(Array.isArray(json.log));
                assert.ok(json.log.length > 0);
                done();
            })
            .catch(e => {
                if (e == 500) {
                    // network unavailable, skip
                    console.log("(network unavailable, skipping live test)");
                    done();
                }
                else done(e);
            });
    });

    test("converts with --idx=0 (first game only)", done => {
        convert("2016031822gm-0009-10011-896da481", { idx: 0 })
            .then(json => {
                assert.ok(json.title);
                assert.equal(json.log.length, 1);
                done();
            })
            .catch(e => {
                if (e == 500) {
                    console.log("(network unavailable, skipping live test)");
                    done();
                }
                else done(e);
            });
    });

});
