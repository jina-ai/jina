FROM docker:git

RUN apk update && apk upgrade && apk --no-cache add curl bash make

CMD ["bash"]