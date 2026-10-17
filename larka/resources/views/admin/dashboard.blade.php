@extends('admin.layout')

@section('title', 'Dashboard')

@section('content')
    <h1>Dashboard</h1>

    <div class="admin-stats">
        <div class="admin-stat">
            <p class="admin-stat__label">Products</p>
            <p class="admin-stat__value">{{ $productCount }}</p>
        </div>

        <div class="admin-stat">
            <p class="admin-stat__label">Orders</p>
            <p class="admin-stat__value">{{ $orderCount }}</p>
        </div>

        <div class="admin-stat">
            <p class="admin-stat__label">Customers</p>
            <p class="admin-stat__value">{{ $userCount }}</p>
        </div>

        <div class="admin-stat">
            <p class="admin-stat__label">Revenue</p>
            <p class="admin-stat__value">${{ number_format($revenue, 2) }}</p>
        </div>
    </div>

    <h2>Recent orders</h2>

    @if($recentOrders->isEmpty())
        <p class="empty-state">No orders yet.</p>
    @else
        <table class="admin-table">
            <thead>
                <tr>
                    <th>Order</th>
                    <th>Customer</th>
                    <th>Date</th>
                    <th>Status</th>
                    <th>Total</th>
                </tr>
            </thead>
            <tbody>
                @foreach($recentOrders as $order)
                    <tr>
                        <td>{{ $order->number }}</td>
                        <td>{{ $order->user?->name }}</td>
                        <td>{{ $order->placed_at?->format('M j, Y H:i') }}</td>
                        <td>{{ $order->status_label }}</td>
                        <td>${{ number_format($order->total, 2) }}</td>
                    </tr>
                @endforeach
            </tbody>
        </table>
    @endif
@endsection
