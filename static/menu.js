// menu.js
// Initialize the mobile menu
function initializeMenu() {
    const menuToggle = document.getElementById('menu-toggle');
    const closeMenu = document.getElementById('close-menu');
    const mobileMenu = document.getElementById('mobile-menu');
    const menuOverlay = mobileMenu.querySelector('.menu-overlay');
    const slideInMenu = mobileMenu.querySelector('.slide-in');

    function openMenu() {
        mobileMenu.classList.remove('hidden');
        setTimeout(() => {
            menuOverlay.classList.add('opacity-100');
            slideInMenu.style.transform = 'translateX(0)';
        }, 10);
    }

    function closeMenuFunc() {
        menuOverlay.classList.remove('opacity-100');
        slideInMenu.style.transform = 'translateX(-100%)';
        setTimeout(() => {
            mobileMenu.classList.add('hidden');
        }, 300);
    }

    menuToggle.addEventListener('click', openMenu);
    closeMenu.addEventListener('click', closeMenuFunc);
    menuOverlay.addEventListener('click', closeMenuFunc);

    window.addEventListener('resize', () => {
        if (window.innerWidth >= 640) {
            closeMenuFunc();
        }
    });
}

document.addEventListener('DOMContentLoaded', initializeMenu);