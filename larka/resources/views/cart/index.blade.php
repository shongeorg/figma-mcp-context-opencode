@extends('layouts.app')

@section('title', 'Shopping Cart — GreenShop')
@section('description', 'Review the plants in your shopping cart, apply a coupon and proceed to checkout.')

@section('content')
    <div class="container">
        <div class="m-topbar">
            <a class="m-topbar__btn" href="{{ route('shop.index') }}" aria-label="Back to shop">
                <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
                    <path d="m14.5 5-6 7 6 7" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </a>
            <p class="m-topbar__title" aria-hidden="true">Cart</p>
            <span class="m-topbar__spacer" aria-hidden="true"></span>
        </div>

        <h1 class="visually-hidden">Shopping Cart</h1>

        <nav class="breadcrumb" aria-label="Breadcrumb">
            <a href="{{ route('home') }}">Home</a> <span aria-hidden="true">/</span>
            <a href="{{ route('shop.index') }}">Shop</a> <span aria-hidden="true">/</span>
            <span aria-current="page">Shopping Cart</span>
        </nav>

        @if(session('status'))
            <p class="form-status" role="status">{{ session('status') }}</p>
        @endif

        @if($lines->isEmpty())
            <p class="empty-state">Your cart is empty. <a href="{{ route('shop.index') }}">Continue shopping</a> to pick some plants.</p>
        @else
            <div class="cart-layout">
                <div>
                    <table class="cart-table" aria-label="Products in your shopping cart">
                        <thead>
                            <tr>
                                <th scope="col" class="col-product">Products</th>
                                <th scope="col" class="col-price">Price</th>
                                <th scope="col" class="col-qty">Quantity</th>
                                <th scope="col" class="col-total">Total</th>
                                <th scope="col" class="col-remove"><span class="visually-hidden">Remove</span></th>
                            </tr>
                        </thead>
                        <tbody>
                            @foreach($lines as $line)
                                <tr>
                                    <td class="col-product">
                                        <div class="cart-item">
                                            <span class="cart-item__media">
                                                <img src="{{ $line['product']->main_image ? Storage::url($line['product']->main_image) : asset('assets/images/plant-barberton-daisy.png') }}" width="70" height="70" alt="{{ $line['product']->name }}" loading="lazy">
                                            </span>
                                            <span class="cart-item__body">
                                                <span class="cart-item__name"><a href="{{ route('product.show', $line['product']->slug) }}">{{ $line['product']->name }}</a></span>
                                                <span class="cart-item__sku">SKU: <span>{{ $line['product']->sku }}</span></span>
                                                @if($line['size'] !== '')
                                                    <span class="cart-item__size">Size : <b>{{ $line['size'] }}</b></span>
                                                @endif
                                            </span>
                                        </div>
                                    </td>

                                    <td class="col-price" data-label="Price">
                                        <span class="cell-price">${{ number_format($line['product']->price, 2) }}</span>
                                    </td>

                                    <td class="col-qty" data-label="Quantity">
                                        <form method="post" action="{{ route('cart.update') }}">
                                            @csrf
                                            <input type="hidden" name="product_id" value="{{ $line['product']->id }}">
                                            <input type="hidden" name="size" value="{{ $line['size'] }}">

                                            <div class="stepper stepper--sm" data-stepper>
                                                <button type="button" data-step="-1" aria-label="Decrease quantity of {{ $line['product']->name }}">&minus;</button>
                                                <input type="number" name="quantity" value="{{ $line['quantity'] }}" min="0" max="999" aria-label="Quantity of {{ $line['product']->name }}">
                                                <button type="button" data-step="1" aria-label="Increase quantity of {{ $line['product']->name }}">+</button>
                                            </div>

                                            <button class="btn btn--primary btn--sm" type="submit" style="margin-inline-start: 8px">Update</button>
                                        </form>
                                    </td>

                                    <td class="col-total" data-label="Total">
                                        <span class="cell-total">${{ number_format($line['product']->price * $line['quantity'], 2) }}</span>
                                    </td>

                                    <td class="col-remove">
                                        <form method="post" action="{{ route('cart.destroy') }}">
                                            @csrf
                                            @method('delete')
                                            <input type="hidden" name="product_id" value="{{ $line['product']->id }}">
                                            <input type="hidden" name="size" value="{{ $line['size'] }}">

                                            <button class="cart-item__remove" type="submit">
                                                <img src="{{ asset('assets/images/icons/icon-delete.svg') }}" width="24" height="24" alt="">
                                                <span class="visually-hidden">Remove {{ $line['product']->name }} from the cart</span>
                                            </button>
                                        </form>
                                    </td>
                                </tr>
                            @endforeach
                        </tbody>
                    </table>
                    <p class="visually-hidden" data-cart-status role="status"></p>
                </div>

                <aside class="summary" aria-labelledby="cart-totals-title">
                    <h2 class="summary__title" id="cart-totals-title">Cart Totals</h2>
                    <hr>

                    <div class="coupon">
                        @if($coupon)
                            <form method="post" action="{{ route('cart.coupon.remove') }}">
                                @csrf
                                @method('delete')
                                <p>Coupon <strong>{{ $coupon['code'] }}</strong> applied</p>
                                <button type="submit">Remove</button>
                            </form>
                        @else
                            <form method="post" action="{{ route('cart.coupon.apply') }}" class="coupon__field">
                                @csrf
                                <label for="coupon-code">Coupon Apply</label>
                                <input id="coupon-code" type="text" name="coupon" value="{{ old('coupon') }}" placeholder="Enter coupon code here..." autocomplete="off">
                                <button type="submit">Apply</button>
                                @error('coupon')
                                    <p class="form-status" role="alert">{{ $message }}</p>
                                @enderror
                            </form>
                        @endif
                    </div>

                    <dl class="totals">
                        <div>
                            <dt>Subtotal</dt>
                            <dd>${{ number_format($subtotal, 2) }}</dd>
                        </div>
                        <div>
                            <dt>Coupon Discount</dt>
                            <dd>(-) {{ number_format($discount, 2) }}</dd>
                        </div>
                        <div>
                            <dt>Shiping</dt>
                            <dd>
                                ${{ number_format($shipping, 2) }}
                                <a class="note" href="{{ route('checkout.show') }}">View shipping charge</a>
                            </dd>
                        </div>
                        <div class="total">
                            <dt>Total</dt>
                            <dd class="value">${{ number_format($total, 2) }}</dd>
                        </div>
                    </dl>

                    <a class="btn btn--primary btn--block" href="{{ route('checkout.show') }}">Proceed To Checkout</a>
                    <a class="continue" href="{{ route('shop.index') }}">Continue Shopping</a>
                </aside>
            </div>
        @endif

        @if($related->isNotEmpty())
            <section class="related" aria-labelledby="interested-title">
                <h2 class="related__title" id="interested-title">You may be interested in</h2>
                <hr>
                <div class="related-grid">
                    @foreach($related as $item)
                        <a class="mini-card" href="{{ route('product.show', $item->slug) }}">
                            <span class="mini-card__media">
                                <img src="{{ $item->main_image ? Storage::url($item->main_image) : asset('assets/images/plant-beach-spider-lily.png') }}" width="219" height="255" alt="{{ $item->name }}" loading="lazy" decoding="async">
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
