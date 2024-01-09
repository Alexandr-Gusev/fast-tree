const {useState, useEffect, Fragment, useRef} = React;
const {createRoot} = ReactDOM;
const {debounce, Icon, TextField, InputAdornment, IconButton} = MaterialUI;

const SearchIcon = ({...props}) => <Icon {...props}>search</Icon>;
const CloseIcon = ({...props}) => <Icon {...props}>close</Icon>;
const TextSnippetIcon  = ({...props}) => <Icon {...props}>text_snippet</Icon>;

const getBlock = async (blockSize, blockStart, query) => {
	try {
		const response = await axios.post(
			"/get-block",
			{block_size: blockSize, block_start: blockStart, query}
		);
		return response.data;
	} catch (error) {
		console.error(error);
		return null;
	}
};

const fetch = async (blockSize, blockStart, query, onResult) => {
	const data = await getBlock(blockSize, blockStart, query);
	onResult(data);
};

const fetchWithDelay = debounce(fetch, 250);

const List = ({width, height, rowHeight}) =>  {
	const blockSize = Math.ceil(height / rowHeight) + 1;

	const [blockStart, setBlockStart] = useState(0);
	const [query, setQuery] = useState("");
	const [rows, setRows] = useState([]);
	const [total, setTotal] = useState(0);
	const [windowTop, setWindowTop] = useState(0);
	const [promptsCount, setPromptsCount] = useState(0);

	const ref = useRef();

	useEffect(() => {
		const onResult = data => {
			if (data === null) {
				return;
			}
			setRows(data.rows);
			setTotal(data.total);
			setWindowTop(blockStart * rowHeight);
		};
		fetchWithDelay(blockSize, blockStart, query, onResult);
	}, [blockSize, blockStart, query, setRows, setTotal, setWindowTop, promptsCount]);

	const onScroll = e => {
		setBlockStart(Math.floor(e.currentTarget.scrollTop / rowHeight));
	};

	const contentHeight = total * rowHeight;

	return (
		<Fragment>
			<div className="query" style={{width: `${width}px`}}>
				<IconButton
					size="small"
					color="primary"
					onClick={() => {
						setBlockStart(0);
						setPromptsCount(promptsCount + 1)
						ref.current.scrollTop = 0;
					}}
				>
					<SearchIcon color="primary" />
				</IconButton>
				<TextField
					fullWidth
					size="small"
					variant="outlined"
					value={query}
					onChange={e => {
						setBlockStart(0);
						setQuery(e.target.value)
						setPromptsCount(promptsCount + 1)
						ref.current.scrollTop = 0;
					}}
				/>
				<IconButton
					size="small"
					color="primary"
					onClick={() => {
						setBlockStart(0);
						setQuery("");
						setPromptsCount(promptsCount + 1)
						ref.current.scrollTop = 0;
					}}
				>
					<CloseIcon color="primary" />
				</IconButton>
			</div>
			<div className="list" style={{width: `${width}px`, height: `${height}px`}} onScroll={onScroll} ref={ref}>
				<div className="content" style={{height: `${contentHeight}px`}}>
					{rows.map(
						(row, index) => (
							<div key={row.id} className="row" style={{top: `${windowTop + index * rowHeight}px`}}>
								<TextSnippetIcon color="primary" />{row.name}
							</div>
						)
					)}
				</div>
			</div>
		</Fragment>
	);
};

const root = createRoot(document.getElementById("root"));

root.render(<List width={400} height={400} rowHeight={40} />);
