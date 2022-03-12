FROM condaforge/mambaforge
ADD . /flayout
RUN pip install -e /flayout[dev]
RUN rm -rf /flayout
