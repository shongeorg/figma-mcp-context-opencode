@extends('layouts.app')

@section('title', 'My Orders — GreenShop')
@section('description', 'See every GreenShop order you have placed and its current status.')

@section('content')
    <div class="container">
        <div class="account">
            @include('partials.account-nav')

            <div class="account-panel">
                <h2>Orders</h2>

                @if(session('status'))
                    <p class="form-status" role="status">{{ session('status') }}</p>
                @endif

                @if(session('error'))
                    <p class="form-status form-status--error" role="alert">{{ session('error') }}</p>
                @endif

                @if($orders->isEmpty())
                    <p class="empty-state">You have not placed any orders yet. <a href="{{ route('shop.index') }}">Start shopping</a>.</p>
                @else
                    <table class="cart-table" aria-label="Your orders">
                        <thead>
                            <tr>
                                <th scope="col">Order</th>
                                <th scope="col">Date</th>
                                <th scope="col">Status</th>
                                <th scope="col">Items</th>
                                <th scope="col">Total</th>
                                <th scope="col"><span class="visually-hidden">Actions</span></th>
                            </tr>
                        </thead>
                        <tbody>
                            @foreach($orders as $order)
                                <tr>
                                    <td class="col-product"><strong>{{ $order->number }}</strong></td>
                                    <td data-label="Date">{{ $order->placed_at?->format('M j, Y') }}</td>
                                    <td data-label="Status"><span class="badge">{{ $order->status_label }}</span></td>
                                    <td data-label="Items">{{ $order->items_count }}</td>
                                    <td data-label="Total">${{ number_format($order->total, 2) }}</td>
                                    <td class="col-remove">
                                        <a class="btn btn--primary btn--sm" href="{{ route('orders.show', $order) }}">View</a>

                                        @if($order->is_cancellable)
                                            <form method="post" action="{{ route('orders.cancel', $order) }}" class="order-cancel">
                                                @csrf
                                                @method('delete')
                                                <button class="btn btn--outline btn--sm" type="submit">Cancel</button>
                                            </form>
                                        @endif
                                    </td>
                                </tr>
                            @endforeach
                        </tbody>
                    </table>

                    {{ $orders->links() }}
                @endif
            </div>
        </div>
    </div>
@endsection
