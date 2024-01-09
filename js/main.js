const commander = require("commander");
const express = require("express");
const path = require("path");

commander
	.option("--port <value>", "Port.", 3000)
	.option("--addr <value>", "Address.", "0.0.0.0")
	.parse();
const opts = commander.opts();

const rows = [];
let i = 1;
while (i <= 250000) {
	rows.push({
		id: `${i}`,
		name: `Row ${i}`,
		keyForSearch: `row ${i}`
	});
	i += 1;
}

const getBlock = async (rows, blockSize, blockStart, query) => {
	query = query.toLowerCase();
	const blockRows = [];
	let total = 0;
	for (const row of rows) {
		if (query === "" || row.keyForSearch.indexOf(query) != -1) {
			if (total >= blockStart && blockRows.length < blockSize) {
				blockRows.push(row);
			}
			total += 1;
		}
	}
	return {rows: blockRows, total};
};

const getBlockHandler = async (req, res) => {
	let {block_size: blockSize, block_start: blockStart, query} = req.body;
	const t = new Date().getTime();
	block = await getBlock(rows, blockSize, blockStart, query)
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
