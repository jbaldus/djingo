const isTooBig = ({ clientHeight, scrollHeight }) => scrollHeight > clientHeight

function adjustFontSize(element) {
    let fontSize = window.getComputedStyle(element).fontSize.slice(0,-2) ;
    let minSize = 12 ;
    while (isTooBig(element.parentElement) && fontSize > minSize) {
        fontSize-- ;
        element.style.fontSize = `${fontSize}px`
    }
}

htmx.onLoad(function(content) {
    console.log(content);
    for (text of content.getElementsByClassName("bingo-cell-text")) {
        adjustFontSize(text) ;
    }
});
  