<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\Category;
use App\Models\Product;
use App\Services\ImageSearch\ProductImageFetcher;
use Illuminate\Contracts\View\View;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Str;

class AdminProductController extends Controller
{
    public function index(Request $request): View
    {
        $query = Product::with(['category', 'images'])->latest();

        if ($request->filled('q')) {
            $search = $request->string('q')->toString();
            $query->where(function ($builder) use ($search) {
                $builder->where('name', 'ilike', "%{$search}%")
                    ->orWhere('sku', 'ilike', "%{$search}%");
            });
        }

        return view('admin.products.index', [
            'products' => $query->paginate(20)->withQueryString(),
            'search' => $request->input('q'),
        ]);
    }

    public function create(): View
    {
        return view('admin.products.form', [
            'product' => new Product,
            'categories' => Category::orderBy('position')->get(),
        ]);
    }

    public function store(Request $request, ProductImageFetcher $fetcher): RedirectResponse
    {
        $validated = $this->validated($request);

        $product = Product::create($validated);

        if ($request->filled('image_query')) {
            $fetcher->attachToProduct($product, $request->string('image_query')->toString(), 3);
        }

        return redirect()->route('admin.products.edit', $product)->with('status', 'Product created.');
    }

    public function edit(Product $product): View
    {
        $product->load('images');

        return view('admin.products.form', [
            'product' => $product,
            'categories' => Category::orderBy('position')->get(),
        ]);
    }

    public function update(Request $request, Product $product, ProductImageFetcher $fetcher): RedirectResponse
    {
        $product->update($this->validated($request));

        if ($request->filled('image_query')) {
            $fetcher->attachToProduct($product, $request->string('image_query')->toString(), 3);
        }

        return redirect()->route('admin.products.edit', $product)->with('status', 'Product updated.');
    }

    public function destroy(Product $product): RedirectResponse
    {
        $product->delete();

        return redirect()->route('admin.products.index')->with('status', 'Product deleted.');
    }

    /**
     * @return array<string, mixed>
     */
    private function validated(Request $request): array
    {
        return $request->validate([
            'category_id' => ['required', 'exists:categories,id'],
            'name' => ['required', 'string', 'max:150'],
            'sku' => ['required', 'string', 'max:64', 'unique:products,sku'],
            'short_description' => ['nullable', 'string', 'max:1000'],
            'description' => ['nullable', 'string'],
            'price' => ['required', 'numeric', 'min:0'],
            'old_price' => ['nullable', 'numeric', 'min:0'],
            'stock' => ['required', 'integer', 'min:0'],
            'rating' => ['nullable', 'numeric', 'min:0', 'max:5'],
            'is_new' => ['nullable', 'boolean'],
            'sizes' => ['nullable', 'string', 'max:100'],
        ]) + [
            'slug' => Str::slug($request->input('name')).'-'.uniqid(),
            'is_new' => $request->boolean('is_new'),
            'sizes' => array_values(array_filter(array_map('trim', explode(',', (string) $request->input('sizes'))))),
        ];
    }
}
