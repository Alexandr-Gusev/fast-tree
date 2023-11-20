const commander = require("commander");
const express = require("express");
const path = require("path");

commander
	.option("--port <value>", "Port.", 3000)
	.option("--addr <value>", "Address.", "0.0.0.0")
	.parse();
const opts = commander.opts();

const allRows = [];
let i = 1;
while (i <= 250000) {
	allRows.push({
		"guid": `${i}`,
		"name": `Row ${i}`,
		"tags": `row ${i}`
	});
	i += 1;
}

const getBlock = async (allRows, count, start, query) => {
	query = query.toLowerCase();
	const rows = [];
	let total = 0;
	for (const row of allRows) {
		if (query === "" || row.tags.indexOf(query) != -1) {
			if (total >= start && rows.length < count) {
				rows.push(row);
			}
			total += 1;
		}
	}
	return {rows, total};
};

const getBlockHandler = async (req, res) => {
	let {count, start, query} = req.body;
	const t = new Date().getTime();
	block = await getBlock(allRows, count, start, query)
	console.log("dt: " + (new Date().getTime() - t) + " ms");
	return res.json(block);
};

const app = express();
app.use(express.json());
app.get("/", (req, res) => {
	res.sendFile(path.join(__dirname, "..", "static", "index.html"));
});
app.use("/static", express.static(path.join(__dirname, "..", "static")));
app.post("/get-block", getBlockHandler);

app.listen(opts.port, () => console.log(`Server listening on port ${opts.port}`));
