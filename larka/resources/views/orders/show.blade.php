@extends('layouts.app')

@section('title', 'Order '.$order->number.' confirmed — GreenShop')
@section('description', 'Thank you! Your GreenShop order '.$order->number.' has been received and is being prepared.')

@section('content')
    <div class="container">
        <div class="m-topbar">
            <a class="m-topbar__btn" href="{{ route('shop.index') }}" aria-label="Back to shop">
                <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">
                    <path d="m14.5 5-6 7 6 7" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </a>
            <p class="m-topbar__title" aria-hidden="true">Checkout</p>
            <span class="m-topbar__spacer" aria-hidden="true"></span>
        </div>

        <div class="thanks">
            <div class="thanks__banner">
                <span class="thanks__icon" aria-hidden="true">
                    <img src="{{ asset('assets/images/icons/icon-check.svg') }}" width="46" height="46" alt="">
                </span>
                <h1 class="block-title">Thank you!</h1>
                <p class="thanks__lead" id="thanks-dialog-title">
                    Your order has been placed successfully. We sent a confirmation to {{ $order->shipping_address['email'] ?? $order->user->email }}.
                </p>

                <dl class="thanks__meta">
                    <div>
                        <dt>Order number</dt>
                        <dd>{{ $order->number }}</dd>
                    </div>
                    <div>
                        <dt>Date</dt>
                        <dd>{{ $order->placed_at?->format('F j, Y') ?? $order->created_at->format('F j, Y') }}</dd>
                    </div>
                    <div>
                        <dt>Total</dt>
                        <dd>${{ number_format($order->total, 2) }}</dd>
                    </div>
                    <div>
                        <dt>Payment method</dt>
                        <dd>{{ strtoupper($order->payment_method) }}</dd>
                    </div>
                </dl>
            </div>

            <div>
                <h2 class="block-title">Order Details</h2>

                <div class="thanks__head">
                    <h3>Billing Address</h3>
                </div>

                <p>
                    {{ $order->shipping_address['first_name'] ?? '' }} {{ $order->shipping_address['last_name'] ?? '' }}<br>
                    {{ $order->shipping_address['street'] ?? '' }}<br>
                    {{ $order->shipping_address['city'] ?? '' }} {{ $order->shipping_address['postal_code'] ?? '' }}<br>
                    {{ $order->shipping_address['phone'] ?? '' }}<br>
                    {{ $order->shipping_address['email'] ?? '' }}
                </p>

                <ul class="thanks__list">
                    @foreach($order->items as $item)
                        <li class="thanks__row">
                            <span class="thanks__product">
                                <img src="{{ $item->image_path ? Storage::url($item->image_path) : asset('assets/images/plant-barberton-daisy.png') }}" width="56" height="56" alt="{{ $item->product_name }}" loading="lazy">
                                <span>
                                    <strong>{{ $item->product_name }}</strong>
                                    <small>SKU: {{ $item->product_sku }}{{ $item->size ? ' · '.$item->size : '' }}</small>
                                </span>
                            </span>
                            <span>{{ $item->quantity }} × ${{ number_format($item->unit_price, 2) }}</span>
                            <span>${{ number_format($item->line_total, 2) }}</span>
                        </li>
                    @endforeach
                </ul>

                <dl class="totals">
                    <div>
                        <dt>Subtotal</dt>
                        <dd>${{ number_format($order->subtotal, 2) }}</dd>
                    </div>
                    <div>
                        <dt>Discount</dt>
                        <dd>(-) {{ number_format($order->discount, 2) }}</dd>
                    </div>
                    <div>
                        <dt>Shiping</dt>
                        <dd>${{ number_format($order->shipping, 2) }}</dd>
                    </div>
                    <div class="total">
                        <dt>Total</dt>
                        <dd class="value">${{ number_format($order->total, 2) }}</dd>
                    </div>
                </dl>

                @if(session('status'))
                    <p class="form-status" role="status">{{ session('status') }}</p>
                @endif

                @if(session('error'))
                    <p class="form-status form-status--error" role="alert">{{ session('error') }}</p>
                @endif

                <p class="thanks__actions">
                    <a class="btn btn--primary" href="{{ route('shop.index') }}">Continue Shopping</a>
                    @if($order->is_cancellable)
                        <form method="post" action="{{ route('orders.cancel', $order) }}" class="order-cancel">
                            @csrf
                            @method('delete')
                            <button class="btn btn--outline" type="submit">Cancel this order</button>
                        </form>
                    @endif
                    @auth
                        <a class="continue" href="{{ route('account.show') }}">View my account</a>
                    @endauth
                </p>
            </div>
        </div>
    </div>
@endsection
