@extends('layouts.app')

@section('title', 'My Addresses — GreenShop')
@section('description', 'Manage the delivery addresses saved in your GreenShop account.')

@section('content')
    <div class="container">
        <div class="account">
            @include('partials.account-nav')

            <div class="account-panel">
                @if(session('status'))
                    <p class="form-status" role="status">{{ session('status') }}</p>
                @endif

                <h2>Addresses</h2>

                @forelse($addresses as $address)
                    <div class="address-card">
                        <p><strong>{{ $address->label }}</strong>@if($address->is_default) <span class="badge">Default</span> @endif</p>
                        <p>{{ $address->full_name }}</p>
                        <p>{{ $address->full_line }}</p>
                        <p>{{ $address->phone }}</p>

                        <div class="address-card__actions">
                            <form method="post" action="{{ route('account.addresses.destroy', $address) }}">
                                @csrf
                                @method('delete')
                                <button type="submit">Remove</button>
                            </form>
                        </div>
                    </div>
                @empty
                    <p class="empty-state">You have no saved addresses yet.</p>
                @endforelse

                <h3 class="group-title">Add a new address</h3>

                <form method="post" action="{{ route('account.addresses.store') }}">
                    @csrf

                    <div class="form-grid">
                        <p class="field">
                            <label class="field__label" for="addr-label">Label <span class="req">*</span></label>
                            <input class="input" id="addr-label" name="label" type="text" value="{{ old('label', 'Home') }}" required>
                        </p>

                        <p class="field">
                            <label class="field__label" for="addr-name">Full name <span class="req">*</span></label>
                            <input class="input" id="addr-name" name="full_name" type="text" value="{{ old('full_name', $user->name ?? '') }}" required>
                        </p>

                        <p class="field">
                            <label class="field__label" for="addr-phone">Phone</label>
                            <input class="input" id="addr-phone" name="phone" type="tel" value="{{ old('phone') }}">
                        </p>

                        <p class="field">
                            <label class="field__label" for="addr-street">Street <span class="req">*</span></label>
                            <input class="input" id="addr-street" name="street" type="text" value="{{ old('street') }}" required>
                        </p>

                        <p class="field">
                            <label class="field__label" for="addr-city">City <span class="req">*</span></label>
                            <input class="input" id="addr-city" name="city" type="text" value="{{ old('city') }}" required>
                        </p>

                        <p class="field">
                            <label class="field__label" for="addr-region">Region</label>
                            <input class="input" id="addr-region" name="region" type="text" value="{{ old('region') }}">
                        </p>

                        <p class="field">
                            <label class="field__label" for="addr-postal">Postcode / ZIP</label>
                            <input class="input" id="addr-postal" name="postal_code" type="text" value="{{ old('postal_code') }}">
                        </p>

                        <p class="field">
                            <label class="field__label" for="addr-country">Country</label>
                            <input class="input" id="addr-country" name="country" type="text" value="{{ old('country', 'Ukraine') }}">
                        </p>
                    </div>

                    <p class="field">
                        <label><input type="checkbox" name="is_default" value="1" @checked(old('is_default'))> Set as default address</label>
                    </p>

                    @if($errors->any())
                        <p class="form-status" role="alert">{{ $errors->first() }}</p>
                    @endif

                    <button class="btn btn--primary" type="submit">Save Address</button>
                </form>
            </div>
        </div>
    </div>
@endsection
