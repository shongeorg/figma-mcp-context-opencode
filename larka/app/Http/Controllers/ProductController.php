<?php

namespace App\Http\Controllers;

use App\Models\Product;
use App\Models\Review;
use Illuminate\Contracts\View\View;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;

class ProductController extends Controller
{
    public function show(Request $request, Product $product): View
    {
        $product->load(['images', 'category']);

        $images = $product->images;

        if ($images->isEmpty()) {
            $images = collect();
        }

        $reviews = $product->reviews()->with('user')->latest()->get();

        $related = Product::with('images')
            ->where('category_id', $product->category_id)
            ->whereKeyNot($product->id)
            ->inStock()
            ->take(4)
            ->get();

        return view('product.show', [
            'product' => $product,
            'images' => $images,
            'reviews' => $reviews,
            'related' => $related,
        ]);
    }

    public function storeReview(Request $request, Product $product)
    {
        $validated = $request->validate([
            'rating' => ['required', 'integer', 'min:1', 'max:5'],
            'body' => ['required', 'string', 'max:2000'],
        ]);

        Review::updateOrCreate(
            ['product_id' => $product->id, 'user_id' => Auth::id()],
            $validated,
        );

        $product->update([
            'rating' => round($product->reviews()->avg('rating'), 2),
            'reviews_count' => $product->reviews()->count(),
        ]);

        return back()->with('status', 'Thank you, your review has been submitted.');
    }
}
