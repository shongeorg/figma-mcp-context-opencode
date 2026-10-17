<div class="container shop">
    <div>
        <aside class="filters" id="filters" aria-label="Product filters">
            <form method="get" action="{{ $filterAction ?? route('shop.index') }}" id="filters-form">
                <div class="filter-block">
                    <h2 class="filter-title">Categories</h2>
                    <ul class="filter-list">
                        <li>
                            <a href="{{ route('shop.index') }}" @unless(request('category')) aria-current="true" @endunless>All Plants</a>
                            <span class="count">({{ $totalProducts ?? 0 }})</span>
                        </li>
                        @foreach($categories ?? [] as $category)
                            <li>
                                <a href="{{ route('shop.index', array_merge(request()->query(), ['category' => $category->slug, 'page' => null])) }}"
                                   @if(request('category') === $category->slug) aria-current="true" @endif>{{ $category->name }}</a>
                                <span class="count">({{ $category->products_count ?? 0 }})</span>
                            </li>
                        @endforeach
                    </ul>
                </div>

                <div class="filter-block">
                    <h2 class="filter-title">Price Range</h2>
                    <div class="range" data-range>
                        <div class="range__track">
                            <span class="range__fill" aria-hidden="true"></span>
                            <input type="range" name="min" min="{{ $priceBounds['min'] ?? 0 }}" max="{{ $priceBounds['max'] ?? 9999 }}" value="{{ request('min', $priceBounds['min'] ?? 0) }}" aria-label="Minimum price">
                            <input type="range" name="max" min="{{ $priceBounds['min'] ?? 0 }}" max="{{ $priceBounds['max'] ?? 9999 }}" value="{{ request('max', $priceBounds['max'] ?? 9999) }}" aria-label="Maximum price">
                        </div>
                        <p class="range__label">Price: <strong data-range-label>${{ request('min', $priceBounds['min'] ?? 0) }} - ${{ request('max', $priceBounds['max'] ?? 9999) }}</strong></p>
                        <button class="btn btn--primary" type="submit">Filter</button>
                    </div>
                </div>

                <div class="filter-block filter-block--size">
                    <h2 class="filter-title">Size</h2>
                    <ul class="filter-list">
                        @foreach(['Small', 'Medium', 'Large'] as $size)
                            <li>
                                <a href="{{ route('shop.index', array_merge(request()->query(), ['size' => $size, 'page' => null])) }}"
                                   @if(request('size') === $size) aria-current="true" @endif>{{ $size }}</a>
                            </li>
                        @endforeach
                    </ul>
                </div>

                <input type="hidden" name="q" value="{{ request('q') }}">
                <input type="hidden" name="category" value="{{ request('category') }}">
                <input type="hidden" name="size" value="{{ request('size') }}">
                <input type="hidden" name="sort" value="{{ request('sort') }}">
                <input type="hidden" name="tab" value="{{ request('tab') }}">
            </form>
        </aside>

        <section class="sale-banner" aria-labelledby="sale-title">
            <h2 class="sale-banner__title" id="sale-title">Super Sale</h2>
            <p class="sale-banner__sub">UP TO 75% OFF</p>
            <div class="sale-banner__media" aria-hidden="true">
                <img src="{{ asset('assets/images/super-sale.png') }}" width="370" height="370" alt="" loading="lazy" decoding="async">
            </div>
        </section>
    </div>

    <nav class="m-tabs" aria-label="Shop sections">
        @foreach(['all' => 'All Plants', 'new' => 'New Arrivals', 'sale' => 'Sale'] as $key => $label)
            <a class="m-tabs__item" href="{{ route('shop.index', array_merge(request()->query(), ['tab' => $key === 'all' ? null : $key, 'page' => null])) }}"
               data-m-tab="{{ $key }}" @if(($tab ?? 'all') === $key) aria-current="true" @endif>{{ $label }}</a>
        @endforeach
    </nav>

    <section aria-labelledby="shop-title">
        <h2 class="visually-hidden" id="shop-title">Shop plants</h2>

        <div class="shop-toolbar">
            <div class="shop-tabs" role="group" aria-label="Filter product list">
                @foreach(['all' => 'All Plants', 'new' => 'New Arrivals', 'sale' => 'Sale'] as $key => $label)
                    <a href="{{ route('shop.index', array_merge(request()->query(), ['tab' => $key === 'all' ? null : $key, 'page' => null])) }}"
                       aria-pressed="{{ ($tab ?? 'all') === $key ? 'true' : 'false' }}">{{ $label }}</a>
                @endforeach
            </div>

            <div class="sort">
                <label for="sort-by">Short by:</label>
                <form method="get" action="{{ $filterAction ?? route('shop.index') }}" style="display: contents">
                    <select class="select" id="sort-by" name="sort" onchange="this.form.submit()">
                        <option value="default" @if(request('sort', 'default') === 'default') selected @endif>Default sorting</option>
                        <option value="price-asc" @if(request('sort') === 'price-asc') selected @endif>Price: low to high</option>
                        <option value="price-desc" @if(request('sort') === 'price-desc') selected @endif>Price: high to low</option>
                        <option value="name" @if(request('sort') === 'name') selected @endif>Name: A–Z</option>
                    </select>
                    @foreach(request()->query() as $key => $value)
                        @if(! in_array($key, ['sort', 'page']))
                            <input type="hidden" name="{{ $key }}" value="{{ $value }}">
                        @endif
                    @endforeach
                </form>
            </div>
        </div>

        @if(($products ?? collect())->isEmpty())
            <p class="empty-state">No plants matched your filters. Try resetting a filter or two.</p>
        @else
            <ul class="product-grid">
                @foreach($products as $product)
                    <x-product-card :product="$product" />
                @endforeach
            </ul>
        @endif

        @if(($products ?? collect())->hasPages())
            <nav class="pagination" aria-label="Pagination">
                @if($products->onFirstPage())
                    <span aria-disabled="true" aria-label="Previous page">‹</span>
                @else
                    <a href="{{ $products->previousPageUrl() }}" aria-label="Previous page">‹</a>
                @endif

                @foreach($products->getUrlRange(max(1, $products->currentPage() - 2), min($products->lastPage(), $products->currentPage() + 2)) as $page => $url)
                    @if($page === $products->currentPage())
                        <span aria-current="page">{{ $page }}</span>
                    @else
                        <a href="{{ $url }}" aria-label="Page {{ $page }}">{{ $page }}</a>
                    @endif
                @endforeach

                @if($products->hasMorePages())
                    <a href="{{ $products->nextPageUrl() }}" aria-label="Next page">
                        <img src="{{ asset('assets/images/icons/arrow-right-outline.svg') }}" width="18" height="18" alt="" loading="lazy">
                    </a>
                @else
                    <span aria-disabled="true" aria-label="Next page">
                        <img src="{{ asset('assets/images/icons/arrow-right-outline.svg') }}" width="18" height="18" alt="" loading="lazy">
                    </span>
                @endif
            </nav>
        @endif
    </section>
</div>
