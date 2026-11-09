document.addEventListener('DOMContentLoaded', () => {
    const carousels = document.querySelectorAll('.dashboard-horizontal-carousel');

    carousels.forEach(carousel => {
        const controls = document.querySelectorAll(
            `[data-dashboard-scroll="${carousel.id}"]`
        );

        const updateControls = () => {
            const canScroll = carousel.scrollWidth > carousel.clientWidth + 1;
            const atStart = carousel.scrollLeft <= 1;
            const atEnd = carousel.scrollLeft + carousel.clientWidth >= carousel.scrollWidth - 1;

            controls.forEach(button => {
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
});
