@extends('admin.layout')

@section('title', 'Products')

@section('content')
    <div class="admin-toolbar">
        <h1>Products</h1>

        <form method="get" action="{{ route('admin.products.index') }}" style="display: contents">
            <input class="input" type="search" name="q" value="{{ $search }}" placeholder="Search name or SKU">
            <button class="btn btn--primary" type="submit">Search</button>
        </form>

        <a class="btn btn--primary" href="{{ route('admin.products.create') }}">Add product</a>
    </div>

    <table class="admin-table">
        <thead>
            <tr>
                <th><span class="visually-hidden">Image</span></th>
                <th>Name</th>
                <th>SKU</th>
                <th>Category</th>
                <th>Price</th>
                <th>Stock</th>
                <th><span class="visually-hidden">Actions</span></th>
            </tr>
        </thead>
        <tbody>
            @forelse($products as $product)
                <tr>
                    <td>
                        @if($product->main_image)
                            <img class="admin-thumb" src="{{ Storage::url($product->main_image) }}" alt="{{ $product->name }}">
                        @endif
                    </td>
                    <td><a href="{{ route('admin.products.edit', $product) }}">{{ $product->name }}</a></td>
                    <td>{{ $product->sku }}</td>
                    <td>{{ $product->category?->name }}</td>
                    <td>${{ number_format($product->price, 2) }}</td>
                    <td>{{ $product->stock }}</td>
                    <td>
                        <form method="post" action="{{ route('admin.products.destroy', $product) }}" onsubmit="return confirm('Delete this product?')">
                            @csrf
                            @method('delete')
                            <button type="submit" class="btn btn--sm">Delete</button>
                        </form>
                    </td>
                </tr>
            @empty
                <tr>
                    <td colspan="7">No products found.</td>
                </tr>
            @endforelse
        </tbody>
    </table>

    {{ $products->links() }}
@endsection
