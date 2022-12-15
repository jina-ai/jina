function addUTMSourceToLink(href) {
    try {
        var url = new URL(href);
        url.searchParams.set("utm_source", "core");
        return url.href
    }
    catch{}
}

function addSourceToAllLinks() {
    var anchors = document.getElementsByTagName("a");

    for (var i = 0; i < anchors.length; i++) {
        anchors[i].href = addUTMSourceToLinks(anchors[i].href)
    }
}

window.onload = function () {
    addSourceToAllLinks()
}