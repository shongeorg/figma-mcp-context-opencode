@props(['product'])

@php
    $mainImage = $product->main_image;
    $discount = $product->discount_percent;
@endphp

<li class="product-card">
    <div class="product-card__media">
        @if($discount)
            <span class="badge">{{ $discount }}% OFF</span>
        @endif

        <a href="{{ route('product.show', $product->slug) }}">
            <img
                src="{{ $mainImage ? Storage::url($mainImage) : asset('assets/images/plant-barberton-daisy.png') }}"
                width="250"
                height="250"
                alt="{{ $product->name }}"
                loading="lazy"
                decoding="async"
            >
        </a>

        <div class="quick-actions">
            <form method="post" action="{{ route('cart.store') }}">
                @csrf
                <input type="hidden" name="product_id" value="{{ $product->id }}">
                <button type="submit">
                    <img src="{{ asset('assets/images/icons/icon-cart.svg') }}" width="20" height="20" alt="">
                    <span class="visually-hidden">Add {{ $product->name }} to cart</span>
                </button>
            </form>
            <a href="{{ route('product.show', $product->slug) }}">
                <img src="{{ asset('assets/images/icons/icon-eye.svg') }}" width="20" height="20" alt="">
                <span class="visually-hidden">View {{ $product->name }}</span>
            </a>
        </div>
    </div>

    <h3 class="product-card__title">
        <a href="{{ route('product.show', $product->slug) }}">{{ $product->name }}</a>
    </h3>

    <p class="product-card__price">
        <span>${{ number_format($product->price, 2) }}</span>
        @if($product->old_price)
            <span class="price--old">${{ number_format($product->old_price, 2) }}</span>
        @endif
    </p>
</li>
