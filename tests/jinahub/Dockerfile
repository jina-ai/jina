FROM jinaai/jina:test-pip

WORKDIR /

#RUN python -m pip install --no-cache-dir --upgrade pip && \
#    cd jina && \
#    pip install --ignore-installed -e .[devel] && \
#    pip install docarray==0.21.0 && \
#    cd ..

COPY app.py flow.yml /
ENV JINA_LOG_LEVEL=DEBUG
ENTRYPOINT ["python", "app.py"]
