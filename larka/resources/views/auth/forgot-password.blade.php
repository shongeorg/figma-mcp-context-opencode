@extends('layouts.app')

@section('title', 'Forgot Password — GreenShop')
@section('description', 'Request a link to reset your GreenShop account password.')

@section('content')
    <div class="container">
        <div class="auth-split">
            <div class="dialog-card dialog-card--pad">
                <img class="auth-logo" src="{{ asset('assets/images/logo-stacked.svg') }}" width="158" height="91" alt="{{ config('app.name', 'GreenShop') }}">
                <p class="auth-title" aria-hidden="true">Forgot Password?</p>

                <form class="auth-form" method="post" action="{{ route('password.email') }}">
                    @csrf
                    <p class="auth-lead">Enter your email to reset your password.</p>

                    @if(session('status'))
                        <p class="form-status" role="status">{{ session('status') }}</p>
                    @endif

                    @if($errors->any())
                        <p class="form-status" role="alert">{{ $errors->first() }}</p>
                    @endif

                    <label class="visually-hidden" for="forgot-email">Email address</label>
                    <input class="input" id="forgot-email" type="email" name="email" value="{{ old('email') }}" placeholder="Email address" autocomplete="email" required>

                    <button class="btn btn--primary btn--block" type="submit">Send Reset Link</button>
                </form>

                <p class="auth-links"><a href="{{ route('login') }}">Back to Login</a></p>
            </div>
        </div>
    </div>
@endsection
