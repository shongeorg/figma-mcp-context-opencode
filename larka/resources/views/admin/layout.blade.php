<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="robots" content="noindex, nofollow">

    <title>@yield('title', 'Admin') — {{ config('app.name', 'GreenShop') }}</title>

    <link rel="icon" href="{{ asset('assets/images/logo.svg') }}" type="image/svg+xml">
    <link rel="stylesheet" href="{{ asset('assets/css/style.css') }}">
    <link rel="stylesheet" href="{{ asset('assets/css/admin.css') }}">
</head>
<body class="admin-body">
<header class="admin-header">
    <a class="logo" href="{{ route('admin.dashboard') }}">
        <img src="{{ asset('assets/images/logo.svg') }}" width="120" height="28" alt="{{ config('app.name', 'GreenShop') }} admin">
    </a>

    <nav aria-label="Admin">
        <a href="{{ route('admin.dashboard') }}" @if(request()->routeIs('admin.dashboard')) aria-current="page" @endif>Dashboard</a>
        <a href="{{ route('admin.products.index') }}" @if(request()->routeIs('admin.products.*')) aria-current="page" @endif>Products</a>
        <a href="{{ route('admin.orders.index') }}" @if(request()->routeIs('admin.orders.*')) aria-current="page" @endif>Orders</a>
        <a href="{{ route('home') }}">View shop</a>
    </nav>

    <form method="post" action="{{ route('logout') }}">
        @csrf
        <button type="submit" class="btn btn--primary btn--sm">Log out ({{ auth()->user()->name }})</button>
    </form>
</header>

<main class="admin-main container">
    @if(session('status'))
        <p class="form-status" role="status">{{ session('status') }}</p>
    @endif

    @if(session('error'))
        <p class="form-status form-status--error" role="alert">{{ session('error') }}</p>
    @endif

    @yield('content')
</main>
</body>
</html>
