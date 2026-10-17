<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <title>@yield('title', config('app.name', 'GreenShop'))</title>
    <meta name="description" content="@yield('description', 'GreenShop — online plant shop offering a wide range of cheap and trendy plants.')">

    <link rel="canonical" href="@yield('canonical', url()->current())">

    <meta property="og:type" content="website">
    <meta property="og:site_name" content="{{ config('app.name', 'GreenShop') }}">
    <meta property="og:title" content="@yield('title', config('app.name', 'GreenShop'))">
    <meta property="og:description" content="@yield('description', 'GreenShop — online plant shop offering a wide range of cheap and trendy plants.')">
    <meta property="og:url" content="@yield('canonical', url()->current())">

    <link rel="icon" href="{{ asset('assets/images/logo.svg') }}" type="image/svg+xml">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="preconnect" href="https://images.unsplash.com">
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cera+Pro:wght@400;500;700&family=Poppins:wght@300;400;500;600&display=swap">

    <link rel="stylesheet" href="{{ asset('assets/css/style.css') }}">
    <link rel="stylesheet" href="{{ asset('assets/css/mobile-shell.css') }}">
    <link rel="stylesheet" href="{{ asset('assets/css/mobile-home.css') }}">
    <link rel="stylesheet" href="{{ asset('assets/css/mobile-pdp.css') }}">
    <link rel="stylesheet" href="{{ asset('assets/css/mobile-cart.css') }}">
    <link rel="stylesheet" href="{{ asset('assets/css/mobile-auth.css') }}">
    <link rel="stylesheet" href="{{ asset('assets/css/shop.css') }}">

    <script src="{{ asset('assets/js/main.js') }}" defer></script>
    @stack('head')
</head>
<body>
<a class="skip-link" href="#main">Skip to main content</a>

<header class="site-header">
    <div class="container header-inner">
        <a class="logo" href="{{ route('home') }}">
            <img src="{{ asset('assets/images/logo.svg') }}" width="150" height="35" alt="{{ config('app.name', 'GreenShop') }} — go to the home page">
        </a>

        <nav class="primary-nav" id="primary-nav" aria-label="Primary">
            <ul>
                <li><a href="{{ route('home') }}" @if(request()->routeIs('home')) aria-current="page" @endif>Home</a></li>
                <li><a href="{{ route('shop.index') }}" @if(request()->routeIs('shop.*')) aria-current="page" @endif>Shop</a></li>
                <li><a href="{{ route('home') }}#services">Plant Care</a></li>
                <li><a href="{{ route('home') }}#blog">Blogs</a></li>
            </ul>
        </nav>

        <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="primary-nav">
            <span class="visually-hidden">Menu</span>
            <span></span>
            <span></span>
            <span></span>
        </button>

        <div class="header-actions">
            <button class="icon-btn" type="button" data-search-toggle aria-expanded="false" aria-controls="header-search">
                <img src="{{ asset('assets/images/icons/search.svg') }}" width="20" height="20" alt="">
                <span class="visually-hidden">Search</span>
            </button>

            <a class="cart-link" href="{{ route('cart.index') }}">
                <img src="{{ asset('assets/images/icons/cart.svg') }}" width="24" height="24" alt="">
                @auth
                    <span class="cart-link__badge" aria-hidden="true">{{ $cartCount ?? 0 }}</span>
                    <span class="visually-hidden">Cart, {{ $cartCount ?? 0 }} items</span>
                @else
                    <span class="cart-link__badge" aria-hidden="true">{{ session('cart') ? collect(session('cart'))->sum('quantity') : 0 }}</span>
                    <span class="visually-hidden">Cart</span>
                @endauth
            </a>

            @auth
                <a class="btn btn--primary btn-login" href="{{ route('account.show') }}">
                    <img src="{{ asset('assets/images/icons/icon-logout.svg') }}" width="20" height="20" alt="">
                    <span>{{ auth()->user()->name }}</span>
                </a>
            @else
                <a class="btn btn--primary btn-login" href="{{ route('login') }}" data-dialog="login-dialog">
                    <img src="{{ asset('assets/images/icons/icon-logout.svg') }}" width="20" height="20" alt="">
                    <span>Login</span>
                </a>
            @endauth
        </div>
    </div>

    <div class="header-search container" id="header-search" data-open="false">
        <search>
            <form action="{{ route('shop.index') }}" method="get" role="search">
                <label class="visually-hidden" for="site-search">Search products</label>
                <input class="input" type="search" id="site-search" name="q" value="{{ request('q') }}" placeholder="Search for plants, pots and accessories…" autocomplete="off">
                <button class="btn btn--primary" type="submit">Search</button>
            </form>
        </search>
    </div>
</header>

<main id="main">
    <div class="m-toprow">
        <form class="m-search" role="search" action="{{ route('shop.index') }}" method="get">
            <label class="visually-hidden" for="m-search-input">Find your plants</label>
            <svg class="m-search__icon" viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
                <circle cx="11" cy="11" r="6.4" fill="none" stroke="currentColor" stroke-width="2"/>
                <path d="m16 16 4.2 4.2" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            <input id="m-search-input" type="search" name="q" value="{{ request('q') }}" placeholder="Find your plants" autocomplete="off">
        </form>
        <button class="m-filter" type="button" data-filter-toggle aria-expanded="false" aria-controls="filters" aria-label="Product filters">
            <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
                <path d="M4 8h9M17 8h3M4 16h3M11 16h9" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <circle cx="15" cy="8" r="2.2" fill="none" stroke="currentColor" stroke-width="2"/>
                <circle cx="9" cy="16" r="2.2" fill="none" stroke="currentColor" stroke-width="2"/>
            </svg>
        </button>
    </div>

    @yield('content')
</main>

<footer class="site-footer">
    <div class="container">
        <div class="footer-top" id="services">
            <article class="service">
                <div class="service__icon">
                    <img src="{{ asset('assets/images/icons/svc-garden.png') }}" width="92" height="104" alt="" loading="lazy" decoding="async">
                </div>
                <h2 class="service__title">Garden Care</h2>
                <p class="service__text">We are an online plant shop offering a wide range of cheap and trendy plants.</p>
            </article>

            <article class="service">
                <div class="service__icon">
                    <img src="{{ asset('assets/images/icons/svc-renovation.png') }}" width="92" height="104" alt="" loading="lazy" decoding="async">
                </div>
                <h2 class="service__title">Plant Renovation</h2>
                <p class="service__text">We are an online plant shop offering a wide range of cheap and trendy plants.</p>
            </article>

            <article class="service">
                <div class="service__icon">
                    <img src="{{ asset('assets/images/icons/svc-watering.png') }}" width="96" height="104" alt="" loading="lazy" decoding="async">
                </div>
                <h2 class="service__title">Watering</h2>
                <p class="service__text">We are an online plant shop offering a wide range of cheap and trendy plants.</p>
            </article>

            <div class="newsletter">
                <h2 class="newsletter__title">Would you like to join newsletters?</h2>
                <form class="newsletter__form" data-demo="Thanks for subscribing to our newsletter!">
                    <label class="visually-hidden" for="newsletter-email">Email address</label>
                    <input id="newsletter-email" type="email" name="email" placeholder="enter your email address..." autocomplete="email" required>
                    <button type="submit">Join</button>
                    <p class="form-status" data-status role="status"></p>
                </form>
                <p class="newsletter__text">We usually post offers, tips and tricks and other interesting info on our social media accounts.</p>
            </div>
        </div>

        <div class="footer-contact">
            <a class="logo" href="{{ route('home') }}">
                <img src="{{ asset('assets/images/logo.svg') }}" width="150" height="35" alt="{{ config('app.name', 'GreenShop') }} — go to the home page" loading="lazy">
            </a>
            <p class="contact-item">
                <img src="{{ asset('assets/images/icons/icon-location.svg') }}" width="20" height="20" alt="" loading="lazy">
                <span>70 West Buckingham Ave.<br>Farmingdale, NY 11735</span>
            </p>
            <p class="contact-item">
                <img src="{{ asset('assets/images/icons/icon-message.svg') }}" width="20" height="20" alt="" loading="lazy">
                <a href="mailto:contact@greenshop.com">contact@greenshop.com</a>
            </p>
            <p class="contact-item">
                <img src="{{ asset('assets/images/icons/icon-calling.svg') }}" width="20" height="20" alt="" loading="lazy">
                <a href="tel:+8801911717490">+88 01911 717 490</a>
            </p>
        </div>

        <div class="footer-links">
            <nav class="footer-col" aria-labelledby="footer-account">
                <h2 class="footer-col__title" id="footer-account">My Account</h2>
                <ul>
                    <li><a href="{{ route('account.show') }}">My Account</a></li>
                    <li><a href="{{ route('shop.index') }}">Our stores</a></li>
                    <li><a href="{{ route('account.addresses') }}">Contact us</a></li>
                    <li><a href="{{ route('home') }}#blog">Career</a></li>
                    <li><a href="{{ route('shop.index', ['sort' => 'sale']) }}">Specials</a></li>
                </ul>
            </nav>

            <nav class="footer-col" aria-labelledby="footer-help">
                <h2 class="footer-col__title" id="footer-help">Help &amp; Guide</h2>
                <ul>
                    <li><a href="{{ route('home') }}#services">Help Center</a></li>
                    <li><a href="{{ route('shop.index') }}">How to Buy</a></li>
                    <li><a href="{{ route('checkout.show') }}">Shipping &amp; Delivery</a></li>
                    <li><a href="{{ route('home') }}#services">Product Policy</a></li>
                    <li><a href="{{ route('cart.index') }}">How to Return</a></li>
                </ul>
            </nav>

            <nav class="footer-col" aria-labelledby="footer-categories">
                <h2 class="footer-col__title" id="footer-categories">Categories</h2>
                <ul>
                    @foreach(($footerCategories ?? []) as $category)
                        <li><a href="{{ route('shop.index', ['category' => $category->slug]) }}">{{ $category->name }}</a></li>
                    @endforeach
                </ul>
            </nav>

            <div class="footer-col">
                <h2 class="footer-col__title">Social Media</h2>
                <ul class="social">
                    <li><a href="https://www.instagram.com/" rel="noopener noreferrer" target="_blank"><img src="{{ asset('assets/images/icons/social-instagram.svg') }}" width="20" height="20" alt="Instagram" loading="lazy"></a></li>
                    <li><a href="https://www.facebook.com/" rel="noopener noreferrer" target="_blank"><img src="{{ asset('assets/images/icons/social-facebook.svg') }}" width="20" height="20" alt="Facebook" loading="lazy"></a></li>
                    <li><a href="https://twitter.com/" rel="noopener noreferrer" target="_blank"><img src="{{ asset('assets/images/icons/social-twitter.svg') }}" width="20" height="20" alt="Twitter" loading="lazy"></a></li>
                    <li><a href="https://www.youtube.com/" rel="noopener noreferrer" target="_blank"><img src="{{ asset('assets/images/icons/social-youtube.svg') }}" width="20" height="20" alt="YouTube" loading="lazy"></a></li>
                    <li><a href="https://www.linkedin.com/" rel="noopener noreferrer" target="_blank"><img src="{{ asset('assets/images/icons/social-linkedin.svg') }}" width="20" height="20" alt="LinkedIn" loading="lazy"></a></li>
                </ul>

                <div class="accept">
                    <h3 class="footer-col__title">We accept</h3>
                    <img src="{{ asset('assets/images/payment-methods.png') }}" width="224" height="30" alt="Accepted payment methods" loading="lazy" decoding="async">
                </div>
            </div>
        </div>

        <p class="copyright">Ac 2021 GreenShop. All Rights Reserved.</p>
    </div>
</footer>

@include('partials.auth-dialogs')

<nav class="appbar" aria-label="App">
    <a class="appbar__link" href="{{ route('home') }}">
        <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true"><path d="M4 10.5 12 4l8 6.5V20a1 1 0 0 1-1 1h-4v-6H9v6H5a1 1 0 0 1-1-1z" fill="currentColor"/></svg>
        <span class="visually-hidden">Home</span>
    </a>
    <a class="appbar__link" href="{{ route('shop.index') }}">
        <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true"><path d="M12 20.3 4.6 13a4.6 4.6 0 0 1 6.5-6.5l.9.9.9-.9A4.6 4.6 0 0 1 19.4 13z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>
        <span class="visually-hidden">Wishlist</span>
    </a>
    <span class="appbar__gap" aria-hidden="true"></span>
    <a class="appbar__link" href="{{ route('cart.index') }}">
        <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
            <path d="M3 4h2.2l2.1 10.4a1.6 1.6 0 0 0 1.6 1.3h8.3a1.6 1.6 0 0 0 1.6-1.2L21 7H6.2" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="9.5" cy="19.5" r="1.4" fill="currentColor"/>
            <circle cx="17.5" cy="19.5" r="1.4" fill="currentColor"/>
        </svg>
        <span class="visually-hidden">Cart</span>
    </a>
    <a class="appbar__link" href="{{ route('account.show') }}">
        <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
            <circle cx="12" cy="8" r="3.6" fill="none" stroke="currentColor" stroke-width="1.8"/>
            <path d="M4.8 20c.6-3.7 3.6-5.8 7.2-5.8s6.6 2.1 7.2 5.8" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
        </svg>
        <span class="visually-hidden">My account</span>
    </a>
</nav>

<a class="appbar__fab" href="{{ route('shop.index') }}" aria-label="Find your plants">
    <svg viewBox="0 0 24 24" width="26" height="26" aria-hidden="true">
        <path d="M4 8.5V6a2 2 0 0 1 2-2h2.5M15.5 4H18a2 2 0 0 1 2 2v2.5M20 15.5V18a2 2 0 0 1-2 2h-2.5M8.5 20H6a2 2 0 0 1-2-2v-2.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        <circle cx="12" cy="12" r="3.1" fill="none" stroke="currentColor" stroke-width="2"/>
    </svg>
</a>

<p class="appbar__note" data-appbar-note role="status"></p>
</body>
</html>
