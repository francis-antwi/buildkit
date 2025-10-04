document.addEventListener('DOMContentLoaded', () => {
    // Cart functionality
    let cart = JSON.parse(localStorage.getItem('cart')) || [];
    const addToCartButtons = document.querySelectorAll('.add-to-cart');

    addToCartButtons.forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.dataset.id;
            cart.push(productId);
            localStorage.setItem('cart', JSON.stringify(cart));
            this.textContent = 'Added!';
            this.style.background = '#28a745';
            this.setAttribute('aria-label', 'Item added to cart');
            setTimeout(() => {
                this.textContent = 'Add to cart';
                this.style.background = '#ff6b35';
                this.setAttribute('aria-label', `Add ${this.closest('.product-info').querySelector('.product-name').textContent} to cart`);
            }, 2000);
        });
    });

    // Price filter validation
    const priceFilterForm = document.querySelector('#price-filter-form');
    if (priceFilterForm) {
        priceFilterForm.addEventListener('submit', (e) => {
            const minPrice = document.querySelector('.price-input[name="min_price"]').value;
            const maxPrice = document.querySelector('.price-input[name="max_price"]').value;
            if (minPrice < 0 || maxPrice < 0) {
                e.preventDefault();
                alert('Prices cannot be negative.');
            } else if (parseFloat(minPrice) > parseFloat(maxPrice)) {
                e.preventDefault();
                alert('Minimum price cannot exceed maximum price.');
            }
        });
    }

    // Search form submission
    const searchForm = document.querySelector('#filter-form');
    if (searchForm) {
        searchForm.addEventListener('submit', (e) => {
            const searchQuery = document.querySelector('.search-input[name="search"]').value;
            if (searchQuery.trim() === '') {
                e.preventDefault(); // Prevent empty search submissions
            }
        });
    });
});