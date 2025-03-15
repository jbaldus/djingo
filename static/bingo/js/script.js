const isTooTall = ({ clientHeight, scrollHeight }) => scrollHeight > clientHeight
const isTooWide = ({ clientWidth, scrollWidth }) => scrollWidth > clientWidth
const isTooBig = (element) => isTooTall(element) || isTooWide(element)

function adjustFontSize(element) {
    element.style.fontSize = '100px';
    let fontSize = window.getComputedStyle(element).fontSize.slice(0,-2) ;
    let minSize = 10 ;
    while (isTooBig(element.parentElement) && fontSize > minSize) {
        fontSize-- ;
        element.style.fontSize = `${fontSize}px`
    }
}

htmx.onLoad(function(content) {
    console.log(content);
    attachShowTargetHandler(content);
    for (text of content.getElementsByClassName("bingo-cell-text")) {
        adjustFontSize(text) ;
    }
});

function attachShowTargetHandler(element) {
    element == element || document
    element.querySelectorAll('[data-show-target]').forEach(button => {
        button.addEventListener('click', () => {
            const targetSelector = button.dataset.showTarget
            document.querySelectorAll(targetSelector).forEach(target => {
                target.classList.toggle('show');
            });
        });
    });
}
  
document.addEventListener('DOMContentLoaded', attachShowTargetHandler)
