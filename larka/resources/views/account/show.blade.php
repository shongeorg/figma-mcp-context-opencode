@extends('layouts.app')

@section('title', 'My Account — GreenShop')
@section('description', 'Manage your GreenShop profile, password and account balance.')

@section('content')
    <div class="container">
        <div class="account">
            @include('partials.account-nav')

            <div class="account-panel">
                @if(session('status'))
                    <p class="form-status" role="status">{{ session('status') }}</p>
                @endif

                <h2>Personal Information</h2>

                <form method="post" action="{{ route('account.update') }}">
                    @csrf
                    @method('put')

                    <div class="form-grid">
                        <p class="field">
                            <label class="field__label" for="acc-name">Username <span class="req">*</span></label>
                            <input class="input" id="acc-name" name="name" type="text" value="{{ old('name', $user->name) }}" autocomplete="username" required>
                        </p>

                        <p class="field">
                            <label class="field__label" for="acc-email">Email address <span class="req">*</span></label>
                            <input class="input" id="acc-email" name="email" type="email" value="{{ old('email', $user->email) }}" autocomplete="email" required>
                        </p>

                        <p class="field">
                            <label class="field__label" for="acc-phone">Phone Number</label>
                            <input class="input" id="acc-phone" name="phone" type="tel" value="{{ old('phone', $user->phone ?? '') }}" autocomplete="tel">
                        </p>

                        <p class="field">
                            <label class="field__label">Account balance</label>
                            <span class="input">${{ number_format($user->balance, 2) }}</span>
                        </p>
                    </div>

                    <button class="btn btn--primary" type="submit">Save Changes</button>
                </form>

                <h3 class="group-title">Password change</h3>

                <form method="post" action="{{ route('account.password') }}">
                    @csrf
                    @method('put')

                    <div class="form-grid">
                        <p class="field">
                            <label class="field__label" for="acc-pass">Current password</label>
                            <span class="input-wrap">
                                <input class="input" id="acc-pass" name="current_password" type="password" autocomplete="current-password" required>
                            </span>
                        </p>

                        <p class="field">
                            <label class="field__label" for="acc-pass-new">New password</label>
                            <span class="input-wrap">
                                <input class="input" id="acc-pass-new" name="password" type="password" autocomplete="new-password" minlength="8" required>
                            </span>
                        </p>

                        <p class="field">
                            <label class="field__label" for="acc-pass-confirm">Confirm new password</label>
                            <span class="input-wrap">
                                <input class="input" id="acc-pass-confirm" name="password_confirmation" type="password" autocomplete="new-password" minlength="8" required>
                            </span>
                        </p>
                    </div>

                    <button class="btn btn--primary" type="submit">Change Password</button>
                </form>
            </div>
        </div>
    </div>
@endsection
