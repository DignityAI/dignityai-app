// Main JavaScript file for Content Aggregator
(function() {
    'use strict';

    // Global variables
    let isRefreshing = false;

    // Initialize the application
    document.addEventListener('DOMContentLoaded', function() {
        initializeApp();
        setupEventListeners();
        setupTooltips();
        setupProgressiveLoading();
    });

    function initializeApp() {
        console.log('Content Aggregator initialized');
        
        // Add loading states to initial content
        setupLoadingStates();
        
        // Setup auto-refresh if enabled
        setupAutoRefresh();
        
        // Initialize content animations
        animateContentCards();
    }

    function setupEventListeners() {
        // Refresh button
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', refreshContent);
        }

        // Navbar collapse on mobile
        const navbarToggler = document.querySelector('.navbar-toggler');
        if (navbarToggler) {
            navbarToggler.addEventListener('click', function() {
                const navbar = document.querySelector('.navbar-collapse');
                navbar.classList.toggle('show');
            });
        }

        // Close mobile menu when clicking outside
        document.addEventListener('click', function(event) {
            const navbar = document.querySelector('.navbar-collapse');
            const toggler = document.querySelector('.navbar-toggler');
            
            if (navbar && navbar.classList.contains('show') && 
                !navbar.contains(event.target) && 
                !toggler.contains(event.target)) {
                navbar.classList.remove('show');
            }
        });

        // Smooth scrolling for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });

        // Search functionality (if search box exists)
        const searchInput = document.querySelector('#searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', debounce(performSearch, 300));
        }
    }

    function setupTooltips() {
        // Initialize Bootstrap tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    function setupProgressiveLoading() {
        // Setup intersection observer for lazy loading
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        imageObserver.unobserve(img);
                    }
                });
            });

            document.querySelectorAll('img[data-src]').forEach(img => {
                imageObserver.observe(img);
            });
        }
    }

    function setupLoadingStates() {
        // Add loading indicators to content areas
        const contentAreas = document.querySelectorAll('.content-preview, .card-body');
        contentAreas.forEach(area => {
            if (area.children.length === 0) {
                area.innerHTML = `
                    <div class="text-center p-4">
                        <div class="spinner-border text-secondary" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <p class="mt-2 text-muted">Loading content...</p>
                    </div>
                `;
            }
        });
    }

    function setupAutoRefresh() {
        // Auto-refresh content every 10 minutes (if enabled)
        const autoRefreshInterval = 600000; // 10 minutes
        
        if (localStorage.getItem('autoRefresh') === 'enabled') {
            setInterval(() => {
                if (!isRefreshing && document.visibilityState === 'visible') {
                    refreshContent(true); // Silent refresh
                }
            }, autoRefreshInterval);
        }
    }

    function animateContentCards() {
        // Animate cards on load
        const cards = document.querySelectorAll('.card');
        cards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 100);
        });
    }

    // Global refresh function
    window.refreshContent = function(silent = false) {
        if (isRefreshing) return;
        
        isRefreshing = true;
        const refreshBtn = document.getElementById('refreshBtn');
        const loadingOverlay = document.getElementById('loadingOverlay');
        
        if (!silent) {
            // Show loading state
            if (refreshBtn) {
                const originalHTML = refreshBtn.innerHTML;
                refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Refreshing...';
                refreshBtn.disabled = true;
            }
            
            if (loadingOverlay) {
                loadingOverlay.classList.remove('d-none');
            }
        }

        // Call the refresh API
        fetch('/refresh-cache', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (!silent) {
                showNotification('Content refreshed successfully!', 'success');
                
                // Reload the page after a short delay
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }
        })
        .catch(error => {
            console.error('Error refreshing content:', error);
            if (!silent) {
                showNotification('Failed to refresh content. Please try again.', 'error');
            }
        })
        .finally(() => {
            isRefreshing = false;
            
            if (!silent) {
                // Reset button state
                if (refreshBtn) {
                    refreshBtn.innerHTML = '<i class="fas fa-sync-alt me-1"></i>Refresh';
                    refreshBtn.disabled = false;
                }
                
                if (loadingOverlay) {
                    loadingOverlay.classList.add('d-none');
                }
            }
        });
    };

    function showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    function performSearch(query) {
        const searchTerm = query.toLowerCase().trim();
        if (searchTerm.length < 2) return;
        
        // Search through content cards
        const contentCards = document.querySelectorAll('.card');
        let visibleCount = 0;
        
        contentCards.forEach(card => {
            const title = card.querySelector('.card-title, h4, h5, h6');
            const content = card.querySelector('.content-preview, .card-body');
            
            const titleText = title ? title.textContent.toLowerCase() : '';
            const contentText = content ? content.textContent.toLowerCase() : '';
            
            if (titleText.includes(searchTerm) || contentText.includes(searchTerm)) {
                card.style.display = '';
                visibleCount++;
                
                // Highlight search terms
                highlightSearchTerm(card, searchTerm);
            } else {
                card.style.display = 'none';
            }
        });
        
        // Show search results count
        updateSearchResults(visibleCount, searchTerm);
    }

    function highlightSearchTerm(element, term) {
        // Remove existing highlights
        element.querySelectorAll('.search-highlight').forEach(highlight => {
            highlight.outerHTML = highlight.innerHTML;
        });
        
        // Add new highlights
        const walker = document.createTreeWalker(
            element,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );
        
        const textNodes = [];
        let node;
        
        while (node = walker.nextNode()) {
            textNodes.push(node);
        }
        
        textNodes.forEach(textNode => {
            const text = textNode.textContent;
            const regex = new RegExp(`(${term})`, 'gi');
            
            if (regex.test(text)) {
                const highlightedText = text.replace(regex, '<span class="search-highlight bg-warning">$1</span>');
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = highlightedText;
                
                while (tempDiv.firstChild) {
                    textNode.parentNode.insertBefore(tempDiv.firstChild, textNode);
                }
                textNode.remove();
            }
        });
    }

    function updateSearchResults(count, term) {
        let resultsDiv = document.getElementById('search-results');
        
        if (!resultsDiv) {
            resultsDiv = document.createElement('div');
            resultsDiv.id = 'search-results';
            resultsDiv.className = 'alert alert-info mt-3';
            
            const container = document.querySelector('.container');
            if (container && container.firstChild) {
                container.insertBefore(resultsDiv, container.firstChild.nextSibling);
            }
        }
        
        if (term) {
            resultsDiv.style.display = 'block';
            resultsDiv.innerHTML = `
                <i class="fas fa-search me-2"></i>
                Found ${count} result${count !== 1 ? 's' : ''} for "${term}"
                <button type="button" class="btn-close float-end" onclick="clearSearch()"></button>
            `;
        } else {
            resultsDiv.style.display = 'none';
        }
    }

    // Global clear search function
    window.clearSearch = function() {
        const searchInput = document.querySelector('#searchInput');
        if (searchInput) {
            searchInput.value = '';
        }
        
        // Show all cards
        document.querySelectorAll('.card').forEach(card => {
            card.style.display = '';
        });
        
        // Remove highlights
        document.querySelectorAll('.search-highlight').forEach(highlight => {
            highlight.outerHTML = highlight.innerHTML;
        });
        
        // Hide search results
        const resultsDiv = document.getElementById('search-results');
        if (resultsDiv) {
            resultsDiv.style.display = 'none';
        }
    };

    // Utility function for debouncing
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl+R or F5 - Refresh content
        if ((e.ctrlKey && e.key === 'r') || e.key === 'F5') {
            e.preventDefault();
            refreshContent();
        }
        
        // Escape - Clear search
        if (e.key === 'Escape') {
            clearSearch();
        }
        
        // Ctrl+/ - Focus search
        if (e.ctrlKey && e.key === '/') {
            e.preventDefault();
            const searchInput = document.querySelector('#searchInput');
            if (searchInput) {
                searchInput.focus();
            }
        }
    });

    // Handle online/offline status
    window.addEventListener('online', function() {
        showNotification('Connection restored. Content will auto-refresh.', 'success');
        setTimeout(() => refreshContent(true), 2000);
    });

    window.addEventListener('offline', function() {
        showNotification('Connection lost. Some features may not work.', 'warning');
    });

    // Performance monitoring
    if ('performance' in window) {
        window.addEventListener('load', function() {
            setTimeout(() => {
                const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
                console.log(`Page load time: ${loadTime}ms`);
                
                if (loadTime > 3000) {
                    console.warn('Slow page load detected. Consider optimizing content delivery.');
                }
            }, 0);
        });
    }

})();
