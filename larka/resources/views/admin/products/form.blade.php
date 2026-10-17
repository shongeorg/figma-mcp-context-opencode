@extends('admin.layout')

@section('title', $product->exists ? 'Edit product' : 'Add product')

@section('content')
    <h1>{{ $product->exists ? 'Edit product' : 'Add product' }}</h1>

    @if($errors->any())
        <p class="form-status" role="alert">{{ $errors->first() }}</p>
    @endif

    <form method="post" action="{{ $product->exists ? route('admin.products.update', $product) : route('admin.products.store') }}">
        @csrf
        @if($product->exists)
            @method('put')
        @endif

        <div class="admin-form-grid">
            <p class="field">
                <label class="field__label" for="f-name">Name <span class="req">*</span></label>
                <input class="input" id="f-name" name="name" type="text" value="{{ old('name', $product->name) }}" required>
            </p>

            <p class="field">
                <label class="field__label" for="f-sku">SKU <span class="req">*</span></label>
                <input class="input" id="f-sku" name="sku" type="text" value="{{ old('sku', $product->sku) }}" required>
            </p>

            <p class="field">
                <label class="field__label" for="f-category">Category <span class="req">*</span></label>
                <select class="select" id="f-category" name="category_id" required>
                    @foreach($categories as $category)
                        <option value="{{ $category->id }}" @selected(old('category_id', $product->category_id) === $category->id)>{{ $category->name }}</option>
                    @endforeach
                </select>
            </p>

            <p class="field">
                <label class="field__label" for="f-price">Price <span class="req">*</span></label>
                <input class="input" id="f-price" name="price" type="number" step="0.01" min="0" value="{{ old('price', $product->price) }}" required>
            </p>

            <p class="field">
                <label class="field__label" for="f-old-price">Old price</label>
                <input class="input" id="f-old-price" name="old_price" type="number" step="0.01" min="0" value="{{ old('old_price', $product->old_price) }}">
            </p>

            <p class="field">
                <label class="field__label" for="f-stock">Stock <span class="req">*</span></label>
                <input class="input" id="f-stock" name="stock" type="number" min="0" value="{{ old('stock', $product->stock ?? 0) }}" required>
            </p>

            <p class="field">
                <label class="field__label" for="f-sizes">Sizes (comma separated)</label>
                <input class="input" id="f-sizes" name="sizes" type="text" value="{{ old('sizes', is_array($product->sizes) ? implode(', ', $product->sizes) : '') }}" placeholder="Small, Medium, Large">
            </p>

            <p class="field">
                <label class="field__label" for="f-image-query">Image search query</label>
                <input class="input" id="f-image-query" name="image_query" type="text" value="{{ old('image_query') }}" placeholder="Barberton Daisy plant">
            </p>
        </div>

        <p class="field">
            <label class="field__label" for="f-short">Short description</label>
            <textarea class="textarea" id="f-short" name="short_description" rows="3">{{ old('short_description', $product->short_description) }}</textarea>
        </p>

        <p class="field">
            <label class="field__label" for="f-description">Full description</label>
            <textarea class="textarea" id="f-description" name="description" rows="8">{{ old('description', $product->description) }}</textarea>
        </p>

        <p class="field">
            <label><input type="checkbox" name="is_new" value="1" @checked(old('is_new', $product->is_new))> Mark as new arrival</label>
        </p>

        @if($product->exists && $product->images->isNotEmpty())
            <div class="admin-images">
                @foreach($product->images as $image)
                    <img src="{{ Storage::url($image->path) }}" alt="{{ $product->name }} image {{ $image->position + 1 }}">
                @endforeach
            </div>
        @endif

        <p style="margin-block-start: 16px">
            <button class="btn btn--primary" type="submit">{{ $product->exists ? 'Save changes' : 'Create product' }}</button>
        </p>
    </form>
@endsection
