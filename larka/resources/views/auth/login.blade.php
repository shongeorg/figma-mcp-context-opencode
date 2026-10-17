@extends('layouts.app')

@section('title', 'Login — GreenShop')
@section('description', 'Log in to your GreenShop account to track orders, save addresses and check out faster.')

@section('content')
    <div class="container">
        <div class="auth-split">
            <div class="dialog-card dialog-card--pad">
                <img class="auth-logo" src="{{ asset('assets/images/logo-stacked.svg') }}" width="158" height="91" alt="{{ config('app.name', 'GreenShop') }}">
                <p class="auth-title" aria-hidden="true">Login</p>

                <nav class="auth-tabs" aria-label="Account">
                    <a href="{{ route('login') }}" aria-current="page">Login</a>
                    <span class="sep" aria-hidden="true">|</span>
                    <a href="{{ route('register') }}">Register</a>
                </nav>

                <form class="auth-form" method="post" action="{{ route('login') }}">
                    @csrf
                    <p class="auth-lead">Enter your username and password to login.</p>

                    @if(session('status'))
                        <p class="form-status" role="status">{{ session('status') }}</p>
                    @endif

                    @if($errors->any())
                        <p class="form-status" role="alert">{{ $errors->first() }}</p>
                    @endif

                    <label class="visually-hidden" for="login-email">Email address</label>
                    <input class="input" id="login-email" type="email" name="email" value="{{ old('email') }}" placeholder="almamun_uxui@outlook.com" autocomplete="email" required>

                    <label class="visually-hidden" for="login-password">Password</label>
                    <span class="input-wrap">
                        <input class="input" id="login-password" type="password" name="password" autocomplete="current-password" required>
                        <button class="input-wrap__toggle" type="button" data-toggle-password="login-password" aria-pressed="false" aria-label="Show password">
                            <img src="{{ asset('assets/images/icons/icon-eye-off.svg') }}" width="20" height="20" alt="">
                        </button>
                    </span>

                    <p class="auth-links"><a href="{{ route('password.request') }}">Forgot Password?</a></p>

                    <label class="auth-remember"><input type="checkbox" name="remember" value="1"> Remember me</label>

                    <button class="btn btn--primary btn--block" type="submit">Login</button>
                </form>

                <p class="auth-foot">Don't have an account? <a href="{{ route('register') }}">Sign Up</a></p>
            </div>
        </div>
    </div>
@endsection
