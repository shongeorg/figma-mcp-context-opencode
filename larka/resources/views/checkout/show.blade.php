@extends('layouts.app')

@section('title', 'Checkout — GreenShop')
@section('description', 'Enter your shipping details, choose a payment method and place your GreenShop order.')

@section('content')
    <div class="container">
        <h1 class="visually-hidden">Checkout</h1>

        <nav class="breadcrumb" aria-label="Breadcrumb">
            <a href="{{ route('home') }}">Home</a> <span aria-hidden="true">/</span>
            <a href="{{ route('cart.index') }}">Cart</a> <span aria-hidden="true">/</span>
            <span aria-current="page">Checkout</span>
        </nav>

        @if($errors->any())
            <p class="form-status" role="alert">{{ $errors->first() }}</p>
        @endif

        <form method="post" action="{{ route('checkout.store') }}" class="checkout">
            @csrf

            <div class="form-grid">
                <div>
                    <p class="field">
                        <label for="first_name">First name</label>
                        <input class="input" id="first_name" type="text" name="first_name" value="{{ old('first_name', $user?->name) }}" autocomplete="given-name" required>
                    </p>

                    <p class="field">
                        <label for="last_name">Last name</label>
                        <input class="input" id="last_name" type="text" name="last_name" value="{{ old('last_name') }}" autocomplete="family-name" required>
                    </p>

                    <p class="field">
                        <label for="street">Street address</label>
                        <input class="input" id="street" type="text" name="street" value="{{ old('street') }}" autocomplete="street-address" required>
                    </p>

                    <p class="field">
                        <label for="city">Town / City</label>
                        <input class="input" id="city" type="text" name="city" value="{{ old('city') }}" autocomplete="address-level2" required>
                    </p>

                    <p class="field">
                        <label for="region">Region / State</label>
                        <input class="input" id="region" type="text" name="region" value="{{ old('region') }}" autocomplete="address-level1">
                    </p>

                    <p class="field">
                        <label for="postal_code">Postcode / ZIP</label>
                        <input class="input" id="postal_code" type="text" name="postal_code" value="{{ old('postal_code') }}" autocomplete="postal-code">
                    </p>

                    <p class="field">
                        <label for="phone">Phone</label>
                        <input class="input" id="phone" type="tel" name="phone" value="{{ old('phone') }}" autocomplete="tel" required>
                    </p>

                    <p class="field">
                        <label for="email">Email address</label>
                        <input class="input" id="email" type="email" name="email" value="{{ old('email', $user?->email) }}" autocomplete="email" required>
                    </p>

                    <p class="field">
                        <label for="note">Order notes (optional)</label>
                        <textarea class="textarea" id="note" name="note" rows="3">{{ old('note') }}</textarea>
                    </p>
                </div>

                <aside class="order-panel" aria-labelledby="order-title">
                    <div class="order-panel__head">
                        <h2 id="order-title">Your Order</h2>
                    </div>

                    <ul class="order-list">
                        @foreach($lines as $line)
                            <li>
                                <span class="order-list__media">
                                    <img src="{{ $line['product']->main_image ? Storage::url($line['product']->main_image) : asset('assets/images/plant-barberton-daisy.png') }}" width="58" height="58" alt="{{ $line['product']->name }}" loading="lazy">
                                </span>
                                <span class="order-list__body">
                                    <span class="order-list__name">{{ $line['product']->name }}</span>
                                    <span class="order-list__sku">SKU: {{ $line['product']->sku }}</span>
                                    <span class="order-list__qty">(x {{ $line['quantity'] }}){{ $line['size'] !== '' ? ' · '.$line['size'] : '' }}</span>
                                </span>
                                <span class="order-list__sum">${{ number_format($line['product']->price * $line['quantity'], 2) }}</span>
                            </li>
                        @endforeach
                    </ul>

                    <div class="order-indent">
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
                                <dd>${{ number_format($shipping, 2) }}</dd>
                            </div>
                            <div class="total">
                                <dt>Total</dt>
                                <dd class="value">${{ number_format($total, 2) }}</dd>
                            </div>
                        </dl>
                    </div>

                    <fieldset class="payments">
                        <legend class="visually-hidden">Payment method</legend>

                        <label class="payment">
                            <input type="radio" name="payment_method" value="cod" @checked(old('payment_method', 'cod') === 'cod')>
                            <span>Cash on delivery</span>
                        </label>

                        <label class="payment">
                            <input type="radio" name="payment_method" value="card" @checked(old('payment_method') === 'card')>
                            <span>Credit card</span>
                        </label>

                        <label class="payment">
                            <input type="radio" name="payment_method" value="bank" @checked(old('payment_method') === 'bank')>
                            <span>Direct bank transfer</span>
                        </label>
                    </fieldset>

                    <button class="btn btn--primary btn--block" type="submit">Place Order</button>
                </aside>
            </div>
        </form>
    </div>
@endsection
