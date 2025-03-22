const isTooTall = ({ clientHeight, scrollHeight }) => scrollHeight > clientHeight
const isTooWide = ({ clientWidth, scrollWidth }) => scrollWidth > clientWidth
const isTooBig = (element) => isTooTall(element) || isTooWide(element)

function adjustFontSize(element) {
    element.style.fontSize = '100px';
    let fontSize = window.getComputedStyle(element).fontSize.slice(0,-2) ;
    let minSize = 6 ;
    while (isTooBig(element.parentElement) && fontSize > minSize) {
        fontSize-- ;
        element.style.fontSize = `${fontSize}px`
    }
}

htmx.onLoad(function(content) {
    console.log(content);
    // Attach handler for data-show-target attributes if it exists in new elements
    attachShowTargetHandler(content);
    // Adjust the font size for bingo cells
    for (text of content.getElementsByClassName("bingo-cell-text")) {
        adjustFontSize(text) ;
    }
});

function attachShowTargetHandler(el) {
    el == el || document ;
    el.querySelectorAll('[data-show-target]').forEach(button => {
        button.addEventListener('click', () => {
            const targetSelector = button.dataset.showTarget ;
            document.querySelectorAll(targetSelector).forEach(target => {
                target.classList.toggle('show');
            });
        });
    });
}
  
document.addEventListener('DOMContentLoaded', attachShowTargetHandler)

// Do the shadow scroll indicator:
document.addEventListener('DOMContentLoaded', () => {

    sidebarContent = document.getElementById("sidebar-content")
    topTarget = document.getElementById("sidebar-top-trigger")
    bottomTarget = document.getElementById("sidebar-bottom-trigger")

    intersectionCallback = (entries) => {
        entries.forEach((entry) => {
            if (entry.target == topTarget) {
                if (entry.isIntersecting) {
                    sidebarContent.classList.remove("top-shadow")
                }
                else {
                    sidebarContent.classList.add("top-shadow")
                }
            }
            if (entry.target == bottomTarget) {
                if (entry.isIntersecting) {
                    sidebarContent.classList.remove("bottom-shadow")
                }
                else {
                    sidebarContent.classList.add("bottom-shadow")
                }
            }
        })
    }

    observer = new IntersectionObserver(intersectionCallback, {root: sidebarContent, threshold: 1.0})
    observer.observe(topTarget)
    observer.observe(bottomTarget)
})