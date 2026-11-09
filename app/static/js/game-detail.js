document.addEventListener('DOMContentLoaded', () => {
    const relatedCarousels = document.querySelectorAll('.related-games-carousel');
    relatedCarousels.forEach(carousel => {
        const controls = document.querySelectorAll(
            `[data-related-scroll="${carousel.id}"]`
        );
        const updateControls = () => {
            const canScroll = carousel.scrollWidth > carousel.clientWidth + 1;
            controls.forEach(button => {
                const atStart = carousel.scrollLeft <= 1;
                const atEnd = carousel.scrollLeft + carousel.clientWidth >= carousel.scrollWidth - 1;
                button.disabled = !canScroll || (
                    button.dataset.direction === 'previous' ? atStart : atEnd
                );
            });
        };

        controls.forEach(button => {
            button.addEventListener('click', () => {
                const direction = button.dataset.direction === 'next' ? 1 : -1;
                carousel.scrollBy({
                    left: direction * carousel.clientWidth * 0.8,
                    behavior: 'smooth'
                });
            });
        });

        updateControls();
        carousel.addEventListener('scroll', updateControls, { passive: true });
        window.addEventListener('resize', updateControls);
    });

    const gallery = document.getElementById('gameGallery');
    const dialog = document.getElementById('gameGalleryDialog');
    const dialogImage = document.getElementById('gameGalleryDialogImage');
    const counter = document.getElementById('gameGalleryCounter');

    if (!gallery || !dialog || !dialogImage || !counter) {
        return;
    }

    const images = Array.from(gallery.querySelectorAll('.game-gallery-item img'));
    const closeButton = dialog.querySelector('.game-gallery-close');
    const previousButton = dialog.querySelector('.game-gallery-previous');
    const nextButton = dialog.querySelector('.game-gallery-next');
    const scrollButtons = dialog.ownerDocument.querySelectorAll('[data-gallery-scroll]');
    let activeIndex = 0;

    const showImage = (index) => {
        activeIndex = (index + images.length) % images.length;
        dialogImage.src = images[activeIndex].src;
        dialogImage.alt = images[activeIndex].alt;
        counter.textContent = `${activeIndex + 1} / ${images.length}`;
    };

    gallery.addEventListener('click', (event) => {
        const button = event.target.closest('.game-gallery-item');
        if (!button) {
            return;
        }
        showImage(Number(button.dataset.galleryIndex));
        dialog.showModal();
    });

    scrollButtons.forEach(button => {
        button.addEventListener('click', () => {
            const direction = button.dataset.galleryScroll === 'next' ? 1 : -1;
            gallery.scrollBy({
                left: direction * gallery.clientWidth * 0.8,
                behavior: 'smooth'
            });
        });
    });

    closeButton.addEventListener('click', () => dialog.close());
    previousButton.addEventListener('click', () => showImage(activeIndex - 1));
    nextButton.addEventListener('click', () => showImage(activeIndex + 1));
    dialog.addEventListener('click', (event) => {
        if (event.target === dialog) {
            dialog.close();
        }
    });
    dialog.addEventListener('keydown', (event) => {
        if (event.key === 'ArrowLeft') {
            showImage(activeIndex - 1);
        } else if (event.key === 'ArrowRight') {
            showImage(activeIndex + 1);
        }
    });
});
