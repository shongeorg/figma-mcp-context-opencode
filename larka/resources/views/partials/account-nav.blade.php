<nav class="account-nav" aria-labelledby="account-nav-title">
    <h1 class="account-nav__title" id="account-nav-title">My Account</h1>
    <ul>
        <li>
            <a href="{{ route('account.show') }}" @if(request()->routeIs('account.show')) aria-current="page" @endif>
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="8" r="4"/><path d="M4.5 21v-1.2A5.8 5.8 0 0 1 10.3 14h3.4a5.8 5.8 0 0 1 5.8 5.8V21"/></svg>
                Account Details
            </a>
        </li>
        <li>
            <a href="{{ route('account.addresses') }}" @if(request()->routeIs('account.addresses')) aria-current="page" @endif>
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 22s7-6.2 7-11a7 7 0 1 0-14 0c0 4.8 7 11 7 11Z"/><circle cx="12" cy="11" r="2.6"/></svg>
                Address
            </a>
        </li>
        <li>
            <a href="{{ route('account.orders') }}" @if(request()->routeIs('account.orders')) aria-current="page" @endif>
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 4h2.1l1.9 10.5h9.8L19 7.6H6.1"/><circle cx="9.2" cy="19" r="1.5"/><circle cx="16.6" cy="19" r="1.5"/></svg>
                Orders
            </a>
        </li>
        <li>
            <a href="{{ route('shop.index') }}">
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 20.2S4.6 15.5 4.6 10.6A3.9 3.9 0 0 1 12 8.3a3.9 3.9 0 0 1 7.4 2.3c0 4.9-7.4 9.6-7.4 9.6Z"/></svg>
                Wishlist
            </a>
        </li>
    </ul>

    <p class="account-nav__logout">
        <form method="post" action="{{ route('logout') }}">
            @csrf
            <button type="submit" style="background:none;border:0;padding:0;cursor:pointer;color:inherit;font:inherit;display:inline-flex;align-items:center;gap:8px">
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10.4 5H6.6A2.2 2.2 0 0 0 4.4 7.2v9.6A2.2 2.2 0 0 0 6.6 19h3.8"/><path d="M15.4 8.4 19 12l-3.6 3.6"/><path d="M19 12H9.6"/></svg>
                Logout
            </button>
        </form>
    </p>
</nav>
