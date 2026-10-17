@extends('layouts.app')

@section('title', 'GreenShop — plants for your urban jungle')
@section('description', 'Buy cheap and trendy plants online. House plants, seeds, accessories and more with fast delivery.')

@section('content')
    @include('partials.hero')
    @include('partials.catalog')

    <section class="promo container" aria-label="Featured collections">
        <article class="promo-card">
            <div class="promo-card__media" aria-hidden="true">
                <img src="{{ asset('assets/images/promo-left.png') }}" width="430" height="250" alt="" loading="lazy" decoding="async">
            </div>
            <div class="promo-card__body">
                <h2 class="promo-card__title">Summer cactus<br>&amp; succulents</h2>
                <p class="promo-card__text">We are an online plant shop offering a wide range of cheap and trendy plants.</p>
                <a class="btn btn--primary" href="{{ route('shop.index', ['category' => 'succulents']) }}">Shop Now</a>
            </div>
        </article>

        <article class="promo-card">
            <div class="promo-card__media" aria-hidden="true">
                <img src="{{ asset('assets/images/promo-right.png') }}" width="430" height="250" alt="" loading="lazy" decoding="async">
            </div>
            <div class="promo-card__body">
                <h2 class="promo-card__title">Styling Trends<br>&amp; much more</h2>
                <p class="promo-card__text">We are an online plant shop offering a wide range of cheap and trendy plants.</p>
                <a class="btn btn--primary" href="{{ route('shop.index', ['sort' => 'name']) }}">Shop Now</a>
            </div>
        </article>
    </section>

    <section class="blog container" id="blog" aria-labelledby="blog-title">
        <h2 class="section-title" id="blog-title">Our Blog Posts</h2>
        <p class="blog__lead">We are an online plant shop offering a wide range of cheap and trendy plants.</p>

        <div class="blog-grid">
            <article class="blog-card">
                <a class="blog-card__media" href="#blog" tabindex="-1" aria-hidden="true">
                    <img src="{{ asset('assets/images/blog-1.png') }}" width="400" height="250" alt="" loading="lazy" decoding="async">
                </a>
                <div class="blog-card__body">
                    <p class="blog-card__meta">September 12 I Read in 6 minutes</p>
                    <h3 class="blog-card__title"><a href="#blog">Cactus &amp; Succulent Care Tips</a></h3>
                    <p class="blog-card__text">Cacti are succulent plants that require a very distinct set of care conditions to grow and thrive.</p>
                    <a class="blog-card__more" href="#blog">Read More</a>
                </div>
            </article>

            <article class="blog-card">
                <a class="blog-card__media" href="#blog" tabindex="-1" aria-hidden="true">
                    <img src="{{ asset('assets/images/blog-2.png') }}" width="400" height="250" alt="" loading="lazy" decoding="async">
                </a>
                <div class="blog-card__body">
                    <p class="blog-card__meta">September 12 I Read in 6 minutes</p>
                    <h3 class="blog-card__title"><a href="#blog">Botanical Prints Now Available</a></h3>
                    <p class="blog-card__text">We are excited to announce that botanical prints are now available in our shop.</p>
                    <a class="blog-card__more" href="#blog">Read More</a>
                </div>
            </article>

            <article class="blog-card">
                <a class="blog-card__media" href="#blog" tabindex="-1" aria-hidden="true">
                    <img src="{{ asset('assets/images/blog-3.png') }}" width="400" height="250" alt="" loading="lazy" decoding="async">
                </a>
                <div class="blog-card__body">
                    <p class="blog-card__meta">September 12 I Read in 6 minutes</p>
                    <h3 class="blog-card__title"><a href="#blog">Grow Carefully: A Field Guide</a></h3>
                    <p class="blog-card__text">A field guide to growing plants carefully, from seed selection to harvesting.</p>
                    <a class="blog-card__more" href="#blog">Read More</a>
                </div>
            </article>
        </div>
    </section>
@endsection
