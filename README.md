# how-many-words
A simple Flask project that counts the number of specified length words in documents.

## Getting started
The best way to run this project is with Docker. If you don't have Docker, you can run it without Docker, but you will need to install the dependencies manually.

### Run with Docker

```bash
docker-compose up
```

You can visit the application at [http://localhost:65011](http://localhost:65011).

Note: By default docker-compose will spawn 1 worker. You can change this by adding the `--scale` flag. For example, to spawn 3 workers:

```bash
docker-compose up --scale worker=3
```

Don't have Docker? [Install it](https://docs.docker.com/get-docker/).

### Run without Docker
It is highly recommended to use a virtual environment to run this project without Docker. You can use [venv](https://docs.python.org/3/library/venv.html) or [virtualenv](https://virtualenv.pypa.io/en/latest/).

Install the dependencies:

```bash
pip install -r server/requirements.txt
pip install -r worker/requirements.txt
```
Run the server:

```bash
cd server
waitress-serve --port 65011 app:app
```

Run the worker:

```bash
python worker/worker.py
```
You can visit the application at [http://localhost:65011](http://localhost:65011).

To see the available options for the worker, run:

```bash
python worker/worker.py --help
```

Note: You can run multiple workers by running the worker command multiple times. The workers will automatically distribute the work between themselves. You can also run the worker on a different machine, as long as it can access the server.

## License
This project is licensed under the GNU AGPL - see the [LICENSE](LICENSE) file for details.
