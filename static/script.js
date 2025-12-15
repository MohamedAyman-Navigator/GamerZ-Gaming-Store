// --- GLOBAL VARIABLES ---
let chatHistory = []; // Stores conversation memory for the AI

document.addEventListener("DOMContentLoaded", () => {

    // 1. SMART LOADING ANIMATION (Run once per session)
    const loader = document.getElementById('loader');

    // Check if the user has already seen the intro in this session
    if (sessionStorage.getItem('gamerz_intro_shown')) {
        if (loader) loader.style.display = 'none';
    } else {
        // Play the intro animation
        if (loader) {
            setTimeout(() => {
                loader.style.opacity = '0';
                setTimeout(() => {
                    loader.style.display = 'none';
                    // Set the flag so it doesn't run again
                    sessionStorage.setItem('gamerz_intro_shown', 'true');
                }, 500);
            }, 2000);
        }
    }

    // 2. Custom Cursor Logic
    const cursorDot = document.querySelector('.cursor-dot');
    const cursorOutline = document.querySelector('.cursor-outline');

    window.addEventListener("mousemove", (e) => {
        const posX = e.clientX;
        const posY = e.clientY;
        if (cursorDot) {
            cursorDot.style.left = `${posX}px`;
            cursorDot.style.top = `${posY}px`;
            cursorDot.style.opacity = 1; // Ensure visible on move
        }
        if (cursorOutline) {
            cursorOutline.style.left = `${posX}px`;
            cursorOutline.style.top = `${posY}px`;
            cursorOutline.style.opacity = 1; // Ensure visible on move
        }
    });

    // Hide cursor when leaving the window
    document.addEventListener("mouseout", (e) => {
        if (!e.relatedTarget && !e.toElement) {
            if (cursorDot) cursorDot.style.opacity = 0;
            if (cursorOutline) cursorOutline.style.opacity = 0;
        }
    });

    // 3. Video Play on Hover (Home Page)
    function attachVideoHoverListeners(cards) {
        cards.forEach(card => {
            const video = card.querySelector('video');
            if (!video) return;

            // Remove existing listeners to prevent duplicates if called multiple times (optional safety)
            // But cloning creates new elements so it's fine.

            card.addEventListener('mouseenter', () => {
                video.currentTime = 0;
                video.play().catch(e => console.log("Video play error:", e));
            });
            card.addEventListener('mouseleave', () => {
                video.pause();
            });
        });
    }

    // Initial attachment
    const initialCards = document.querySelectorAll('.game-card');
    attachVideoHoverListeners(initialCards);



    // 4. Horizontal Scroll (Home Page)
    // 4. Horizontal Scroll (Home Page)

    // 5. Light Mode Toggle

    // 6. Hero Carousel Logic
    const slides = document.querySelectorAll('.slide');
    const nextBtn = document.querySelector('.next-btn');
    const prevBtn = document.querySelector('.prev-btn');
    const dotsContainer = document.querySelector('.dot-navigation');

    if (slides.length > 0) {
        let currentSlide = 0;
        const totalSlides = slides.length;

        // Create Dots
        if (dotsContainer) {
            dotsContainer.innerHTML = ''; // Clear existing dots if any
            slides.forEach((_, index) => {
                const dot = document.createElement('div');
                dot.classList.add('dot');
                if (index === 0) dot.classList.add('active');
                dot.addEventListener('click', () => goToSlide(index));
                dotsContainer.appendChild(dot);
            });
        }
        const dots = document.querySelectorAll('.dot');

        function updateDots(index) {
            dots.forEach(dot => dot.classList.remove('active'));
            if (dots[index]) dots[index].classList.add('active');
        }

        function showSlide(index) {
            slides.forEach(slide => slide.classList.remove('active'));
            slides[index].classList.add('active');
            updateDots(index);
        }

        function nextSlide() {
            currentSlide = (currentSlide + 1) % totalSlides;
            showSlide(currentSlide);
        }

        function prevSlide() {
            currentSlide = (currentSlide - 1 + totalSlides) % totalSlides;
            showSlide(currentSlide);
        }

        function goToSlide(index) {
            currentSlide = index;
            showSlide(currentSlide);
        }

        if (nextBtn) nextBtn.addEventListener('click', nextSlide);
        if (prevBtn) prevBtn.addEventListener('click', prevSlide);

        // Auto Play
        let slideInterval = setInterval(nextSlide, 5000);

        // Pause on hover
        const carousel = document.getElementById('hero-carousel');
        if (carousel) {
            carousel.addEventListener('mouseenter', () => clearInterval(slideInterval));
            carousel.addEventListener('mouseleave', () => slideInterval = setInterval(nextSlide, 5000));
        }

        // Initialize first slide
        showSlide(0);
    }

    // 7. Sidebar Category Logic - REMOVED (Handled by direct links to /view_all/<category>)


    // 8. Search Functionality (Floating Window)
    const searchInput = document.getElementById('search-input');
    const searchResults = document.getElementById('search-results');

    // Scrape game data from the DOM
    let gamesData = [];

    // Fetch games from API for global search
    fetch('/api/games')
        .then(response => response.json())
        .then(data => {
            if (Array.isArray(data)) {
                gamesData = data;
                console.log("Loaded " + gamesData.length + " games for search.");
            }
        })
        .catch(error => console.error("Error loading search data:", error));

    if (searchInput && searchResults) {
        searchInput.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            searchResults.innerHTML = ''; // Clear previous results

            if (searchTerm.length === 0) {
                searchResults.classList.remove('show');
                setTimeout(() => {
                    if (!searchResults.classList.contains('show')) {
                        searchResults.style.display = 'none';
                    }
                }, 300); // Wait for animation
                return;
            }

            const filteredGames = gamesData.filter(game =>
                game.title.toLowerCase().includes(searchTerm)
            );

            if (filteredGames.length > 0) {
                filteredGames.forEach((game, index) => {
                    const item = document.createElement('a');
                    item.className = 'search-result-item';
                    item.href = game.link;
                    item.style.animationDelay = `${index * 0.05}s`; // Staggered animation

                    // Highlight logic
                    const regex = new RegExp(`(${searchTerm})`, 'gi');
                    const highlightedTitle = game.title.replace(regex, '<span class="highlight">$1</span>');

                    item.innerHTML = `
                        <img src="${game.image}" class="search-result-img" alt="${game.title}">
                        <div class="search-result-info">
                            <h4>${highlightedTitle}</h4>
                            <p>Click to view details</p>
                        </div>
                    `;
                    searchResults.appendChild(item);
                });
                searchResults.style.display = 'block';
                // Small delay to allow display:block to apply before adding class for transition
                requestAnimationFrame(() => {
                    searchResults.classList.add('show');
                });
            } else {
                searchResults.classList.remove('show');
                setTimeout(() => {
                    if (!searchResults.classList.contains('show')) {
                        searchResults.style.display = 'none';
                    }
                }, 300);
            }
        });

        // Hide results when clicking outside
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
                searchResults.classList.remove('show');
                setTimeout(() => {
                    if (!searchResults.classList.contains('show')) {
                        searchResults.style.display = 'none';
                    }
                }, 300);
            }
        });
    }

    // 11. Media Carousel (Game Details)
    (() => {
        const mediaContainer = document.getElementById('media-carousel');
        if (!mediaContainer) return;

        const slides = mediaContainer.querySelectorAll('.media-slide');
        const prevBtn = mediaContainer.querySelector('.prev-media');
        const nextBtn = mediaContainer.querySelector('.next-media');
        const dotsContainer = mediaContainer.querySelector('.media-dots');
        let currentIndex = 0;
        let slideTimeout;

        if (slides.length === 0) return;

        // Create Dots
        slides.forEach((_, index) => {
            const dot = document.createElement('div');
            dot.className = 'media-dot';
            if (index === 0) {
                dot.classList.add('active');
                slides[index].classList.add('active');
            }
            dot.addEventListener('click', () => goToSlide(index));
            dotsContainer.appendChild(dot);
        });

        const dots = dotsContainer.querySelectorAll('.media-dot');

        function scheduleNextSlide() {
            clearTimeout(slideTimeout);
            const currentSlide = slides[currentIndex];
            const video = currentSlide.querySelector('video');

            if (video) {
                video.loop = false;
                video.onended = () => nextSlide();
            } else {
                slideTimeout = setTimeout(nextSlide, 10000);
            }
        }

        function showSlide(index) {
            // Clean up previous slide
            const prevSlide = slides[currentIndex];
            const prevVid = prevSlide.querySelector('video');
            if (prevVid) {
                prevVid.pause();
                prevVid.onended = null; // Remove listener
            }

            // Setup next slide
            const nextSlideEl = slides[index];
            const nextVid = nextSlideEl.querySelector('video');
            if (nextVid) {
                nextVid.currentTime = 0;
                nextVid.play().catch(() => { });
            }

            // Update Classes
            slides.forEach(s => s.classList.remove('active'));
            nextSlideEl.classList.add('active');

            dots.forEach(d => d.classList.remove('active'));
            if (dots[index]) dots[index].classList.add('active');

            currentIndex = index;

            // Conditional Arrows
            if (prevBtn) prevBtn.style.display = (currentIndex === 0) ? 'none' : 'block';
            if (nextBtn) nextBtn.style.display = (currentIndex === slides.length - 1) ? 'none' : 'block';

            // Schedule next move
            scheduleNextSlide();
        }

        function nextSlide() {
            const newIndex = (currentIndex + 1) % slides.length;
            showSlide(newIndex);
        }

        function prevSlide() {
            const newIndex = (currentIndex - 1 + slides.length) % slides.length;
            showSlide(newIndex);
        }

        function goToSlide(i) {
            showSlide(i);
        }

        if (nextBtn) nextBtn.addEventListener('click', nextSlide);
        if (prevBtn) prevBtn.addEventListener('click', prevSlide);

        // Hover Logic: Pause timer for images only
        mediaContainer.addEventListener('mouseenter', () => {
            if (!slides[currentIndex].querySelector('video')) {
                clearTimeout(slideTimeout);
            }
        });

        mediaContainer.addEventListener('mouseleave', () => {
            if (!slides[currentIndex].querySelector('video')) {
                scheduleNextSlide();
            }
        });

        // Initialize
        showSlide(0);

    })();
}); // <--- FINAL CLOSING BRACE FOR DOMContentLoaded


// 6. CHATBOT FUNCTIONS (Memory & API)
// ===========================================

// Chat History (Reset on page load)
chatHistory = [];

function toggleChat() {
    const chatWindow = document.getElementById('chatWindow');
    if (chatWindow.style.display === 'flex') {
        // Close with animation
        chatWindow.classList.add('closing');
        setTimeout(() => {
            chatWindow.style.display = 'none';
            chatWindow.classList.remove('closing');
        }, 300);
    } else {
        chatWindow.style.display = 'flex';
    }
}

function handleEnter(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

async function sendMessage() {
    const inputField = document.getElementById('userInput');
    const chatBody = document.getElementById('chatBody');
    const message = inputField.value.trim();

    if (message === "") return;

    // 1. Add User Message to UI
    chatBody.innerHTML += `<div class="user-message">${message}</div>`;
    inputField.value = "";
    chatBody.scrollTop = chatBody.scrollHeight;

    // 2. Show Loading
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'bot-message';
    loadingDiv.innerText = 'Thinking...';
    loadingDiv.id = 'loadingMsg';
    chatBody.appendChild(loadingDiv);

    try {
        // 3. Send Message AND History to Flask Backend
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                history: chatHistory
            })
        });

        const data = await response.json();

        // 4. Remove Loading
        document.getElementById('loadingMsg').remove();

        // 5. Add Bot Response to UI
        let botText = data.reply
            .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>') // Bold
            .replace(/\n/g, '<br>'); // Line breaks
        chatBody.innerHTML += `<div class="bot-message">${botText}</div>`;

        // 6. UPDATE HISTORY MEMORY
        chatHistory.push({ role: "user", parts: [{ text: message }] });
        chatHistory.push({ role: "model", parts: [{ text: data.reply }] });

        // 7. SAVE TO SESSION STORAGE

    } catch (error) {
        if (document.getElementById('loadingMsg')) document.getElementById('loadingMsg').remove();
        chatBody.innerHTML += `<div class="bot-message" style="color:red;">Connection Error.</div>`;
    }

    chatBody.scrollTop = chatBody.scrollHeight;
}


// ===========================================
// --- 6.5. SCROLL ARROW LOGIC ---
// ===========================================
document.addEventListener('DOMContentLoaded', () => {
    const scrollWrappers = document.querySelectorAll('.scroll-wrapper');

    scrollWrappers.forEach(wrapper => {
        const container = wrapper.querySelector('.scroll-container');
        const leftArrow = wrapper.querySelector('.left-arrow');
        const rightArrow = wrapper.querySelector('.right-arrow');

        if (!container || !leftArrow || !rightArrow) return;

        // Scroll Amount
        const scrollAmount = 400;

        // Click Handlers
        leftArrow.addEventListener('click', () => {
            container.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
        });

        rightArrow.addEventListener('click', () => {
            container.scrollBy({ left: scrollAmount, behavior: 'smooth' });
        });

        // Visibility Logic
        function updateArrows() {
            // Left Arrow: Show if scrolled > 0
            if (container.scrollLeft > 10) {
                leftArrow.classList.add('visible');
            } else {
                leftArrow.classList.remove('visible');
            }

            // Right Arrow: Show if not at end
            // Tolerance of 10px for float calculation errors
            if (container.scrollLeft + container.clientWidth < container.scrollWidth - 10) {
                rightArrow.classList.add('visible');
            } else {
                rightArrow.classList.remove('visible');
            }
        }

        // Initial Check
        // Use setTimeout to allow layout to stabilize (images loading etc)
        setTimeout(updateArrows, 100);
        setTimeout(updateArrows, 1000); // Double check

        // Scroll Listener
        container.addEventListener('scroll', updateArrows);

        // Resize Listener
        window.addEventListener('resize', updateArrows);
    });
});


// ===========================================
// --- 7. SHOPPING CART FUNCTIONS ---
// ===========================================

function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast-notification';
    toast.innerText = message;
    document.body.appendChild(toast);

    setTimeout(() => toast.classList.add('show'), 100);

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function updateCartCounter(count) {
    const badge = document.getElementById('cart-count');
    if (badge) {
        badge.innerText = count;
        badge.style.display = count > 0 ? 'flex' : 'none';
        badge.style.transform = 'scale(1.5)';
        setTimeout(() => badge.style.transform = 'scale(1)', 200);
    }
}

async function addToCart(gameId) {
    const numericId = Number(gameId);

    try {
        const response = await fetch('/add_to_cart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ game_id: numericId })
        });

        const data = await response.json();

        if (data.status === 'success') {
            showToast("Game Added to Cart! 🛒");
            updateCartCounter(data.cart_count);
        } else if (data.status === 'exists') {
            showToast("Item is already in cart!");
        }

    } catch (error) {
        console.error('Error adding to cart:', error);
        showToast("Error: Could not add item.");
    }
}
// <--- END OF FILE (No missing braces here now)
// 9. Cart Item Removal Animation
function removeItem(event, gameId) {
    event.preventDefault(); // Stop immediate navigation
    const row = event.target.closest('tr'); // Find the table row
    const tbody = row ? row.parentElement : null;
    const table = row ? row.closest('table') : null;

    if (row && tbody && table) {
        // Check if it's the last item
        if (tbody.children.length === 1) {
            table.classList.add('fade-out'); // Fade out the whole table
        } else {
            row.classList.add('fade-out'); // Fade out just the row
        }

        // Wait for animation to finish (0.5s) then navigate
        setTimeout(() => {
            window.location.href = '/remove_from_cart/' + gameId;
        }, 500);
    } else {
        // Fallback if row not found
        window.location.href = '/remove_from_cart/' + gameId;
    }
}

// 10. Light Mode Toggle
document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('themeToggle');
    const body = document.body;

    // Check local storage - Apply theme regardless of toggle button existence
    if (localStorage.getItem('theme') === 'light') {
        body.classList.add('light-mode');
        if (themeToggle) {
            const icon = themeToggle.querySelector('i');
            if (icon) {
                icon.classList.remove('fa-fire-flame-curved');
                icon.classList.add('fa-fire');
            }
        }
    }

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            body.classList.toggle('light-mode');
            const icon = themeToggle.querySelector('i');

            if (body.classList.contains('light-mode')) {
                localStorage.setItem('theme', 'light');
                if (icon) {
                    icon.classList.remove('fa-fire-flame-curved');
                    icon.classList.add('fa-fire');
                    themeToggle.style.color = '#555';
                }
            } else {
                localStorage.setItem('theme', 'dark');
                if (icon) {
                    icon.classList.remove('fa-fire');
                    icon.classList.add('fa-fire-flame-curved');
                    themeToggle.style.color = '#ffaa00';
                }
            }
        });
    }

    // 11. Category Filtering - REMOVED (Handled by direct links)

});

// 8. CLOSE CHATBOT ON OUTSIDE CLICK
document.addEventListener('click', (event) => {
    const chatWindow = document.getElementById('chatWindow');
    const chatIcon = document.querySelector('.chatbot-icon');

    // Check if elements exist and chat is open
    if (chatWindow && chatWindow.style.display === 'flex') {
        // If click is NOT inside chat window AND NOT on the toggle icon
        if (!chatWindow.contains(event.target) && !chatIcon.contains(event.target)) {
            // Close with animation
            chatWindow.classList.add('closing');
            setTimeout(() => {
                chatWindow.style.display = 'none';
                chatWindow.classList.remove('closing');
            }, 300);
        }
    }
});

// 9. PAGE TRANSITIONS
document.addEventListener('DOMContentLoaded', () => {
    document.body.addEventListener('click', (e) => {
        const link = e.target.closest('a');
        if (!link) return;

        const href = link.getAttribute('href');
        // Ignore anchors, JS links, blank targets, or if already exiting
        if (!href || href.startsWith('#') || href.startsWith('javascript:') || link.target === '_blank' || document.body.classList.contains('page-exit')) return;

        e.preventDefault();
        document.body.classList.add('page-exit');

        setTimeout(() => {
            window.location.href = href;
        }, 300); // Match CSS animation duration
    });

    // Handle back button cache restoration (Safari/Firefox bfcache)
    window.addEventListener('pageshow', (event) => {
        if (event.persisted) {
            document.body.classList.remove('page-exit');
        }
    });
});

// 12. SCROLL FADE-IN ANIMATION
function initScrollAnimation() {
    const observerOptions = {
        root: null,
        rootMargin: '0px 0px -50px 0px', // Trigger slightly later (50px from bottom)
        threshold: 0.15 // Require 15% visibility
    };

    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-visible');
            } else {
                entry.target.classList.remove('is-visible');
            }
        });
    }, observerOptions);

    const hiddenElements = document.querySelectorAll('.game-card, .section-header, .hero-content');
    hiddenElements.forEach((el) => observer.observe(el));

    // Game Hover Popup Logic (Moved outside observer to run ONCE)
    const popup = document.getElementById('game-hover-popup');
    if (!popup) return; // Guard clause

    const popupTitle = popup.querySelector('.popup-title');
    const popupRelease = popup.querySelector('.popup-release');
    const popupVideo = popup.querySelector('.popup-video');
    const popupImage = popup.querySelector('.popup-image');
    const popupRating = popup.querySelector('.popup-rating');
    const popupGenre = popup.querySelector('.popup-genre');
    const popupDescription = popup.querySelector('.popup-description');

    let hoverTimeout;

    document.querySelectorAll('.game-card').forEach(card => {
        card.addEventListener('mouseenter', (e) => {
            hoverTimeout = setTimeout(() => {
                const rect = card.getBoundingClientRect();
                const data = card.dataset;

                // Populate Data
                popupTitle.textContent = data.title;
                popupRelease.textContent = data.release || 'TBD';
                popupRating.textContent = data.rating ? `★ ${data.rating}` : '';
                popupGenre.textContent = data.genre;
                popupDescription.textContent = data.description || 'No description available.';

                // Mark card as hovered
                card.isHovered = true;

                // Media Handling
                let slideshowInterval;

                // Use landscape image if available, otherwise fallback to vertical cover
                const displayImage = data.landscape && data.landscape !== 'None' ? data.landscape : data.image;

                // Reset media state
                popupVideo.style.display = 'none';
                popupImage.style.display = 'none';
                popupVideo.pause();
                popupVideo.currentTime = 0;

                console.log('Popup Data:', {
                    id: data.id,
                    trailer: data.trailer,
                    image: data.image,
                    landscape: data.landscape,
                    displayImage: displayImage
                });

                if (data.trailer && data.trailer !== 'None' && data.trailer !== '') {
                    console.log('Attempting to play trailer:', data.trailer);
                    popupVideo.style.display = 'block';
                    popupVideo.src = '';
                    popupVideo.src = data.trailer;
                    popupVideo.load();

                    const playPromise = popupVideo.play();
                    if (playPromise !== undefined) {
                        playPromise.catch(error => {
                            console.log('Auto-play prevented, falling back to screenshots:', error);
                            if (card.isHovered) startScreenshotSlideshow(data.id, displayImage);
                        });
                    }
                } else {
                    console.log('No trailer, starting slideshow');
                    startScreenshotSlideshow(data.id, displayImage);
                }

                function startScreenshotSlideshow(gameId, defaultImage) {
                    if (!card.isHovered) return;

                    console.log('Starting slideshow for Game ID:', gameId);
                    popupVideo.style.display = 'none';
                    popupImage.style.display = 'block';
                    popupImage.style.opacity = 1;
                    popupImage.src = defaultImage; // Show cover immediately

                    // Fetch screenshots
                    fetch(`/api/game/${gameId}/screenshots`)
                        .then(response => {
                            console.log('API Response Status:', response.status);
                            return response.json();
                        })
                        .then(screenshots => {
                            if (!card.isHovered) return; // Stop if user left

                            console.log('Fetched Screenshots:', screenshots);
                            if (screenshots && screenshots.length > 0) {
                                let currentIndex = 0;
                                // Add default image to rotation
                                const allImages = [defaultImage, ...screenshots];

                                // Clear any existing interval
                                if (card.slideshowInterval) clearInterval(card.slideshowInterval);

                                card.slideshowInterval = setInterval(() => {
                                    if (!card.isHovered) {
                                        clearInterval(card.slideshowInterval);
                                        return;
                                    }

                                    // Fade Out
                                    popupImage.style.opacity = 0;

                                    setTimeout(() => {
                                        if (!card.isHovered) return;

                                        currentIndex = (currentIndex + 1) % allImages.length;
                                        console.log('Switching to image:', allImages[currentIndex]);

                                        // Create a temporary image to preload
                                        const tempImg = new Image();
                                        tempImg.src = allImages[currentIndex];

                                        tempImg.onload = () => {
                                            if (!card.isHovered) return;
                                            popupImage.src = allImages[currentIndex];
                                            // Slight delay to ensure DOM update
                                            requestAnimationFrame(() => {
                                                popupImage.style.opacity = 1;
                                            });
                                        };
                                    }, 500); // Wait longer than transition (400ms) to ensure full fade out

                                }, 3000); // Slightly longer interval
                            } else {
                                console.log('No screenshots found, sticking to default image');
                            }
                        })
                        .catch(err => console.error('Error fetching screenshots:', err));
                }

                // Store interval on card to clear it later
                card.slideshowInterval = slideshowInterval;



                // Positioning
                let left = rect.right + 15; // More spacing
                let top = rect.top;

                // Check right edge (Width increased to 380px)
                if (left + 400 > window.innerWidth) {
                    left = rect.left - 400; // Show on left if no space on right
                }

                // Check bottom edge (Height increased)
                if (top + 500 > window.innerHeight) {
                    top = window.innerHeight - 520;
                }

                popup.style.left = `${left}px`;
                popup.style.top = `${top}px`;
                popup.classList.add('active');
            }, 500); // 500ms delay
        });

        card.addEventListener('mouseleave', () => {
            clearTimeout(hoverTimeout);
            card.isHovered = false; // Mark as not hovered

            // Clear slideshow interval
            if (card.slideshowInterval) {
                clearInterval(card.slideshowInterval);
                card.slideshowInterval = null;
            }

            popup.classList.remove('active');
            popupVideo.pause();
            popupVideo.currentTime = 0;
        });
    });

    // Elements to animate
    const targets = document.querySelectorAll(
        'section, .game-card, .details-container, .auth-box, .cart-container, .profile-container, .extras-category, .hero-section, .form-container, .success-container, .stat-card, .library-card, .extra-card, .games-table tbody tr'
    );

    console.log("Scroll Animation Targets Found:", targets.length);

    targets.forEach(target => {
        target.classList.add('fade-in-section');
        // Small delay to ensure the browser registers the initial hidden state
        // before the observer potentially triggers 'is-visible'
        setTimeout(() => {
            observer.observe(target);
        }, 100);
    });
}

// Run immediately if DOM is ready, otherwise wait
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initScrollAnimation);
} else {
    initScrollAnimation();
}