@extends('layouts.app')

@section('title', 'Reset Password — GreenShop')
@section('description', 'Set a new password for your GreenShop account.')

@section('content')
    <div class="container">
        <div class="auth-split">
            <div class="dialog-card dialog-card--pad">
                <img class="auth-logo" src="{{ asset('assets/images/logo-stacked.svg') }}" width="158" height="91" alt="{{ config('app.name', 'GreenShop') }}">
                <p class="auth-title" aria-hidden="true">Reset Password</p>

                <form class="auth-form" method="post" action="{{ route('password.update') }}">
                    @csrf
                    <input type="hidden" name="token" value="{{ $token }}">

                    @if($errors->any())
                        <p class="form-status" role="alert">{{ $errors->first() }}</p>
                    @endif

                    <label class="visually-hidden" for="reset-email">Email address</label>
                    <input class="input" id="reset-email" type="email" name="email" value="{{ old('email', $email) }}" autocomplete="email" required>

                    <label class="visually-hidden" for="reset-password">New password</label>
                    <span class="input-wrap">
                        <input class="input" id="reset-password" type="password" name="password" autocomplete="new-password" minlength="8" required>
                    </span>

                    <label class="visually-hidden" for="reset-confirm">Confirm password</label>
                    <span class="input-wrap">
                        <input class="input" id="reset-confirm" type="password" name="password_confirmation" autocomplete="new-password" minlength="8" required>
                    </span>

                    <button class="btn btn--primary btn--block" type="submit">Reset Password</button>
                </form>
            </div>
        </div>
    </div>
@endsection
