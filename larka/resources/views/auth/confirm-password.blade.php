@extends('layouts.app')

@section('title', 'Confirm Password — GreenShop')
@section('description', 'Confirm your password before continuing.')

@section('content')
    <div class="container">
        <div class="auth-split">
            <div class="dialog-card dialog-card--pad">
                <img class="auth-logo" src="{{ asset('assets/images/logo-stacked.svg') }}" width="158" height="91" alt="{{ config('app.name', 'GreenShop') }}">
                <p class="auth-title" aria-hidden="true">Confirm Password</p>

                <form class="auth-form" method="post" action="{{ route('password.confirm') }}">
                    @csrf

                    @if($errors->any())
                        <p class="form-status" role="alert">{{ $errors->first() }}</p>
                    @endif

                    <p class="auth-lead">This is a secure area of the application. Please confirm your password before continuing.</p>

                    <label class="visually-hidden" for="confirm-password">Password</label>
                    <span class="input-wrap">
                        <input class="input" id="confirm-password" type="password" name="password" autocomplete="current-password" required>
                    </span>

                    <button class="btn btn--primary btn--block" type="submit">Confirm Password</button>
                </form>
            </div>
        </div>
    </div>
@endsection
