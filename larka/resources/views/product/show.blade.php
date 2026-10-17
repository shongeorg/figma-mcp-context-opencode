@extends('layouts.app')

@section('title', $product->name.' — GreenShop')
@section('description', \Illuminate\Support\Str::limit(strip_tags($product->short_description ?? $product->description ?? $product->name), 155))

@section('content')
    <div class="container">
        <div class="m-topbar m-topbar--media">
            <a class="m-topbar__btn" href="{{ route('shop.index') }}" aria-label="Back to shop">
                <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
                    <path d="m14.5 5-6 7 6 7" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </a>
        </div>

        <nav class="breadcrumb" aria-label="Breadcrumb">
            <a href="{{ route('home') }}">Home</a> <span aria-hidden="true">/</span>
            <a href="{{ route('shop.index') }}">Shop</a> <span aria-hidden="true">/</span>
            <span aria-current="page">{{ $product->name }}</span>
        </nav>

        <div class="product">
            <div class="gallery" data-gallery>
                <div class="gallery__thumbs" role="tablist" aria-label="Product images">
                    @foreach($images as $index => $image)
                        <button type="button" role="tab" aria-selected="{{ $index === 0 ? 'true' : 'false' }}" tabindex="{{ $index === 0 ? 0 : -1 }}" data-gallery-thumb>
                            <img src="{{ Storage::url($image->path) }}" width="100" height="100" data-full="{{ Storage::url($image->path) }}" alt="{{ $product->name }} view {{ $index + 1 }}">
                        </button>
                    @endforeach
                </div>

                <div class="gallery__main">
                    <img src="{{ $images->first() ? Storage::url($images->first()->path) : asset('assets/images/plant-barberton-daisy.png') }}"
                         width="444" height="444" alt="{{ $product->name }}" fetchpriority="high" decoding="async" data-gallery-main>
                </div>
            </div>

            <div class="product-info">
                <h1 class="product-info__title">{{ $product->name }}</h1>

                <p class="score-chip">
                    <span class="score-chip__star" aria-hidden="true">&#9733;</span>
                    <strong>{{ number_format($product->rating, 1) }}</strong> <span class="score-chip__count">({{ $product->reviews_count }})</span>
                    <span class="visually-hidden">rated {{ number_format($product->rating, 1) }} out of 5 from {{ $product->reviews_count }} reviews</span>
                </p>

                <div class="product-info__row">
                    <p class="product-info__price">
                        ${{ number_format($product->price, 2) }}
                        @if($product->old_price)
                            <span class="price--old">${{ number_format($product->old_price, 2) }}</span>
                        @endif
                    </p>
                    <p class="rating">
                        <span class="rating__stars">
                            @for($i = 1; $i <= 5; $i++)
                                <img src="{{ asset('assets/images/icons/icon-star.svg') }}" width="16" height="16" alt="" @if($i > round($product->rating)) class="is-off" @endif>
                            @endfor
                        </span>
                        <a href="#tab-rev">Review</a>
                    </p>
                </div>

                <hr>

                <div class="product-info__block">
                    <p class="product-info__label">Description</p>
                    <p class="product-info__text">{{ $product->short_description }}</p>
                </div>

                @if($product->sizes)
                    <div class="product-info__block">
                        <p class="product-info__label">Size</p>
                        <div class="sizes" data-press-group>
                            @foreach($product->sizes as $index => $size)
                                <button type="button" aria-pressed="{{ $index === 0 ? 'true' : 'false' }}" data-size value="{{ $size }}">{{ $size }}</button>
                            @endforeach
                        </div>
                    </div>
                @endif

                <form class="buy-row" method="post" action="{{ route('cart.store') }}" id="buy-form">
                    @csrf
                    <input type="hidden" name="product_id" value="{{ $product->id }}">
                    <input type="hidden" name="size" id="selected-size" value="{{ $product->sizes[0] ?? '' }}">
                    <input type="hidden" name="redirect" value="1">

                    <span class="buy-row__qty" aria-hidden="true">Qty</span>
                    <div class="stepper" data-stepper>
                        <button type="button" data-step="-1" aria-label="Decrease quantity">&minus;</button>
                        <input type="number" name="quantity" value="1" min="1" max="{{ max(1, $product->stock) }}" aria-label="Quantity">
                        <button type="button" data-step="1" aria-label="Increase quantity">+</button>
                    </div>

                    <p class="buy-row__price">${{ number_format($product->price, 2) }}</p>

                    <button class="btn btn--primary" type="submit">
                        <span class="lbl--wide">Add to cart</span>
                        <span class="lbl--narrow">Buy Now</span>
                    </button>

                    <a class="buy-row__cart" href="{{ route('cart.index') }}" aria-label="Go to cart">
                        <img src="{{ asset('assets/images/icons/icon-cart.svg') }}" width="24" height="24" alt="">
                    </a>
                </form>

                <div class="meta">
                    <p><span>SKU:</span> {{ $product->sku }}</p>
                    <p><span>Category:</span> <a href="{{ route('shop.index', ['category' => $product->category->slug]) }}">{{ $product->category->name }}</a></p>
                    <p><span>Stock:</span> {{ $product->stock > 0 ? $product->stock.' in stock' : 'Out of stock' }}</p>
                </div>

                <p class="share">
                    <span>Share:</span>
                    <a href="https://www.facebook.com/" rel="noopener noreferrer" target="_blank"><img src="{{ asset('assets/images/icons/social-facebook.svg') }}" width="18" height="18" alt="Share on Facebook"></a>
                    <a href="https://www.linkedin.com/" rel="noopener noreferrer" target="_blank"><img src="{{ asset('assets/images/icons/social-linkedin.svg') }}" width="18" height="18" alt="Share on LinkedIn"></a>
                    <a href="https://twitter.com/" rel="noopener noreferrer" target="_blank"><img src="{{ asset('assets/images/icons/social-twitter.svg') }}" width="18" height="18" alt="Share on Twitter"></a>
                    <a href="https://www.youtube.com/" rel="noopener noreferrer" target="_blank"><img src="{{ asset('assets/images/icons/social-youtube.svg') }}" width="18" height="18" alt="Share on YouTube"></a>
                </p>
            </div>
        </div>

        <section class="tabs" data-tabs aria-label="Product information">
            <div class="tabs__list" role="tablist">
                <button type="button" role="tab" id="tab-desc" aria-controls="panel-desc" aria-selected="true">Product Description</button>
                <button type="button" role="tab" id="tab-rev" aria-controls="panel-rev" aria-selected="false" tabindex="-1">Reviews ({{ $reviews->count() }})</button>
                @auth
                    <button type="button" role="tab" id="tab-add" aria-controls="panel-add" aria-selected="false" tabindex="-1">Add a Review</button>
                @endauth
            </div>

            <div class="tabs__panel" id="panel-desc" role="tabpanel" aria-labelledby="tab-desc" tabindex="0">
                {!! nl2br(e($product->description ?? $product->short_description)) !!}
            </div>

            <div class="tabs__panel" id="panel-rev" role="tabpanel" aria-labelledby="tab-rev" tabindex="0" hidden>
                @if($reviews->isEmpty())
                    <p>There are no reviews yet. Be the first to review &ldquo;{{ $product->name }}&rdquo;.</p>
                @else
                    @foreach($reviews as $review)
                        <article class="review-item">
                            <p><strong>{{ $review->user->name }}</strong> — {{ $review->rating }}/5 · {{ $review->created_at->diffForHumans() }}</p>
                            <p>{{ $review->body }}</p>
                        </article>
                    @endforeach
                @endif
            </div>

            @auth
                <div class="tabs__panel" id="panel-add" role="tabpanel" aria-labelledby="tab-add" tabindex="0" hidden>
                    <form method="post" action="{{ route('reviews.store', $product) }}">
                        @csrf
                        <label class="visually-hidden" for="review-rating">Rating</label>
                        <select class="select" id="review-rating" name="rating" required>
                            @for($i = 5; $i >= 1; $i--)
                                <option value="{{ $i }}">{{ $i }} star{{ $i > 1 ? 's' : '' }}</option>
                            @endfor
                        </select>

                        <label class="visually-hidden" for="review-body">Your review</label>
                        <textarea class="textarea" id="review-body" name="body" rows="5" required></textarea>

                        <button class="btn btn--primary" type="submit">Submit review</button>
                    </form>
                </div>
            @endauth
        </section>

        @if($related->isNotEmpty())
            <section class="related" aria-labelledby="related-title">
                <h2 class="related__title" id="related-title">Related products</h2>
                <hr>
                <div class="related-grid">
                    @foreach($related as $item)
                        <a class="mini-card" href="{{ route('product.show', $item->slug) }}">
                            <span class="mini-card__media">
                                <img src="{{ $item->main_image ? Storage::url($item->main_image) : asset('assets/images/plant-chinese-evergreen.png') }}" width="219" height="255" alt="{{ $item->name }}" loading="lazy" decoding="async">
                            </span>
                            <span class="mini-card__title">{{ $item->name }}</span>
                            <span class="mini-card__price">${{ number_format($item->price, 2) }}</span>
                        </a>
                    @endforeach
                </div>
            </section>
        @endif
    </div>
@endsection

@push('head')
    <script>
        document.addEventListener('click', function (event) {
            const chip = event.target.closest('[data-size]');

            if (!chip) {
                return;
            }

            document.querySelectorAll('[data-size]').forEach(function (button) {
                button.setAttribute('aria-pressed', button === chip ? 'true' : 'false');
            });

            document.getElementById('selected-size').value = chip.value;
        });
    </script>
@endpush
