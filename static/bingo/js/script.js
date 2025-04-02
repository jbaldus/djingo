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
    console.log(`Adjusting the font for item ${element.text}`)
}

htmx.onLoad(content => {
    // Adjust the font size for bingo cells
    content.querySelectorAll('.bingo-cell-text').forEach(adjustFontSize);
    // Attach handler for data-show-target attributes if it exists in new elements
    attachShowTargetHandler(content);
    attachHideTargetHandler(content);
    attachToggleTargetHandler(content);
});

function attachShowTargetHandler(el) {
    el = el || document ;
    el.querySelectorAll('[data-show-target]').forEach(button => {
        button.addEventListener('click', () => {
            const targetSelector = button.dataset.showTarget ;
            document.querySelectorAll(targetSelector).forEach(target => {
                target.classList.add('show');
            });
        });
    });
}

function attachHideTargetHandler(el) {
    el = el || document ;
    el.querySelectorAll('[data-hide-target]').forEach(button => {
        button.addEventListener('click', () => {
            const targetSelector = button.dataset.hideTarget ;
            document.querySelectorAll(targetSelector).forEach(target => {
                target.classList.remove('show');
            });
        });
    });
}

function attachToggleTargetHandler(el) {
    el = el || document ;
    el.querySelectorAll('[data-toggle-target]').forEach(button => {
        button.addEventListener('click', () => {
            const targetSelector = button.dataset.toggleTarget ;
            document.querySelectorAll(targetSelector).forEach(target => {
                target.classList.toggle('show');
            });
        });
    });
}
  
window.onload = () => document.querySelectorAll('.bingo-cell-text').forEach(adjustFontSize) ;

// Do the shadow scroll indicator:
document.addEventListener('DOMContentLoaded', () => {

    sidebarContent = document.getElementById("sidebar-content")
    topTarget = document.getElementById("sidebar-top-trigger")
    bottomTarget = document.getElementById("sidebar-bottom-trigger")

    intersectionCallback = (entries) => {
        entries.forEach(entry => {
            if (entry.target == topTarget) {
                if (entry.isIntersecting) {
                    sidebarContent.classList.remove("top-shadow")
                    console.log("Top Target Visible")
                }
                else {
                    sidebarContent.classList.add("top-shadow")
                    console.log("Top Target Not Visible")
                }
            }
            if (entry.target == bottomTarget) {
                if (entry.isIntersecting) {
                    sidebarContent.classList.remove("bottom-shadow")
                    console.log("Bottom Target Visible")
                }
                else {
                    sidebarContent.classList.add("bottom-shadow")
                    console.log("Bottom Target Not Visible")
                }
            }
        })
    }
    if (sidebarContent && topTarget && bottomTarget) {
        observer = new IntersectionObserver(intersectionCallback, {root: sidebarContent, threshold: 0.1})
        observer.observe(topTarget)
        observer.observe(bottomTarget)
    }
})