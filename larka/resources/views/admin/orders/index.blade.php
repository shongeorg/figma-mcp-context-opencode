@extends('admin.layout')

@section('title', 'Orders')

@section('content')
    <div class="admin-toolbar">
        <h1>Orders</h1>

        <form method="get" action="{{ route('admin.orders.index') }}" style="display: contents">
            <select class="select" name="status" onchange="this.form.submit()">
                <option value="">All statuses</option>
                @foreach($statuses as $status)
                    <option value="{{ $status }}" @selected($current === $status)>{{ ucfirst($status) }}</option>
                @endforeach
            </select>
        </form>
    </div>

    @if($orders->isEmpty())
        <p class="empty-state">No orders found.</p>
    @else
        <table class="admin-table">
            <thead>
                <tr>
                    <th>Order</th>
                    <th>Customer</th>
                    <th>Date</th>
                    <th>Items</th>
                    <th>Total</th>
                    <th>Status</th>
                    <th><span class="visually-hidden">Actions</span></th>
                </tr>
            </thead>
            <tbody>
                @foreach($orders as $order)
                    <tr>
                        <td>
                            <strong>{{ $order->number }}</strong><br>
                            <small>{{ $order->payment_method }}</small>
                        </td>
                        <td>
                            {{ $order->user?->name }}<br>
                            <small>{{ $order->shipping_address['city'] ?? '' }}, {{ $order->shipping_address['street'] ?? '' }}</small>
                        </td>
                        <td>{{ $order->placed_at?->format('M j, Y') }}</td>
                        <td>{{ $order->items->sum('quantity') }}</td>
                        <td>${{ number_format($order->total, 2) }}</td>
                        <td>
                            <form method="post" action="{{ route('admin.orders.status', $order) }}">
                                @csrf
                                @method('put')
                                <select class="select" name="status" onchange="this.form.submit()">
                                    @foreach($statuses as $status)
                                        <option value="{{ $status }}" @selected($order->status === $status)>{{ ucfirst($status) }}</option>
                                    @endforeach
                                </select>
                            </form>
                        </td>
                        <td>
                            @if($order->is_paid)
                                <small>Already shipped</small>
                            @else
                                <form method="post" action="{{ route('admin.orders.destroy', $order) }}" onsubmit="return confirm('Delete order {{ $order->number }}?')">
                                    @csrf
                                    @method('delete')
                                    <button class="btn btn--outline btn--sm" type="submit">Delete</button>
                                </form>
                            @endif
                        </td>
                    </tr>
                @endforeach
            </tbody>
        </table>

        {{ $orders->links() }}
    @endif
@endsection
