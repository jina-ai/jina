function inIframe() {
    try {
      return window.self !== window.top;
    } catch (Exception) {
      return true;
    }
  }
  
  if (inIframe()) {
    document.getElementsByTagName('html')[0].classList.add('loaded-in-iframe');
  }