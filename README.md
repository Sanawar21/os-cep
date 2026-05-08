# Operating Systems CEP

To run the project without GUI run: `python main-no-ui.py`
You can configure the settings using `config.py`.

To run the project with GUI, you will need flask to be installed in your environment.
Configure the app using `config.py` then run `python server.py`. Then in a separate terminal, run `python main-ui.py` then open the URL `http://localhost:5000` for the visualization. 

## Note
The entire project, except the `server.py` file was developed by humans. Since UI was beyond the scope of this project, `claude.ai` was used to generate the code in `server.py`. 

Also, the visualization does not accurately depict the parallelism of the threads. It can be observed in the visualization that only one thread interacts with the crate or the tree at any given moment, which, according  to our no-UI simulation, shouldn't happen.
