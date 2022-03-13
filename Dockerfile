FROM condaforge/mambaforge
ADD . /flayout
RUN pip install /flayout[dev]
