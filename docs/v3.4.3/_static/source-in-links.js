function addUTMSourceToLink(href) {
    try {
        var url = new URL(href);
        url.searchParams.set("utm_source", "jina");
        return url.href
    }
    catch{
        return href
    }
}

function addUTMSourceToLinks() {
    var anchors = document.getElementsByTagName("a");

    for (var i = 0; i < anchors.length; i++) {
        anchors[i].href = addUTMSourceToLink(anchors[i].href)
    }
}

window.onload = function () {
    addUTMSourceToLinks()
}