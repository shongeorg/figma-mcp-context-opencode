@extends('layouts.app')

@section('title', 'Two Factor Authentication — GreenShop')
@section('description', 'Confirm your identity with a two factor code.')

@section('content')
    <div class="container">
        <div class="auth-split">
            <div class="dialog-card dialog-card--pad">
                <img class="auth-logo" src="{{ asset('assets/images/logo-stacked.svg') }}" width="158" height="91" alt="{{ config('app.name', 'GreenShop') }}">
                <p class="auth-title" aria-hidden="true">Two Factor</p>

                <form class="auth-form" method="post" action="{{ route('two-factor.login') }}">
                    @csrf

                    @if($errors->any())
                        <p class="form-status" role="alert">{{ $errors->first() }}</p>
                    @endif

                    <label class="visually-hidden" for="two-factor-code">Authentication code</label>
                    <input class="input" id="two-factor-code" type="text" name="code" inputmode="numeric" autocomplete="one-time-code" placeholder="Authentication code" required>

                    <button class="btn btn--primary btn--block" type="submit">Log in</button>
                </form>

                <form class="auth-form" method="post" action="{{ route('two-factor.login') }}">
                    @csrf
                    <label class="visually-hidden" for="two-factor-recovery">Recovery code</label>
                    <input class="input" id="two-factor-recovery" type="text" name="recovery_code" placeholder="Recovery code" required>
                    <button class="btn btn--primary btn--block" type="submit">Use a recovery code</button>
                </form>
            </div>
        </div>
    </div>
@endsection
