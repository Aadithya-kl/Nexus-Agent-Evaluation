# NEXUS Evaluation Lab · V1.1

Open `index.html` in a browser, or serve this directory locally. Choose a
scenario, edit the two JSON inputs, then evaluate and export the report. Use
synthetic data. The browser evaluates declared outputs in memory. Agent
execution, runtime permissions and evidence authentication are outside its scope.

## Build and checks

From the repository root, with Python 3.10+ and Node on the path:

~~~sh
python docs/lab/build.py
python docs/lab/build.py --check
python docs/lab/test_parity.py
~~~

`template.html` contains the interface and `engine.js` contains the JavaScript
port. The build embeds the root [MIT license](../../LICENSE) and the three
synthetic inputs from `examples/` in a UTF-8 HTML file with LF line endings.
The optional browser smoke test uses Playwright 1.65.2, available for Chromium
and Firefox. To run it against a local HTTP origin:

~~~sh
python -m pip install playwright==1.65.2
python -m playwright install chromium firefox
python -m http.server 8765 --bind 127.0.0.1 --directory docs/lab
~~~

In a separate terminal:

~~~sh
python docs/lab/test_browser.py --browser chromium --url http://127.0.0.1:8765/
python docs/lab/test_browser.py --browser firefox --url http://127.0.0.1:8765/
~~~

Use `--screenshots <directory>` to capture desktop and mobile screenshots.
Use `--executable <path>` to test an installed Chromium-based browser.

## Semantics and provenance

The Python [evaluator](../../evaluator.py) is authoritative. The V1.1 port was
derived from [commit b2b95c4](https://github.com/Yusyer174/Nexus-Agent-Evaluation/tree/b2b95c44a411d9605415e8a94288c392612e65dd).
At integration, the reference evaluator blob
`1dbb90c9b51c814a95a0fe3fbfdf3e9604661e70` and all three bundled fixture blobs
matched that revision. Parity now runs against the source and fixtures in the
checkout. See the [input contract](../INTEGRATION.md) for the evaluator rules.

- The browser accepts standard JSON. Python parser extensions such as `NaN`
  and `Infinity` are outside the browser input format. Syntax errors use
  browser-specific diagnostics. Both implementations reject duplicate keys.
- Input is capped at 100,000 UTF-16 code units per editor, depth 64 with root
  depth zero, and 200 cases. The UI accepts a percentage and the report records
  the equivalent fraction. Displayed percentages may be rounded.
- Critical case failures and unexpected prediction IDs close the gate even at
  0%. The UI labels results with the corresponding Python CLI exit codes.
- Reports are downloaded as JSON from memory. The HTML loads from its host
  when opened online. The app includes a policy that blocks script-initiated
  network connections. Repository and feedback links open GitHub when clicked.

## Pages publishing

After integration and successful checks, set the Pages source to GitHub Actions
and run the Evaluation Lab workflow manually on `main`. Its validation job
checks the build and parity before uploading the single HTML page. The deploy
job publishes that artifact to the `github-pages` environment.
