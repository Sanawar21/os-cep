# Operating Systems CEP

Run `git pull` to get the latest version of the project.

To run the project without GUI run: `python main-no-ui.py`
You can configure the settings using `config.py`.

To run the project with GUI, you will need flask to be installed in your environment.
Configure the app using `config.py` then run `python server.py`. Then in a separate terminal, run `python main-ui.py` then open the URL `http://localhost:5000` for the visualization. 

## Configuration
We encourage the user to configure the project beyond the original constraints for the CEP. For example, setting an absurdly large number of `CRATE_CAPACITY`, `PICKER_COUNT` or `TOTAL_FRUITS`; or setting some non-zero `TRUCK_LOADING_TIME` and `CRATE_LOADING_TIME`. 

`do_work()` is a function in the program which is used for simulating actual, time-consuming, work being done during crate filling and emptying. `BUSY_WAIT_IN_DO_WORK` is used to configure the type of work (blocking or non-blocking) that will be done during the `do_work()` function call.

## Note
The entire project, except the `server.py` file was developed by the group members. Since UI was beyond the scope of this project, `claude.ai` was used to generate the code in `server.py`. 

Also, the visualization does not accurately depict the parallelism of the threads. It can be observed in the visualization that only one thread interacts with the crate or the tree at any given moment, which (according  to our no-UI simulation) shouldn't happen.
