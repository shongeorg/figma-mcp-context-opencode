@extends('layouts.app')

@section('title', $tab === 'sale' ? 'Sale — GreenShop' : ($tab === 'new' ? 'New Arrivals — GreenShop' : 'Shop plants — GreenShop'))
@section('description', 'Browse the full GreenShop catalogue: filter by category, price and size, sort and pick your favorite plants.')

@section('content')
    @include('partials.catalog')
@endsection
