@extends('layouts.app')

@section('title', 'Register — GreenShop')
@section('description', 'Create a GreenShop account to save your addresses, track orders and check out faster.')

@section('content')
    <div class="container">
        <div class="auth-split">
            <div class="dialog-card dialog-card--pad">
                <img class="auth-logo" src="{{ asset('assets/images/logo-stacked.svg') }}" width="158" height="91" alt="{{ config('app.name', 'GreenShop') }}">
                <p class="auth-title" aria-hidden="true">Sign Up</p>

                <nav class="auth-tabs" aria-label="Account">
                    <a href="{{ route('login') }}">Login</a>
                    <span class="sep" aria-hidden="true">|</span>
                    <a href="{{ route('register') }}" aria-current="page">Register</a>
                </nav>

                <form class="auth-form" method="post" action="{{ route('register') }}">
                    @csrf
                    <p class="auth-lead">Enter your email and password to register.</p>

                    @if($errors->any())
                        <p class="form-status" role="alert">{{ $errors->first() }}</p>
                    @endif

                    <label class="visually-hidden" for="register-name">Username</label>
                    <input class="input" id="register-name" type="text" name="name" value="{{ old('name') }}" placeholder="Username" autocomplete="username" required>

                    <label class="visually-hidden" for="register-email">Email address</label>
                    <input class="input" id="register-email" type="email" name="email" value="{{ old('email') }}" placeholder="Enter your email address" autocomplete="email" required>

                    <label class="visually-hidden" for="register-password">Password</label>
                    <span class="input-wrap">
                        <input class="input" id="register-password" type="password" name="password" placeholder="Password" autocomplete="new-password" minlength="8" required>
                        <button class="input-wrap__toggle" type="button" data-toggle-password="register-password" aria-pressed="false" aria-label="Show password">
                            <img src="{{ asset('assets/images/icons/icon-eye-off.svg') }}" width="20" height="20" alt="">
                        </button>
                    </span>

                    <label class="visually-hidden" for="register-confirm">Confirm password</label>
                    <span class="input-wrap">
                        <input class="input" id="register-confirm" type="password" name="password_confirmation" placeholder="Confirm Password" autocomplete="new-password" minlength="8" required>
                    </span>

                    <button class="btn btn--primary btn--block" type="submit">
                        <span class="lbl--wide">Register</span>
                        <span class="lbl--narrow">Create an account</span>
                    </button>
                </form>

                <p class="auth-foot">Already have an account? <a href="{{ route('login') }}">Login</a></p>
            </div>
        </div>
    </div>
@endsection
