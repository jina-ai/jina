FROM python

RUN pip3 install "jina[standard]" && apt update && apt install -y nginx

ADD https://raw.githubusercontent.com/longwuyuan/jina/master/kubernetes/image/example.py /

EXPOSE 12345

ENTRYPOINT ["python3", "/example.py"]
