<section class="hero container" aria-labelledby="hero-title">
    <div class="hero__bg">
        <div class="hero__content">
            <p class="eyebrow">Welcome to GreenShop</p>
            <h1 class="hero__title" id="hero-title">Let's Make a<br>Better <span class="accent">Planet</span></h1>
            <p class="hero__text">
                We are an online plant shop offering a wide range of cheap and trendy
                plants. Use our plants to create an unique Urban Jungle. Order your
                favorite plants!
            </p>
            <p class="hero__cta">
                <a class="btn btn--primary" href="{{ route('shop.index') }}">SHOP NOW</a>
            </p>
        </div>

        <div class="hero__media" aria-hidden="true">
            <img src="{{ asset('assets/images/hero-plant.png') }}" width="518" height="518" alt="" fetchpriority="high" decoding="async">
        </div>
        <div class="hero__media hero__media--thumb" aria-hidden="true">
            <img src="{{ asset('assets/images/hero-plant-small.png') }}" width="135" height="135" alt="" decoding="async">
        </div>

        <div class="hero__dots">
            <img src="{{ asset('assets/images/icons/banner-dots.svg') }}" width="40" height="8" alt="" decoding="async">
        </div>
    </div>
</section>
